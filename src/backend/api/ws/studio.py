"""演播厅 WebSocket — 事件驱动讨论编排。"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# 连接池：{discussion_id: [websocket, ...]}
active_connections: dict[int, list[WebSocket]] = {}


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


async def _run_demo_flow(discussion_id: int):
    """演示完整讨论流程——未来替换为 orchestrator 真实调用。"""
    demo_guests = [
        {"id": 0, "name": "李教授", "profession": "AI 伦理学专家", "thinkSummary": "强调高风险 AI 的安全底线"},
        {"id": 1, "name": "王博士", "profession": "计算机科学家", "thinkSummary": "担忧过度监管抑制创新"},
        {"id": 2, "name": "张律师", "profession": "科技法律顾问", "thinkSummary": "主张分层分级监管框架"},
        {"id": 3, "name": "赵研究员", "profession": "产业政策研究员", "thinkSummary": "建议聚焦可解释性与合规"},
    ]

    demo_messages = [
        {"role": "host", "sender_name": "张主持人", "content": "各位嘉宾好，今天我们讨论AI是否应该被严格监管。这是一个备受关注的话题，让我们先请李教授谈谈您的看法。", "seq_num": 1},
        {"role": "guest", "sender_name": "李教授", "content": "谢谢主持人。我认为对于高风险 AI 应用，严格的监管是必要的。医疗诊断、自动驾驶等领域涉及生命安全。", "seq_num": 2, "guest_index": 0},
        {"role": "guest", "sender_name": "王博士", "content": "我理解李教授的担忧，但也想提醒过度监管可能会扼杀创新。AI 发展速度极快。", "seq_num": 3, "guest_index": 1},
        {"role": "guest", "sender_name": "张律师", "content": "从法律实务角度看，我们需要分层分级的监管体系——高风险严格审批，低风险评估备案。", "seq_num": 4, "guest_index": 2},
    ]

    demo_opinions = [
        {"id": 1, "category": "consensus", "stanceSummary": "各方均认同对高风险 AI 应用必须监管", "confidence": 0.92, "evidence": "严格的监管是必要的"},
        {"id": 2, "category": "disagreement", "stanceSummary": "监管力度存在根本分歧", "confidence": 0.85, "evidence": "过度监管可能会扼杀创新"},
        {"id": 3, "category": "consensus", "stanceSummary": "倾向于借鉴欧盟 AI Act 的分级框架", "confidence": 0.78, "evidence": "需要分层分级的监管体系"},
    ]

    summary = (
        "本场讨论围绕 AI 监管问题展开，各方核心观点如下：\n\n"
        "1. 核心观点：李教授强调高风险 AI 的安全底线不可突破；"
        "王博士认为过度监管会抑制技术创新；"
        "张律师提出了分层分级的务实方案；"
        "赵研究员建议借鉴欧盟经验并结合国内产业特点。\n\n"
        "2. 共识：所有嘉宾一致认同对高风险 AI 领域必须实施某种形式的监管，"
        "且分层分级框架是可行方向。\n\n"
        "3. 分歧：在监管力度上存在'严格审批 vs 备案制'的根本分歧，"
        "各方对监管与创新的平衡点判断不同。\n\n"
        "4. 总结：AI 监管是一个需要在安全与创新之间寻找动态平衡的复杂议题，"
        "建议参考国际经验，结合国内产业实际，构建弹性、分层的监管体系。"
    )

    # 逐条推送嘉宾亮相
    await broadcast(discussion_id, "guests_ready", {"guests": demo_guests})
    await asyncio.sleep(0.3)

    # 逐条推送消息（模拟流式效果）
    for msg in demo_messages:
        if msg["role"] == "host":
            # 流式 token 模拟
            tokens = list(msg["content"])
            for i in range(0, len(tokens), 3):
                chunk = "".join(tokens[i:i + 3])
                await broadcast(discussion_id, "token_stream", {
                    "sender_type": "host", "token": chunk, "seq_num": msg["seq_num"],
                })
                await asyncio.sleep(0.02)
            await broadcast(discussion_id, "host_speak", {
                "content": msg["content"], "seq_num": msg["seq_num"],
            })
        else:
            tokens = list(msg["content"])
            for i in range(0, len(tokens), 3):
                chunk = "".join(tokens[i:i + 3])
                await broadcast(discussion_id, "token_stream", {
                    "sender_type": "guest",
                    "sender_id": msg["guest_index"],
                    "token": chunk,
                    "seq_num": msg["seq_num"],
                })
                await asyncio.sleep(0.02)
            await broadcast(discussion_id, "guest_speak", {
                "guest_name": msg["sender_name"],
                "guest_id": msg.get("guest_index", 0),
                "content": msg["content"],
                "seq_num": msg["seq_num"],
            })

        await asyncio.sleep(0.5)

        # 推送观点
        for op in demo_opinions:
            if op.get("id", 0) <= msg["seq_num"]:
                await broadcast(discussion_id, "opinion_extracted", {
                    "opinion_id": op["id"],
                    "message_seq": msg["seq_num"],
                    "stance_summary": op["stanceSummary"],
                    "category": op["category"],
                    "confidence": op["confidence"],
                })
                demo_opinions = [o for o in demo_opinions if o["id"] != op["id"]]
                await asyncio.sleep(0.3)
                break

    await broadcast(discussion_id, "discussion_end", {
        "summary": summary,
    })
    logger.info("演示流程完成: discussion_id=%s", discussion_id)


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
                await broadcast(discussion_id, "system", {
                    "message": "讨论已开始",
                })
                # 启动演示流程（后续替换为 orchestrator 真实编排）
                asyncio.create_task(_run_demo_flow(discussion_id))

            elif action == "pause":
                await broadcast(discussion_id, "system", {"message": "讨论已暂停"})

            elif action == "resume":
                await broadcast(discussion_id, "system", {"message": "讨论已恢复"})

            elif action == "stop":
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
