"""pytest 共享 fixtures。"""
import pytest


@pytest.fixture
def sample_messages():
    """返回一组标准讨论消息用于测试。"""
    return [
        {"id": 1, "role": "host", "sender_name": "张主持人", "content": "欢迎各位嘉宾，今天讨论AI监管问题。"},
        {"id": 2, "role": "guest", "sender_name": "李教授", "content": "我认为高风险AI必须严格监管。"},
        {"id": 3, "role": "guest", "sender_name": "王博士", "content": "过度监管会扼杀创新。"},
        {"id": 4, "role": "host", "sender_name": "张主持人", "content": "李教授您怎么看王博士的观点？"},
        {"id": 5, "role": "guest", "sender_name": "李教授", "content": "创新固然重要，但安全底线不能突破。"},
    ]


@pytest.fixture
def empty_messages():
    """返回空消息列表。"""
    return []
