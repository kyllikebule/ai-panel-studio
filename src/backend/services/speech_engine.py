"""发言调度引擎：决策谁发言 + 生成发言内容 + 编排单轮。"""
import json
import logging

from src.backend.core.config import settings
from src.backend.core.deepseek import deepseek_chat
from src.logic.prompt_lib import GuestDef

logger = logging.getLogger(__name__)

VALID_REASONS = ("举手", "补充", "反驳")


async def decide_next_speaker(
    transcript: list[dict],
    guests: list[GuestDef],
    last_speaker_index: int | None,
) -> tuple[int, str] | None:
    """返回 (guest_index, reason)，禁止连续同嘉宾、禁止轮值，无人需发言返回 None。

    Args:
        transcript: 消息列表 [{role, sender_name, content}, ...]
        guests: 嘉宾列表
        last_speaker_index: 上一发言人在 guests 中的索引，None 表示无发言

    Returns:
        (guest_index, reason) 或 None
    """
    if not transcript:
        return None

    guest_list_text = "\n".join(
        f"[{i}] {g.name} — {g.persona}（{g.speak_style}）"
        for i, g in enumerate(guests)
    )

    recent = transcript[-8:]
    transcript_text = "\n".join(
        f"[{m.get('role', '')}] {m.get('sender_name', '')}: {m.get('content', '')}"
        for m in recent
    )

    last_hint = ""
    if last_speaker_index is not None:
        last_hint = f"\n上一发言人是 [{last_speaker_index}] {guests[last_speaker_index].name}，此轮不可选。"

    prompt = (
        f"嘉宾列表：\n{guest_list_text}\n\n"
        f"讨论记录：\n{transcript_text}\n"
        f"{last_hint}\n"
        f"请选择下一位最应该发言的嘉宾。规则：\n"
        f"1. 禁止连续选同一嘉宾\n"
        f"2. reason 必须是：举手（主动出击）/ 补充（扩展他人观点）/ 反驳（反对他人观点）\n"
        f"3. 无人需要发言时返回 {{}}\n"
        f'仅返回 JSON：{{"guest_index": <int>, "reason": "<举手|补充|反驳>"}} 或 {{}}'
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await deepseek_chat(
            messages=messages,
            model=settings.llm_model,
            temperature=0.5,
            max_tokens=128,
        )
    except Exception as e:
        logger.warning("发言决策 LLM 调用失败: %s", e)
        return None

    raw = result["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not data or "guest_index" not in data:
        return None

    guest_index = int(data["guest_index"])
    reason = str(data.get("reason", "补充"))

    # 硬规则：禁止连续同嘉宾
    if guest_index == last_speaker_index:
        return None

    # 硬规则：禁止越界
    if guest_index < 0 or guest_index >= len(guests):
        return None

    # 硬规则：reason 必须在合法集合
    if reason not in VALID_REASONS:
        reason = "补充"

    return guest_index, reason


async def generate_speech(
    guest: GuestDef,
    transcript: list[dict],
    speak_reason: str,
    topic: str,
) -> str:
    """生成 1-2 句发言内容，≤ 200 字。

    Args:
        guest: 嘉宾定义
        transcript: 讨论记录
        speak_reason: 发言原因（举手/补充/反驳）
        topic: 讨论主题

    Returns:
        1-2 句发言内容
    """
    recent = transcript[-6:]
    transcript_text = "\n".join(
        f"[{m.get('role', '')}] {m.get('sender_name', '')}: {m.get('content', '')}"
        for m in recent
    )

    prompt = (
        f"你是{guest.name}，{guest.persona}。发言风格：{guest.speak_style}。\n"
        f"讨论主题：{topic}\n"
        f"本轮发言原因：{speak_reason}\n"
        f"最近记录：\n{transcript_text}\n\n"
        f"请以{guest.name}的身份发言，仅输出发言内容（1-2句话，≤200字）。"
        f"不要带角色名前缀或引号。"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await deepseek_chat(
            messages=messages,
            model=settings.llm_model,
            temperature=0.7,
            max_tokens=256,
        )
    except Exception as e:
        logger.error("发言生成 LLM 调用失败: %s", e)
        return f"（{guest.name}暂时无法发言）"

    speech = result["choices"][0]["message"]["content"].strip()

    # 硬约束：≤ 200 字
    if len(speech) > 200:
        speech = speech[:200]

    return speech


async def generate_host_summary(
    transcript: list[dict],
    opinions: list,
    topic: str,
) -> str:
    """基于完整 transcript + 提炼的共识/分歧 → 生成标准中文总结，≤ 500 字。

    输出四段式：核心观点 → 共识 → 分歧 → 总结语。

    Args:
        transcript: 完整消息列表
        opinions: 已提炼观点（OpinionResult 列表）
        topic: 讨论主题

    Returns:
        ≤ 500 字的中文总结
    """
    from src.backend.services.opinion_extractor import OpinionResult

    # 组装 transcript 文本
    transcript_text = "\n".join(
        f"[{m.get('role', '')}] {m.get('sender_name', m.get('senderName', ''))}: "
        f"{m.get('content', '')}"
        for m in transcript[-20:]
    )

    # 组装观点文本
    opinions_text = "\n".join(
        f"- [{op.category}] {op.stance_summary}"
        if isinstance(op, OpinionResult)
        else f"- [{op.get('category', '')}] {op.get('stanceSummary', op.get('stance_summary', ''))}"
        for op in opinions
    ) if opinions else "暂无提炼观点"

    prompt = (
        f"你是讨论主持人。请基于以下内容，用标准中文总结整场讨论（≤500字）。\n\n"
        f"讨论主题：{topic}\n\n"
        f"完整发言记录：\n{transcript_text}\n\n"
        f"已提炼观点：\n{opinions_text}\n\n"
        f"请按以下四段式输出：\n"
        f"1. 各方核心观点（简要概括每位嘉宾的核心主张）\n"
        f"2. 达成的共识（列出各方一致同意的点）\n"
        f"3. 仍存的分歧（列出各方观点不同的点）\n"
        f"4. 总结语（一句话总结整场讨论）\n\n"
        f"要求：用自然段落书写，不要用 Markdown 编号列表。"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await deepseek_chat(
            messages=messages,
            model=settings.llm_model,
            temperature=0.5,
            max_tokens=1024,
        )
    except Exception as e:
        logger.error("总结生成 LLM 调用失败: %s", e)
        return f"（总结生成失败：{e}）"

    summary = result["choices"][0]["message"]["content"].strip()

    # 硬约束：≤ 500 字
    if len(summary) > 500:
        summary = summary[:500]

    return summary


async def run_discussion_round(discussion_id: int) -> list[dict]:
    """编排单轮讨论：决策 → 生成 → 返回消息列表。

    Args:
        discussion_id: 讨论 ID

    Returns:
        本轮产生的消息列表 [{role, sender_name, content, guest_index}, ...]
    """
    logger.info("运行讨论轮次: discussion_id=%s", discussion_id)
    # 后续 DDD 阶段接入 DB 查询 transcript + guests
    raise NotImplementedError("编排循环将在 orchestrator 中实现")
