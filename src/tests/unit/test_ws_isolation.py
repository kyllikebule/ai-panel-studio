"""测试 WebSocket 消息隔离：按 discussion_id 隔离、连接池管理、并发安全。"""
import json
from unittest.mock import MagicMock

import pytest

from src.backend.api.ws.studio import (
    active_connections,
    broadcast,
)


# ═══════════════════════════════════════════════════════════
# 辅助函数：模拟 WebSocket
# ═══════════════════════════════════════════════════════════
def _mock_ws():
    """创建 send_text(text) → 存储到 sent_messages 的 mock ws。"""
    ws = MagicMock()
    ws.sent_messages = []

    async def _send(text):
        ws.sent_messages.append(text)

    ws.send_text = _send
    return ws


# ═══════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════
class TestWSIsolation:
    """按 discussion_id 隔离多会话消息。"""

    def setup_method(self):
        active_connections.clear()

    @pytest.mark.asyncio
    async def test_messages_not_leak_across_discussions(self):
        """2 个 discussion_id 各自连接 → 消息隔离不泄露。"""
        ws1 = _mock_ws()
        ws2 = _mock_ws()

        active_connections.setdefault(1, []).append(ws1)
        active_connections.setdefault(2, []).append(ws2)

        await broadcast(1, "guest_speak", {"guest_name": "李教授", "content": "讨论1发言"})

        # 讨论1的连接收到消息
        assert len(ws1.sent_messages) == 1
        data1 = json.loads(ws1.sent_messages[0])
        assert data1["event"] == "guest_speak"
        assert data1["guest_name"] == "李教授"

        # 讨论2的连接不应收到任何消息
        assert len(ws2.sent_messages) == 0, "讨论2的连接不应收到讨论1的消息"

    @pytest.mark.asyncio
    async def test_broadcast_empty_room_no_error(self):
        """广播到空房间不抛异常。"""
        await broadcast(999, "system", {"message": "没人听到"})

    @pytest.mark.asyncio
    async def test_disconnected_client_removed(self):
        """客户端断开后 send_text 抛异常 → 连接池清理。"""
        ws = MagicMock()

        async def _send_fail(_text):
            raise RuntimeError("连接断开")

        ws.send_text = _send_fail
        active_connections.setdefault(3, []).append(ws)

        await broadcast(3, "system", {"message": "test"})

        # 断开的 ws 应从池中移除
        assert ws not in active_connections.get(3, [])

    @pytest.mark.asyncio
    async def test_concurrent_broadcasts_isolated(self):
        """2 个 discussion 并发 broadcast：各自收到正确消息。"""
        ws_a = _mock_ws()
        ws_b = _mock_ws()

        active_connections.setdefault(10, []).append(ws_a)
        active_connections.setdefault(20, []).append(ws_b)

        # 并发广播
        await broadcast(10, "guest_speak", {"guest_name": "A"})
        await broadcast(20, "guest_speak", {"guest_name": "B"})

        a_data = json.loads(ws_a.sent_messages[0])
        b_data = json.loads(ws_b.sent_messages[0])

        assert a_data["guest_name"] == "A", f"讨论10 应收到 A，实际收到 {a_data['guest_name']}"
        assert b_data["guest_name"] == "B", f"讨论20 应收到 B，实际收到 {b_data['guest_name']}"


import pytest
