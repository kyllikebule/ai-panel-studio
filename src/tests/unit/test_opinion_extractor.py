"""测试观点提取函数。"""
import pytest
from unittest.mock import AsyncMock
from src.logic.opinion_extractor import OpinionResult, extract_opinions


MOCK_LLM_EXTRACT_RESPONSE = {
    "opinions": [
        {
            "stance_summary": "高风险AI应用需要强制监管",
            "category": "consensus",
            "confidence": 0.9,
            "evidence": "高风险AI必须严格监管",
        },
        {
            "stance_summary": "监管力度和范围存在分歧",
            "category": "disagreement",
            "confidence": 0.85,
            "evidence": "过度监管会扼杀创新",
        },
    ]
}


@pytest.fixture
def mock_llm():
    client = AsyncMock()
    client.chat_json = AsyncMock(return_value=MOCK_LLM_EXTRACT_RESPONSE)
    return client


@pytest.fixture
def recent_messages():
    return [
        {"id": 1, "sender_name": "李教授", "content": "高风险AI必须严格监管，这是底线。", "role": "guest"},
        {"id": 2, "sender_name": "王博士", "content": "我认为过度监管会扼杀创新，中小企业尤其受伤。", "role": "guest"},
    ]


class TestExtractOpinions:

    @pytest.mark.asyncio
    async def test_returns_opinion_list(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_each_item_is_opinion_result(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        for op in result:
            assert isinstance(op, OpinionResult)

    @pytest.mark.asyncio
    async def test_opinion_has_required_fields(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        for op in result:
            assert op.stance_summary
            assert op.category in ("consensus", "disagreement", "neutral")
            assert 0.0 <= op.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_category_mapping(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        categories = {op.category for op in result}
        assert "consensus" in categories

    @pytest.mark.asyncio
    async def test_empty_messages_returns_empty(self, mock_llm):
        result = await extract_opinions([], [], mock_llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_dedup_with_existing(self, recent_messages, mock_llm):
        """当 existing 已有相同观点时，不应重复添加。"""
        existing = [
            OpinionResult(
                stance_summary="高风险AI应用需要强制监管",
                category="consensus",
                confidence=0.8,
                evidence="旧证据",
            )
        ]
        result = await extract_opinions(recent_messages, existing, mock_llm)
        summaries = {op.stance_summary for op in result}
        assert "高风险AI应用需要强制监管" not in summaries

    @pytest.mark.asyncio
    async def test_confidence_range(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        for op in result:
            assert 0.0 <= op.confidence <= 1.0
