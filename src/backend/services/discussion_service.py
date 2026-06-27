"""讨论业务服务 —— DDD阶段仅定义函数签名，不写AI逻辑。"""


async def create_discussion(topic: str, host_name: str, host_prompt: str, guest_ids: list[int]):
    """创建讨论并绑定主持人+嘉宾。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")


async def update_discussion_status(discussion_id: int, status: str):
    """更新讨论状态。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")


async def start_discussion_flow(discussion_id: int):
    """启动讨论编排流程：主持人开场 → 嘉宾自主发言 → 观点提炼 → 总结。"""
    raise NotImplementedError("AI 编排逻辑将在后续版本实现")
