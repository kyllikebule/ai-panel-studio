"""发言调度编排 —— 讨论流程 AI 引擎。"""
import asyncio
from typing import Any, AsyncGenerator, Callable

from .prompt_lib import GuestDef
from .transcript_context import build_transcript_context


async def decide_next_speaker_llm(
    transcript: list[dict],
    guests: list[GuestDef],
    topic: str,
    spoken_this_round: set[int] | None,
    llm: Any,
) -> dict | None:
    """由 LLM 根据讨论上下文 + 嘉宾立场自主决定下一位发言人。

    规则（硬约束由代码兜底）：
    - 禁止连续同一位嘉宾发言
    - 空 transcript 返回 None（由 host 开场）

    Returns:
        {"guest_id": int, "reason": "举手|补充|反驳"} | None
    """
    if not transcript:
        return None

    spoken = spoken_this_round or set()
    last_speaker = transcript[-1].get("sender_name", "")

    # 硬约束：排除上一发言人
    allowed = [i for i, g in enumerate(guests) if g.name != last_speaker]
    if not allowed:
        return None

    # 构建嘉宾列表（含是否已发言标注）
    guest_list = "\n".join(
        f"[{i}] {g.name} | {g.persona} | 风格:{g.speak_style}"
        f"{' (本轮已发言)' if i in spoken else ''}"
        for i, g in enumerate(guests)
    )

    recent = transcript[-8:]
    transcript_text = "\n".join(
        f"[{m.get('role','')}] {m.get('sender_name','')}: {m.get('content','')}"
        for m in recent
    )

    prompt = (
        f"讨论主题：{topic}\n\n"
        f"嘉宾阵容：\n{guest_list}\n\n"
        f"最近发言记录：\n{transcript_text}\n\n"
        f"上一发言人是「{last_speaker}」，本轮不可再选。\n"
        f"请从允许的嘉宾中选出**最应该接话的一位**，判断标准：\n"
        f"1. 谁的观点与上一位最可能产生碰撞？→ reason=反驳\n"
        f"2. 谁能为上一位的观点提供补充/延伸？→ reason=补充\n"
        f"3. 如果上一发言没有明确攻击对象，优先选立场最对立的嘉宾 → reason=举手\n"
        f"4. 优先让本轮还没发言的嘉宾参与\n\n"
        f'仅返回 JSON：{{"guest_index": <int>, "reason": "<举手|补充|反驳>"}}'
    )

    try:
        result = await llm.chat_json(prompt)
        idx = int(result.get("guest_index", -1))
        reason = str(result.get("reason", "举手"))

        if idx not in allowed:
            # LLM 选了非法嘉宾 → 从 allowed 中选立场最对立的
            idx = allowed[0]

        if reason not in ("举手", "补充", "反驳"):
            reason = "举手"

        return {"guest_id": idx, "reason": reason}

    except Exception:
        # LLM 失败 → 兜底：从 allowed 中选立场差异最大的
        if not allowed:
            return None
        return {"guest_id": allowed[0], "reason": "举手"}


