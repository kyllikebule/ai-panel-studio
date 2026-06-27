"""测试共识增量提取：分类正确、置信度范围、增量合并。"""
import pytest
from unittest.mock import AsyncMock, patch


# ═══════════════════════════════════════════════════════════
# 测试 1: extract_opinion 分类正确
# ═══════════════════════════════════════════════════════════
class TestExtractOpinion:
    """观点提取 — 分类 + 置信度。"""

    CONSENSUS_RESPONSE = {
        "choices": [{"message": {"content": (
            '{"stance_summary":"各方均认同需要监管AI风险",'
            '"category":"consensus","confidence":0.92,'
            '"evidence":"严格监管是必要的"}'
        )}}]
    }

    DISAGREEMENT_RESPONSE = {
        "choices": [{"message": {"content": (
            '{"stance_summary":"监管力度存在根本分歧",'
            '"category":"disagreement","confidence":0.85,'
            '"evidence":"过度监管可能扼杀创新"}'
        )}}]
    }

    NEUTRAL_RESPONSE = {
        "choices": [{"message": {"content": "{}"}}]
    }

    @pytest.mark.asyncio
    async def test_consensus_speech_returns_consensus(self):
        """共识型发言 → category == 'consensus'。"""
        from src.backend.services.opinion_extractor import extract_opinion

        with patch(
            "src.backend.services.opinion_extractor.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.CONSENSUS_RESPONSE
            result = await extract_opinion(
                "我认为对AI进行严格的监管是确保公众安全的关键",
                "AI监管",
            )

        assert result is not None
        assert result.category == "consensus"

    @pytest.mark.asyncio
    async def test_disagreement_speech_returns_disagreement(self):
        """对立型发言 → category == 'disagreement'。"""
        from src.backend.services.opinion_extractor import extract_opinion

        with patch(
            "src.backend.services.opinion_extractor.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.DISAGREEMENT_RESPONSE
            result = await extract_opinion(
                "我强烈反对这种一刀切的监管方式，它会阻碍技术进步",
                "AI监管",
            )

        assert result is not None
        assert result.category == "disagreement"

    @pytest.mark.asyncio
    async def test_confidence_in_range(self):
        """confidence 在 0.0-1.0 之间。"""
        from src.backend.services.opinion_extractor import extract_opinion

        with patch(
            "src.backend.services.opinion_extractor.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.CONSENSUS_RESPONSE
            result = await extract_opinion("test", "topic")

        assert result is not None
        assert 0.0 <= result.confidence <= 1.0, (
            f"confidence={result.confidence} 不在 [0,1] 范围"
        )

    @pytest.mark.asyncio
    async def test_no_clear_opinion_returns_none(self):
        """边界：无明确观点发言 → extract_opinion 返回 None。"""
        from src.backend.services.opinion_extractor import extract_opinion

        with patch(
            "src.backend.services.opinion_extractor.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.NEUTRAL_RESPONSE
            result = await extract_opinion("嗯，这个问题很有意思，我们可以继续讨论。", "AI监管")

        assert result is None


# ═══════════════════════════════════════════════════════════
# 测试 2: merge_opinions 增量合并
# ═══════════════════════════════════════════════════════════
class TestMergeOpinions:
    """观点增量合并逻辑。"""

    def test_merge_appends_new_opinion(self):
        """追加不重复观点：len 增加 1。"""
        from src.backend.services.opinion_extractor import (
            merge_opinions,
            OpinionResult,
        )

        existing = [
            OpinionResult("监管是必要的", "consensus", 0.8, "证据A"),
        ]
        new = OpinionResult("创新不应被压制", "disagreement", 0.7, "证据B")

        merged = merge_opinions(existing, new)
        assert len(merged) == 2

    def test_merge_updates_confidence_same_stance(self):
        """相同摘要 → len 不变，confidence 取 max。"""
        from src.backend.services.opinion_extractor import (
            merge_opinions,
            OpinionResult,
        )

        existing = [
            OpinionResult("监管是必要的", "consensus", 0.8, "证据A"),
        ]
        new = OpinionResult("监管是必要的", "consensus", 0.9, "证据C")

        merged = merge_opinions(existing, new)
        assert len(merged) == 1, f"期望不增加，实际 {len(merged)}"
        assert merged[0].confidence == 0.9, (
            f"期望confidence=max(0.8,0.9)=0.9，实际={merged[0].confidence}"
        )

    def test_merge_empty_existing(self):
        """边界：空列表 + 新增 → 返回 [new]。"""
        from src.backend.services.opinion_extractor import (
            merge_opinions,
            OpinionResult,
        )

        new = OpinionResult("新观点", "neutral", 0.5, None)
        merged = merge_opinions([], new)
        assert len(merged) == 1
        assert merged[0].stance_summary == "新观点"
