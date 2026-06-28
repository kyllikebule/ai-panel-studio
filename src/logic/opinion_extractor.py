"""观点增量提取 —— 从讨论发言中提炼共识与分歧。"""
from dataclasses import dataclass
from typing import Any


@dataclass
class OpinionResult:
    stance_summary: str
    category: str  # 'consensus' | 'disagreement' | 'neutral'
    confidence: float
    evidence: str | None = None


async def extract_opinions(
    messages: list[dict],
    existing_opinions: list[OpinionResult],
    llm_client: Any,
) -> list[OpinionResult]:
    """从最近消息中增量提取观点，与已有观点去重。

    Args:
        messages: 待分析的消息列表 [{id, sender_name, content, role}, ...]
        existing_opinions: 已有观点列表
        llm_client: 注入的 LLM 客户端，需要有 chat_json 方法

    Returns:
        新增观点列表（已去重）
    """
    if not messages:
        return []

    existing_summaries = {op.stance_summary for op in existing_opinions}

    transcript = "\n".join(
        f"[{m.get('sender_name', '?')}]: {m.get('content', '')}"
        for m in messages[-10:]
    )

    try:
        result = await llm_client.chat_json(
            f"""分析以下讨论发言，提取所有明确观点。

发言记录：
{transcript}

请以 JSON 格式返回：{{"opinions": [...]}}
每条观点：{{"stance_summary": "一句话概述", "category": "consensus|disagreement|neutral", "confidence": 0.0-1.0, "evidence": "原文引用"}}
无观点时返回：{{"opinions": []}}"""
        )
        raw_opinions = result.get("opinions", [])
    except Exception:
        return []

    new_opinions = []
    for op in raw_opinions:
        summary = op.get("stance_summary", "").strip()
        if not summary:
            continue
        if summary in existing_summaries:
            continue

        confidence = float(op.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        new_opinions.append(OpinionResult(
            stance_summary=summary,
            category=op.get("category", "neutral"),
            confidence=confidence,
            evidence=op.get("evidence"),
        ))

    return new_opinions
