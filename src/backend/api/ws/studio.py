"""演播厅 WebSocket — 框架层（不含 AI 编排逻辑）。"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 连接池：{discussion_id: [websocket, ...]}
active_connections: dict[int, list[WebSocket]] = {}


async def broadcast(discussion_id: int, event: str, payload: dict):
    """向讨论室所有客户端广播消息。"""
    connections = active_connections.get(discussion_id, [])
    message = json.dumps({"event": event, **payload}, ensure_ascii=False)
    disconnected = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connections.remove(ws)


@router.websocket("/ws/discussion/{discussion_id}")
async def studio_ws(websocket: WebSocket, discussion_id: int):
    await websocket.accept()

    # 加入连接池
    active_connections.setdefault(discussion_id, []).append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "INVALID_JSON",
                    "message": "消息格式无效，需要 JSON",
                }, ensure_ascii=False))
                continue

            action = data.get("action", "")

            # === DDD 阶段：仅回显 + 框架占位，不写 AI 逻辑 ===
            if action == "start":
                await websocket.send_text(json.dumps({
                    "event": "system",
                    "message": "讨论启动请求已接收。AI 编排逻辑将在后续版本实现。",
                }, ensure_ascii=False))

            elif action == "pause":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已暂停",
                })

            elif action == "resume":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已恢复",
                })

            elif action == "stop":
                await broadcast(discussion_id, "system", {
                    "message": "讨论已结束",
                })
                # 后期在此补充 discussion_end 事件 + summary

            else:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "UNKNOWN_ACTION",
                    "message": f"未知操作: {action}",
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.get(discussion_id, []).remove(websocket)
