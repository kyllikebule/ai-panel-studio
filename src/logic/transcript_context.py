"""Transcript 上下文构建工具。"""


def build_transcript_context(messages: list[dict], max_recent: int = 10) -> str:
    """将最近 N 条消息格式化为讨论上下文字符串。

    Args:
        messages: 消息列表，每条含 {id, role, sender_name, content}
        max_recent: 最多取最近 N 条

    Returns:
        格式化的发言记录文本，格式: "[role] sender_name: content"
    """
    if not messages:
        return ""

    recent = messages[-max_recent:] if len(messages) > max_recent else messages
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        sender = msg.get("sender_name", "?")
        content = msg.get("content", "")
        lines.append(f"[{role}] {sender}: {content}")
    return "\n".join(lines)


def count_messages_by_role(messages: list[dict], role: str) -> int:
    """统计指定角色的消息数量。"""
    return sum(1 for m in messages if m.get("role") == role)


def get_last_speaker(messages: list[dict]) -> dict | None:
    """获取最后一条消息的发言人信息，空列表返回 None。"""
    if not messages:
        return None
    return messages[-1].copy()
