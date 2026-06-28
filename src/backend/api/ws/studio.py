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
    """调用真实 AI 编排流程。无嘉宾时使用演示数据。"""
    from src.logic.speak_orchestrator import run_discussion_flow
    from src.logic.prompt_lib import GuestDef
    from src.backend.core.deepseek import deepseek_chat, deepseek_chat_json

    class LLMClient:
        async def chat(self, messages: list[dict]) -> dict:
            return await deepseek_chat(messages)

        async def chat_json(self, prompt: str) -> dict:
            return await deepseek_chat_json([{"role": "user", "content": prompt}])

    host = {"name": "张主持人", "system_prompt": "你是专业讨论主持人，保持中立，用标准中文开场、追问、串联、总结。"}
    guests = [
        GuestDef(name="李教授", persona="AI伦理学专家，主张对高风险AI严格监管",
                 system_prompt="你是李教授，AI伦理学专家。发言时引用学术研究，语气平和但有分量。",
                 speak_style="学术严谨"),
        GuestDef(name="王博士", persona="计算机科学家，技术乐观派",
                 system_prompt="你是王博士，计算机科学家。发言时注重逻辑和数据，强调技术发展的重要性。",
                 speak_style="理性分析"),
        GuestDef(name="张律师", persona="科技法律顾问，关注监管与创新的平衡",
                 system_prompt="你是张律师，科技法律顾问。发言时从法律实务角度出发，强调可操作性。",
                 speak_style="法律实务"),
    ]

    llm = LLMClient()

    async def _broadcast(disc_id: int, payload: dict):
        event = payload.pop("event", "system")
        await broadcast(disc_id, event, payload)

    try:
        async for event in run_discussion_flow(
            discussion_id=discussion_id,
            topic="AI 是否应该被严格监管？",
            host=host,
            guests=guests,
            max_rounds=2,
            llm=llm,
            broadcast=_broadcast,
            stop_flag=stop_flag,
        ):
            pass
    except Exception as e:
        logger.error("AI 编排异常: %s", e)
        await broadcast(discussion_id, "error", {"message": f"编排异常: {e}"})
