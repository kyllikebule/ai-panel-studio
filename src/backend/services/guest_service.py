"""嘉宾业务服务 —— DDD阶段仅定义函数签名。"""


async def get_orchestration_context(discussion_id: int) -> dict:
    """获取讨论编排上下文（transcript + 嘉宾定义 + 观点列表）。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")
