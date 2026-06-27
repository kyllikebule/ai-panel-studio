"""测试发言调度引擎：禁止轮值抢答、短句发言、决策格式。"""
import pytest
from unittest.mock import AsyncMock, patch

from src.logic.prompt_lib import GuestDef


# ═══════════════════════════════════════════════════════════
# 测试 1: decide_next_speaker 发言调度
# ═══════════════════════════════════════════════════════════
class TestDecideNextSpeaker:
    """发言决策 — 禁止轮值抢答。"""

    MOCK_DECISION = {
        "choices": [{"message": {"content": '{"guest_index":1,"reason":"补充"}'}}]
    }

    @pytest.fixture
    def guests(self):
        return [
            GuestDef(name="李教授", persona="AI伦理学专家", system_prompt="s1", speak_style="学术"),
            GuestDef(name="王博士", persona="技术乐观派", system_prompt="s2", speak_style="理性"),
            GuestDef(name="张律师", persona="法律合规顾问", system_prompt="s3", speak_style="实务"),
        ]

    @pytest.fixture
    def transcript(self):
        return [
            {"role": "host", "sender_name": "主持人", "content": "欢迎各位"},
            {"role": "guest", "sender_name": "李教授", "content": "我认为AI监管很关键"},
            {"role": "guest", "sender_name": "王博士", "content": "我同意部分观点"},
        ]

    @pytest.mark.asyncio
    async def test_prohibits_consecutive_same_speaker(self, guests, transcript):
        """禁止轮值抢答：下一位 != 上一发言人。"""
        from src.backend.services.speech_engine import decide_next_speaker

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {"choices": [{"message": {"content": '{"guest_index":0,"reason":"补充"}'}}]}
            result = await decide_next_speaker(transcript, guests, last_speaker_index=1)

        assert result is not None
        guest_index, reason = result
        assert guest_index != 1, f"禁止连续同一嘉宾发言，实际返回 {guest_index}"

    @pytest.mark.asyncio
    async def test_all_spoken_should_not_return_none(self, guests):
        """所有嘉宾都已发言 1 次后 → 非 None（至少 1 人可补充）。"""
        from src.backend.services.speech_engine import decide_next_speaker

        transcript = [
            {"role": "guest", "sender_name": "李教授", "content": "发言1"},
            {"role": "guest", "sender_name": "王博士", "content": "发言2"},
            {"role": "guest", "sender_name": "张律师", "content": "发言3"},
        ]

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "choices": [{"message": {"content": '{"guest_index":0,"reason":"补充"}'}}]
            }
            result = await decide_next_speaker(transcript, guests, last_speaker_index=2)

        assert result is not None, "所有嘉宾已发言 1 次后不应返回 None"

    @pytest.mark.asyncio
    async def test_empty_transcript_returns_none(self, guests):
        """边界：transcript 为空 → decide_next_speaker 返回 None。"""
        from src.backend.services.speech_engine import decide_next_speaker

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.MOCK_DECISION
            result = await decide_next_speaker([], guests, last_speaker_index=None)

        assert result is None, "空 transcript 应返回 None"

    @pytest.mark.asyncio
    async def test_reason_is_valid(self, guests, transcript):
        """decide_next_speaker 返回的 reason 来自合法集合。"""
        from src.backend.services.speech_engine import decide_next_speaker

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.MOCK_DECISION
            result = await decide_next_speaker(transcript, guests, last_speaker_index=0)

        assert result is not None
        _, reason = result
        assert reason in ("举手", "补充", "反驳"), (
            f"reason='{reason}' 不在合法集合"
        )


# ═══════════════════════════════════════════════════════════
# 测试 2: generate_speech 发言内容生成
# ═══════════════════════════════════════════════════════════
class TestGenerateSpeech:
    """发言生成 — 短句约束。"""

    @pytest.fixture
    def guest(self):
        return GuestDef(
            name="李教授", persona="AI伦理学专家",
            system_prompt="关注AI安全", speak_style="学术严谨",
        )

    @pytest.fixture
    def transcript(self):
        return [
            {"role": "host", "sender_name": "主持人", "content": "请谈谈AI监管"},
        ]

    @pytest.mark.asyncio
    async def test_speech_1_or_2_sentences(self, guest, transcript):
        """短句发言：返回 1-2 句（句号/问号/感叹号 ≤ 2）。"""
        from src.backend.services.speech_engine import generate_speech

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "choices": [{"message": {"content": "我认为AI监管非常必要。它保护了公众利益。"}}]
            }
            speech = await generate_speech(guest, transcript, "补充", "AI监管")

        sentence_marks = [c for c in speech if c in "。？！?!"]
        assert len(sentence_marks) <= 2, (
            f"发言含 {len(sentence_marks)} 句，超过 2 句限制"
        )

    @pytest.mark.asyncio
    async def test_speech_max_200_chars(self, guest, transcript):
        """短句发言：返回内容 ≤ 200 字。"""
        from src.backend.services.speech_engine import generate_speech

        with patch(
            "src.backend.services.speech_engine.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = {
                "choices": [{"message": {"content": "AI监管利大于弊。"}}]
            }
            speech = await generate_speech(guest, transcript, "补充", "AI监管")

        assert len(speech) <= 200, f"发言 {len(speech)} 字，超过 200 字限制"