async def generate_speech(
    guest: GuestDef,
    transcript: list[dict],
    speak_reason: str,
    topic: str,
    llm: Any,
) -> str:
    """生成嘉宾发言内容，1-2 句话。"""
    context = build_transcript_context(transcript, max_recent=10)

    try:
        result = await llm.chat([
            {"role": "system", "content": (
                f"你是{guest.name}，{guest.persona}。"
                f"发言风格：{guest.speak_style}。"
                f"请以第一人称发言，仅输出发言内容。1-2句话。"
                f"不要输出'我认为'开头，直接表达观点。"
                f"不要输出角色名、冒号或引号前缀。"
                f"不要描述你在思考什么，直接输出观点。"
            )},
            {"role": "user", "content": (
                f"讨论主题：{topic}\n"
                f"你发言的原因是：{speak_reason}\n"
                f"最近发言：\n{context}\n\n"
                f"请以{guest.name}的身份发言："
            )},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except Exception:
        return f"我（{guest.name}）认为在这个问题上需要更多讨论。"


async def run_discussion_flow(
    discussion_id: int,
    topic: str,
    host: dict,
    guests: list[GuestDef],
    max_rounds: int,
    llm: Any,
    broadcast: Callable,
    stop_flag: asyncio.Event,
) -> AsyncGenerator[dict, None]:
    """完整讨论编排的异步生成器。

    Yields:
        事件 dict: {"event": "host_open"|"guest_speak"|"round_change"|"opinion_extracted"|"discussion_end", ...}
    """
    from .opinion_extractor import extract_opinions, OpinionResult

    all_messages: list[dict] = []
    all_opinions: list[OpinionResult] = []
    msg_id = 0

    if stop_flag.is_set():
        yield {"event": "discussion_end", "reason": "stopped"}
        return

    # 主持人开场
    try:
        host_result = await llm.chat([
            {"role": "system", "content": host.get("system_prompt", "你是讨论主持人。")},
            {"role": "user", "content": (
                f"讨论主题：{topic}\n"
                f"嘉宾：{', '.join(g.name for g in guests)}\n"
                f"请进行开场白，欢迎嘉宾并介绍话题，然后请第一位嘉宾发言。控制在150字以内。"
            )},
        ])
        host_content = host_result["choices"][0]["message"]["content"].strip()
    except Exception:
        host_content = f"欢迎各位嘉宾，今天讨论的主题是{topic}。"

    msg_id += 1
    all_messages.append({"id": msg_id, "role": "host", "sender_name": host["name"], "content": host_content})

    yield {"event": "host_open", "host_name": host["name"], "content": host_content, "seq_num": msg_id}
    await broadcast(discussion_id, {"event": "host_open", "host_name": host["name"], "content": host_content, "seq_num": msg_id})

    for round_num in range(1, max_rounds + 1):
        if stop_flag.is_set():
            yield {"event": "discussion_end", "reason": "stopped"}
            return

        yield {"event": "round_change", "round": round_num}
        await broadcast(discussion_id, {"event": "round_change", "round": round_num})
        spoken_this_round: set[int] = set()

        for _ in range(len(guests)):
            if stop_flag.is_set():
                break

            decision = await decide_next_speaker_llm(
                all_messages, guests, topic, spoken_this_round, llm)
            if decision is None:
                break

            guest_idx = decision["guest_id"]
            guest = guests[guest_idx]

            # 1. 广播「准备发言」状态
            await broadcast(discussion_id, {
                "event": "guest_preparing",
                "guest_id": guest_idx,
                "guest_name": guest.name,
                "reason": decision["reason"],
            })
            yield {"event": "guest_preparing", "guest_id": guest_idx,
                   "guest_name": guest.name, "reason": decision["reason"]}

            # 2. 生成发言
            speech = await generate_speech(guest, all_messages, decision["reason"], topic, llm)

            msg_id += 1
            all_messages.append({
                "id": msg_id, "role": "guest",
                "sender_name": guest.name, "content": speech,
            })
            spoken_this_round.add(guest_idx)

            # 3. 广播发言
            yield {
                "event": "guest_speak",
                "guest_id": guest_idx,
                "guest_name": guest.name,
                "content": speech,
                "seq_num": msg_id,
                "reason": decision["reason"],
            }
            await broadcast(discussion_id, {
                "event": "guest_speak",
                "guest_id": guest_idx,
                "guest_name": guest.name,
                "content": speech,
                "seq_num": msg_id,
                "reason": decision["reason"],
            })

            # 4. 清除发言状态
            yield {"event": "speak_done", "guest_id": guest_idx}
            await broadcast(discussion_id, {"event": "speak_done", "guest_id": guest_idx})

        # 每轮结束后统一提取观点（基于本轮完整上下文）
        if not stop_flag.is_set():
            try:
                round_start = max(0, len(all_messages) - len(guests) * 2)
                round_messages = all_messages[round_start:]
                new_ops = await extract_opinions(round_messages, all_opinions, llm)
                all_opinions.extend(new_ops)
                # 发送当前所有观点
                opinions_payload = [
                    {
                        "stance_summary": op.stance_summary,
                        "category": op.category,
                        "confidence": op.confidence,
                        "evidence": op.evidence,
                    }
                    for op in all_opinions
                ]
                await broadcast(discussion_id, {
                    "event": "opinions_updated",
                    "opinions": opinions_payload,
                    "new_count": len(new_ops),
                })
                yield {"event": "opinions_updated",
                       "opinions": opinions_payload, "new_count": len(new_ops)}
            except Exception:
                pass

    if not stop_flag.is_set():
        try:
            summary_prompt = build_transcript_context(all_messages, max_recent=20)
            summary_result = await llm.chat([
                {"role": "system", "content": host.get("system_prompt", "你是讨论主持人。")},
                {"role": "user", "content": (
                    f"讨论已结束，请总结：\n{summary_prompt}\n"
                    f"请列出：1) 各方核心观点  2) 达成共识  3) 仍存分歧。控制在300字以内。"
                )},
            ])
            summary = summary_result["choices"][0]["message"]["content"].strip()
        except Exception:
            summary = "讨论已结束，各方发表了各自见解。"

        yield {"event": "discussion_end", "summary": summary}
        await broadcast(discussion_id, {"event": "discussion_end", "summary": summary})
