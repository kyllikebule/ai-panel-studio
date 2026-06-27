"""讨论编排器：串联嘉宾生成 → 发言调度 → 观点提取。"""
import logging

from src.backend.services.guest_generator import generate_guests
from src.backend.services.speech_engine import decide_next_speaker, generate_speech
from src.backend.services.opinion_extractor import extract_opinion, merge_opinions, OpinionResult
from src.logic.prompt_lib import GuestDef

logger = logging.getLogger(__name__)


async def start_discussion(discussion_id: int) -> dict:
    """启动讨论：生成嘉宾 → 创建主持人开场 → 返回初始状态。

    Args:
        discussion_id: 讨论 ID

    Returns:
        {discussion_id, guests, host_opening, ...}
    """
    logger.info("启动讨论: discussion_id=%s", discussion_id)
    # 后续接入 DB 查询 discussion 的 topic + guest_count
    raise NotImplementedError("start_discussion 将在后续 DDD 子任务中接入 DB")


async def run_full_flow(discussion_id: int) -> list[dict]:
    """运行完整讨论编排流程。

    Args:
        discussion_id: 讨论 ID

    Returns:
        全流程产生的消息列表
    """
    logger.info("运行完整编排: discussion_id=%s", discussion_id)
    raise NotImplementedError("run_full_flow 将在后续 DDD 子任务中实现完整循环")
