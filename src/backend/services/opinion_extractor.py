"""共识增量提取服务：从发言中提炼观点，支持增量合并。"""
import json
import logging
from dataclasses import dataclass

from src.backend.core.deepseek import deepseek_chat

logger = logging.getLogger(__name__)


@dataclass
class OpinionResult:
    """观点提取结果。"""
    stance_summary: str
    category: str  # 'consensus' | 'disagreement' | 'neutral'
    confidence: float
    evidence: str | None


async def extract_opinion(
    message_content: str, topic: str
) -> OpinionResult | None:
    """从单条消息提取观点，无明确观点返回 None。

    Args:
        message_content: 发言内容
        topic: 讨论主题

    Returns:
        OpinionResult 或 None
    """
    prompt = (
        f"讨论主题：{topic}\n"
        f"发言内容：{message_content}\n\n"
        f"请分析该发言是否包含明确观点。如果有，提取：\n"
        f"stance_summary（一句话核心观点）\n"
        f"category（consensus 表示与其他发言人一致，disagreement 表示对立，neutral 表示中立或无明确立场）\n"
        f"confidence（置信度 0.0-1.0）\n"
        f"evidence（原文中支撑该观点的关键句，可为 null）\n\n"
        f'仅返回 JSON：{{"stance_summary":"...","category":"...","confidence":0.0,"evidence":"..."}}\n'
        f"如果没有明确观点，返回：{{}}"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await deepseek_chat(
            messages=messages,
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=512,
        )
    except Exception as e:
        logger.warning("观点提取 LLM 调用失败: %s", e)
        return None

    raw = result["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not data or not data.get("stance_summary"):
        return None

    category = data.get("category", "neutral")
    if category not in ("consensus", "disagreement", "neutral"):
        category = "neutral"

    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    return OpinionResult(
        stance_summary=str(data.get("stance_summary", "")),
        category=category,
        confidence=confidence,
        evidence=data.get("evidence") or None,
    )


def merge_opinions(
    existing: list[OpinionResult], new: OpinionResult
) -> list[OpinionResult]:
    """增量合并：相同 stance_summary 更新置信度（取 max），不同则追加。

    Args:
        existing: 已有观点列表
        new: 新提取的观点

    Returns:
        合并后的观点列表（不修改原列表）
    """
    result = list(existing)

    for op in result:
        if op.stance_summary == new.stance_summary:
            op.confidence = max(op.confidence, new.confidence)
            return result

    result.append(new)
    return result
