"""发言调度编排 —— 讨论流程 AI 引擎。"""
import asyncio
from typing import Any, AsyncGenerator, Callable

from .prompt_lib import GuestDef
from .transcript_context import build_transcript_context


def decide_next_speaker(
    transcript: list[dict],
    guests: list[GuestDef],
) -> dict | None:
    """根据 transcript 决定下一位发言嘉宾。

    规则：
    - 禁止连续同一位嘉宾发言
    - 禁止按索引轮值（基于上下文决定）
    - 空 transcript 返回 None（由 host 开场）

    Returns:
        {"guest_id": int, "reason": "举手|补充|反驳", "trigger_msg_id": int|None} | None
    """
    if not transcript:
        return None

    last_speaker = transcript[-1].get("sender_name", "")

    available = []
    for i, g in enumerate(guests):
        if g.name != last_speaker:
            available.append(i)

    if not available:
        return None

    last_guest_msgs = [m for m in reversed(transcript) if m.get("role") == "guest"]

    reason = "举手"
    trigger_msg_id = None

    if len(last_guest_msgs) >= 2:
        last_content = last_guest_msgs[0].get("content", "")
        prev_sender = last_guest_msgs[1].get("sender_name", "")
        if any(kw in last_content for kw in ("不同意", "反对", "不赞同", "质疑")):
            reason = "反驳"
            trigger_msg_id = last_guest_msgs[1].get("id")
        elif last_guest_msgs[0].get("sender_name") != prev_sender:
            reason = "补充"
            trigger_msg_id = last_guest_msgs[0].get("id")

    chosen = available[0]

    return {
        "guest_id": chosen,
        "reason": reason,
        "trigger_msg_id": trigger_msg_id,
    }


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
    from .opinion_extractor import extract_opinions

    all_messages: list[dict] = []
    all_opinions: list = []
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
        spoken_this_round: set[int] = set()

        for _ in range(len(guests)):
            if stop_flag.is_set():
                break

            decision = decide_next_speaker(all_messages, guests)
            if decision is None:
                break

            guest_idx = decision["guest_id"]
            if guest_idx in spoken_this_round:
                continue

            guest = guests[guest_idx]
            speech = await generate_speech(guest, all_messages, decision["reason"], topic, llm)

            msg_id += 1
            all_messages.append({
                "id": msg_id, "role": "guest",
                "sender_name": guest.name, "content": speech,
            })
            spoken_this_round.add(guest_idx)

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
            yield {"event": "speak_done", "guest_id": guest_idx}

            try:
                new_ops = await extract_opinions(all_messages[-3:], all_opinions, llm)
                for op in new_ops:
                    op_dict = {
                        "stance_summary": op.stance_summary,
                        "category": op.category,
                        "confidence": op.confidence,
                        "evidence": op.evidence,
                    }
                    all_opinions.append(op_dict)
                    yield {"event": "opinion_extracted", **op_dict}
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
