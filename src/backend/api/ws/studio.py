"""演播厅 WebSocket — 事件驱动讨论编排。"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# 连接池：{discussion_id: [websocket, ...]}
active_connections: dict[int, list[WebSocket]] = {}
stop_flags: dict[int, asyncio.Event] = {}


async def broadcast(discussion_id: int, event: str, payload: dict):
    """向讨论室所有客户端广播消息。"""
    connections = active_connections.get(discussion_id, [])
    if not connections:
        return
    message = json.dumps({"event": event, **payload}, ensure_ascii=False)
    disconnected = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connections:
            connections.remove(ws)


@router.websocket("/ws/discussion/{discussion_id}")
async def studio_ws(websocket: WebSocket, discussion_id: int):
    await websocket.accept()

    active_connections.setdefault(discussion_id, []).append(websocket)
    logger.info("WS 连接: discussion_id=%s, 连接数=%d", discussion_id, len(active_connections[discussion_id]))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error", "code": "INVALID_JSON",
                    "message": "消息格式无效，需要 JSON",
                }, ensure_ascii=False))
                continue

            action = data.get("action", "")

            if action == "start":
                await broadcast(discussion_id, "system", {"message": "讨论已开始"})
                # 启动真实 AI 编排流程
                stop_flags[discussion_id] = asyncio.Event()
                asyncio.create_task(_run_ai_flow(discussion_id, stop_flags[discussion_id]))

            elif action == "stop":
                flag = stop_flags.get(discussion_id)
                if flag:
                    flag.set()
                await broadcast(discussion_id, "system", {"message": "讨论已结束"})

            else:
                await websocket.send_text(json.dumps({
                    "event": "error", "code": "UNKNOWN_ACTION",
                    "message": f"未知操作: {action}",
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        logger.info("WS 断开: discussion_id=%s", discussion_id)
    finally:
        disc_conns = active_connections.get(discussion_id, [])
        if websocket in disc_conns:
            disc_conns.remove(websocket)
        if not disc_conns:
            active_connections.pop(discussion_id, None)
            stop_flags.pop(discussion_id, None)


async def _run_ai_flow(discussion_id: int, stop_flag: asyncio.Event):
    """从数据库加载讨论数据，调用真实 AI 编排流程。"""
    from sqlalchemy import select
    from src.logic.speak_orchestrator import run_discussion_flow
    from src.logic.prompt_lib import GuestDef
    from src.backend.core.deepseek import deepseek_chat, deepseek_chat_json
    from src.backend.core.config import settings
    from src.backend.db.database import async_session
    from src.backend.db.models import Discussion, Host, Guest, DiscussionGuest

    class LLMClient:
        async def chat(self, messages: list[dict]) -> dict:
            return await deepseek_chat(messages, model=settings.llm_model)

        async def chat_json(self, prompt: str) -> dict:
            return await deepseek_chat_json([{"role": "user", "content": prompt}], model=settings.llm_model)

    async def _broadcast(disc_id: int, payload: dict):
        event = payload.pop("event", "system")
        await broadcast(disc_id, event, payload)

    async with async_session() as db:
        # 1. 加载讨论
        discussion = await db.get(Discussion, discussion_id)
        if not discussion:
            await broadcast(discussion_id, "error", {"message": f"讨论 #{discussion_id} 不存在"})
            return

        # 2. 加载主持人
        host_record = await db.get(Host, discussion.host_id)
        if not host_record:
            await broadcast(discussion_id, "error", {"message": "主持人不存在"})
            return
        host = {"name": host_record.name, "system_prompt": host_record.system_prompt}

        # 3. 加载嘉宾
        result = await db.execute(
            select(DiscussionGuest, Guest)
            .join(Guest, DiscussionGuest.guest_id == Guest.id)
            .where(DiscussionGuest.discussion_id == discussion_id)
        )
        rows = result.all()
        if not rows:
            await broadcast(discussion_id, "error", {"message": "讨论没有嘉宾"})
            return

        guest_defs = []
        guest_list = []
        for dg, g in rows:
            persona = dg.stance_override or g.persona
            guest_defs.append(GuestDef(
                name=g.name,
                persona=persona,
                system_prompt=g.system_prompt,
                speak_style=g.speak_style or "",
            ))
            guest_list.append({
                "guest_id": g.id,
                "name": g.name,
                "persona": persona,
                "speak_style": g.speak_style or "",
            })

        # 4. 发送嘉宾就绪事件
        await broadcast(discussion_id, "guests_ready", {"guests": guest_list})

        max_rounds = discussion.max_rounds or 5

    llm = LLMClient()

    try:
        async for _event in run_discussion_flow(
            discussion_id=discussion_id,
            topic=discussion.topic,
            host=host,
            guests=guest_defs,
            max_rounds=max_rounds,
            llm=llm,
            broadcast=_broadcast,
            stop_flag=stop_flag,
        ):
            pass
    except Exception as e:
        logger.error("AI 编排异常: %s", e)
        await broadcast(discussion_id, "error", {"message": f"编排异常: {e}"})
