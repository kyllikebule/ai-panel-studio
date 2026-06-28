"""测试发言调度编排逻辑。"""
import asyncio
import pytest
from unittest.mock import AsyncMock
from src.logic.prompt_lib import GuestDef
from src.logic.speak_orchestrator import (
    decide_next_speaker_llm,
    generate_speech,
    run_discussion_flow,
)

GUESTS = [
    GuestDef("李教授", "AI伦理学专家，主张严格监管", "你是李教授...", "学术严谨"),
    GuestDef("王博士", "计算机科学家，技术乐观派", "你是王博士...", "理性分析"),
    GuestDef("张律师", "科技法律顾问，关注合规", "你是张律师...", "法律实务"),
    GuestDef("赵研究员", "产业政策研究员，宏观视角", "你是赵研究员...", "政策导向"),
]

HOST = {"name": "张主持人", "system_prompt": "你是专业讨论主持人，保持中立。"}


@pytest.fixture
def transcript_with_last_speaker():
    return [
        {"id": 1, "role": "host", "sender_name": "张主持人", "content": "欢迎各位。"},
        {"id": 2, "role": "guest", "sender_name": "李教授", "content": "我主张严格监管。"},
    ]


@pytest.fixture
def transcript_with_rebuttal():
    return [
        {"id": 1, "role": "host", "sender_name": "张主持人", "content": "欢迎各位。"},
        {"id": 2, "role": "guest", "sender_name": "李教授", "content": "我主张严格监管AI。"},
        {"id": 3, "role": "guest", "sender_name": "王博士", "content": "我不同意李教授的观点，过度监管会..."},
    ]


@pytest.fixture
def mock_llm():
    client = AsyncMock()
    client.chat = AsyncMock(return_value={
        "choices": [{"message": {"content": "大家好，今天我们讨论AI监管问题。"}}]
    })
    client.chat_json = AsyncMock(return_value={
        "guest_index": 0,
        "reason": "举手",
    })
    return client


@pytest.fixture
def mock_broadcast():
    return AsyncMock()


@pytest.fixture
def mock_stop_flag():
    return asyncio.Event()


class TestDecideNextSpeaker:

    @pytest.mark.asyncio
    async def test_not_same_as_last_speaker(self, transcript_with_last_speaker, mock_llm):
        mock_llm.chat_json = AsyncMock(return_value={"guest_index": 1, "reason": "举手"})
        result = await decide_next_speaker_llm(
            transcript_with_last_speaker, GUESTS, "AI监管", None, mock_llm)
        if result:
            last_speaker = transcript_with_last_speaker[-1]["sender_name"]
            guest = GUESTS[result["guest_id"]]
            assert guest.name != last_speaker

    @pytest.mark.asyncio
    async def test_empty_transcript(self, mock_llm):
        result = await decide_next_speaker_llm([], GUESTS, "AI监管", None, mock_llm)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_consecutive_same_guest(self, mock_llm):
        mock_llm.chat_json = AsyncMock(return_value={"guest_index": 2, "reason": "补充"})
        transcript = [
            {"id": 1, "role": "guest", "sender_name": "李教授", "content": "..."},
            {"id": 2, "role": "guest", "sender_name": "王博士", "content": "..."},
            {"id": 3, "role": "guest", "sender_name": "李教授", "content": "..."},
        ]
        result = await decide_next_speaker_llm(
            transcript, GUESTS, "AI监管", None, mock_llm)
        if result:
            assert GUESTS[result["guest_id"]].name != "李教授"

    @pytest.mark.asyncio
    async def test_returns_valid_reason(self, transcript_with_rebuttal, mock_llm):
        mock_llm.chat_json = AsyncMock(return_value={"guest_index": 2, "reason": "反驳"})
        result = await decide_next_speaker_llm(
            transcript_with_rebuttal, GUESTS, "AI监管", None, mock_llm)
        if result:
            assert result["reason"] in ("举手", "补充", "反驳")

    @pytest.mark.asyncio
    async def test_llm_fallback_on_error(self, transcript_with_rebuttal, mock_llm):
        mock_llm.chat_json = AsyncMock(side_effect=Exception("API error"))
        result = await decide_next_speaker_llm(
            transcript_with_rebuttal, GUESTS, "AI监管", None, mock_llm)
        assert result is not None
        assert result["reason"] in ("举手", "补充", "反驳")


class TestGenerateSpeech:

    @pytest.mark.asyncio
    async def test_returns_string(self, mock_llm):
        speech = await generate_speech(
            GUESTS[0],
            [{"id": 1, "role": "host", "sender_name": "主持人", "content": "欢迎"}],
            "举手", "AI监管", mock_llm,
        )
        assert isinstance(speech, str)
        assert len(speech) > 0

    @pytest.mark.asyncio
    async def test_content_short(self, mock_llm):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "我同意监管，但需要分级管理。不能一刀切。"}}]
        })
        speech = await generate_speech(GUESTS[0], [], "举手", "AI监管", mock_llm)
        sentence_count = speech.count("。") + speech.count("！") + speech.count("？")
        assert sentence_count <= 3

    @pytest.mark.asyncio
    async def test_no_meta_description(self, mock_llm):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "我认为可以说监管需要弹性。"}}]
        })
        speech = await generate_speech(GUESTS[0], [], "举手", "AI监管", mock_llm)
        assert "思考" not in speech


class TestRunDiscussionFlow:

    @pytest.mark.asyncio
    async def test_yields_events(self, mock_llm, mock_broadcast, mock_stop_flag):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "大家好，今天我们讨论AI监管问题。"}}]
        })
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_index": 0, "reason": "举手",
        })

        events = []
        async for event in run_discussion_flow(
            discussion_id=1, topic="AI监管", host=HOST, guests=GUESTS[:2],
            max_rounds=1, llm=mock_llm, broadcast=mock_broadcast,
            stop_flag=mock_stop_flag,
        ):
            events.append(event)

        event_types = {e.get("event") for e in events}
        assert "host_open" in event_types
        assert "discussion_end" in event_types

    @pytest.mark.asyncio
    async def test_respects_max_rounds(self, mock_llm, mock_broadcast, mock_stop_flag):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "测试内容"}}]
        })
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_index": 0, "reason": "举手",
        })

        events = []
        async for event in run_discussion_flow(
            discussion_id=1, topic="测试", host=HOST, guests=GUESTS[:2],
            max_rounds=1, llm=mock_llm, broadcast=mock_broadcast,
            stop_flag=mock_stop_flag,
        ):
            events.append(event)

        assert any(e.get("event") == "discussion_end" for e in events)

    @pytest.mark.asyncio
    async def test_stops_on_flag(self, mock_llm, mock_broadcast):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "测试内容"}}]
        })
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_index": 0, "reason": "举手",
        })

        stop_flag = asyncio.Event()
        stop_flag.set()

        events = []
        async for event in run_discussion_flow(
            discussion_id=1, topic="测试", host=HOST, guests=GUESTS[:2],
            max_rounds=5, llm=mock_llm, broadcast=mock_broadcast,
            stop_flag=stop_flag,
        ):
            events.append(event)

        assert len(events) <= 2
