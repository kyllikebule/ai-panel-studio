"""测试 transcript 上下文构建函数。"""
from src.logic.transcript_context import (
    build_transcript_context,
    count_messages_by_role,
    get_last_speaker,
)


class TestBuildTranscriptContext:
    """测试 build_transcript_context 函数。"""

    def test_returns_string(self, sample_messages):
        result = build_transcript_context(sample_messages)
        assert isinstance(result, str)

    def test_includes_sender_names(self, sample_messages):
        result = build_transcript_context(sample_messages)
        assert "张主持人" in result
        assert "李教授" in result
        assert "王博士" in result

    def test_includes_content(self, sample_messages):
        result = build_transcript_context(sample_messages)
        assert "高风险AI必须严格监管" in result

    def test_respects_max_recent(self, sample_messages):
        """max_recent=2 应该只返回最近 2 条消息。"""
        result = build_transcript_context(sample_messages, max_recent=2)
        assert "安全底线不能突破" in result
        assert "欢迎各位嘉宾" not in result

    def test_empty_messages(self, empty_messages):
        result = build_transcript_context(empty_messages)
        assert result == ""

    def test_format_contains_role_tag(self, sample_messages):
        result = build_transcript_context(sample_messages)
        assert "[host]" in result
        assert "[guest]" in result


class TestCountMessagesByRole:
    """测试 count_messages_by_role 函数。"""

    def test_count_host(self, sample_messages):
        assert count_messages_by_role(sample_messages, "host") == 2

    def test_count_guest(self, sample_messages):
        assert count_messages_by_role(sample_messages, "guest") == 3

    def test_count_unknown_role(self, sample_messages):
        assert count_messages_by_role(sample_messages, "system") == 0

    def test_empty_returns_zero(self, empty_messages):
        assert count_messages_by_role(empty_messages, "host") == 0


class TestGetLastSpeaker:
    """测试 get_last_speaker 函数。"""

    def test_returns_last_speaker(self, sample_messages):
        last = get_last_speaker(sample_messages)
        assert last is not None
        assert last["sender_name"] == "李教授"

    def test_empty_returns_none(self, empty_messages):
        assert get_last_speaker(empty_messages) is None
