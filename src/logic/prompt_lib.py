"""
AI Panel Studio — Prompt 模板库 & JSON 校验

SDD 阶段产出：Prompt 模板定义、参数化渲染、Provider 格式适配、JSON 校验。
不包含实际 LLM API 调用代码和讨论编排逻辑。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# LLM Provider
# ============================================================

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# ============================================================
# PromptTemplate
# ============================================================

@dataclass
class PromptTemplate:
    """可参数化的 Prompt 模板，支持 OpenAI / Anthropic 双格式输出。"""
    system: str
    user: str

    def render(self, **kwargs: Any) -> Dict[str, str]:
        """渲染为 {system, user} 文本。"""
        return {
            "system": self.system.format(**kwargs),
            "user": self.user.format(**kwargs),
        }

    def to_messages(self, provider: LLMProvider, **kwargs: Any) -> Dict[str, Any]:
        """按 provider 输出对应 API 消息格式。

        OpenAI  → {"messages": [{"role":"system",...}, {"role":"user",...}]}
        Anthropic → {"system": "...", "messages": [{"role":"user",...}]}
        """
        rendered = self.render(**kwargs)
        if provider == LLMProvider.OPENAI:
            return {
                "messages": [
                    {"role": "system", "content": rendered["system"]},
                    {"role": "user", "content": rendered["user"]},
                ]
            }
        elif provider == LLMProvider.ANTHROPIC:
            return {
                "system": rendered["system"],
                "messages": [
                    {"role": "user", "content": rendered["user"]},
                ],
            }


# ============================================================
# 5 个核心 Prompt 模板
# ============================================================

HOST_OPENING = PromptTemplate(
    system=(
        "你是{host_name}，一场专家讨论的主持人。"
        "你的职责：用标准中文开场、提问、串联、总结。保持中立，不偏向任何一方。"
    ),
    user=(
        "讨论主题：{topic}\n"
        "参与嘉宾：{guest_list}\n"
        "当前状态：讨论即将开始。\n\n"
        "请主持人进行开场白：简要介绍主题，欢迎各位嘉宾，提出第一个讨论问题。"
        "控制在200字以内。"
    ),
)

HOST_FOLLOWUP = PromptTemplate(
    system=(
        "你是{host_name}，一场专家讨论的主持人。"
        "你的职责：根据当前讨论进展追问、串联不同嘉宾观点、推动讨论深入。保持中立。"
    ),
    user=(
        "讨论主题：{topic}\n"
        "当前轮次：{current_round}/{max_rounds}\n"
        "最近发言记录：\n{recent_transcript}\n\n"
        "请主持人进行串联或追问：你可以请某位嘉宾对另一位的观点回应，"
        "或提出新角度推动讨论。控制在150字以内。"
    ),
)

HOST_SUMMARY = PromptTemplate(
    system=(
        "你是{host_name}，一场专家讨论的主持人。"
        "你的职责：用标准中文对讨论进行全面总结，提炼共识与分歧。"
    ),
    user=(
        "讨论主题：{topic}\n"
        "完整发言记录：\n{full_transcript}\n"
        "已提炼观点：\n{opinions}\n\n"
        "请主持人对整场讨论进行总结：\n"
        "1. 各方核心观点\n"
        "2. 达成的共识\n"
        "3. 仍存的分歧\n"
        "4. 总结语\n"
        "控制在500字以内。"
    ),
)

GUEST_SPEAK_DECISION = PromptTemplate(
    system=(
        "你是一个专家讨论的协调者。根据当前讨论记录，判断哪位嘉宾最应该发言。\n"
        "规则：\n"
        "- 如果有嘉宾被其他嘉宾提及/反驳，该嘉宾可回应\n"
        "- 如果当前话题有嘉宾尚未发表观点，该嘉宾可补充\n"
        "- 永远不要连续让同一位嘉宾发言\n"
        "- 如果没有人需要发言，返回空"
    ),
    user=(
        "讨论主题：{topic}\n"
        "嘉宾列表：{guest_list}\n"
        "当前轮次：{current_round}/{max_rounds}\n"
        "最近发言记录：\n{recent_transcript}\n\n"
        "请决定下一位发言嘉宾。返回JSON："
        '{{"guest_id": <id>, "reason": "<举手/补充/反驳>", "trigger_message_id": <关联消息id或null>}}'
        "如果无人需要发言，返回：{{}}"
    ),
)

GUEST_SPEAK_CONTENT = PromptTemplate(
    system=(
        "你是{guest_name}，{persona}。\n"
        "{stance_statement}\n"
        "发言要求：{speak_style}\n"
        "仅输出你的发言内容，1-2句话，不要输出角色名或前缀。"
    ),
    user=(
        "讨论主题：{topic}\n"
        "最近发言记录：\n{recent_transcript}\n"
        "本轮你发言的原因是：{speak_reason}\n\n"
        "请以{guest_name}的身份发言："
    ),
)


# ============================================================
# 观点提炼 Prompt
# ============================================================

OPINION_EXTRACT = PromptTemplate(
    system=(
        "你是一个讨论分析助手。从嘉宾发言中提炼核心观点。"
        "输出JSON格式，不要输出任何其他内容。"
    ),
    user=(
        "发言内容：{content}\n"
        "发言人：{speaker_name}（{speaker_role}）\n"
        "上下文讨论主题：{topic}\n\n"
        "请提炼该发言的核心观点：\n"
        '{{"stance_summary": "<一句话观点>", '
        '"category": "consensus|disagreement|neutral", '
        '"confidence": <0.0-1.0>, '
        '"evidence": "<原文关键句>"}}'
        "\n如果该发言没有明确观点，返回：{{}}"
    ),
)


# ============================================================
# JSON 校验
# ============================================================

@dataclass
class GuestDef:
    """标准化的嘉宾定义结构。"""
    name: str
    persona: str
    system_prompt: str
    speak_style: str = ""
    avatar: str = ""


def validate_guest_json(json_str: str) -> GuestDef:
    """校验前端传入的嘉宾定义 JSON，返回标准化 GuestDef。

    必填：name, persona, system_prompt
    可选：speak_style, avatar

    Raises:
        ValueError: 缺少必填字段或类型错误
    """
    import json

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")

    # 必填校验
    for field in ("name", "persona", "system_prompt"):
        if field not in data:
            raise ValueError(f"Missing required field: '{field}'")
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Field '{field}' must be a non-empty string")

    return GuestDef(
        name=data["name"].strip(),
        persona=data["persona"].strip(),
        system_prompt=data["system_prompt"].strip(),
        speak_style=data.get("speak_style", "").strip(),
        avatar=data.get("avatar", "").strip(),
    )


# ============================================================
# 讨论上下文构建
# ============================================================

def build_discussion_context(
    messages: List[Dict[str, Any]],
    max_recent: int = 10,
) -> str:
    """将最近 N 条消息格式化为讨论上下文字符串。

    Args:
        messages: 消息列表，每条含 {role, sender_name, content}
        max_recent: 最多取最近 N 条

    Returns:
        格式化的发言记录文本
    """
    recent = messages[-max_recent:] if len(messages) > max_recent else messages
    lines = []
    for i, msg in enumerate(recent):
        tag = f"[{msg.get('role', 'unknown')}] {msg.get('sender_name', '')}"
        lines.append(f"{tag}: {msg['content']}")
    return "\n".join(lines)


# ============================================================
# Provider 检测
# ============================================================

def detect_provider(provider_str: Optional[str] = None) -> LLMProvider:
    """根据字符串或环境变量检测 LLM Provider。

    Args:
        provider_str: "openai" | "anthropic" | None（自动读环境变量）

    Returns:
        LLMProvider 枚举值
    """
    import os

    if provider_str is None:
        provider_str = os.getenv("LLM_PROVIDER", "openai")

    provider_str = provider_str.lower().strip()
    if provider_str in ("openai", "openai"):
        return LLMProvider.OPENAI
    elif provider_str in ("anthropic", "anthropic"):
        return LLMProvider.ANTHROPIC
    else:
        raise ValueError(f"Unknown LLM provider: {provider_str}")
