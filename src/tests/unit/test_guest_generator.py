"""测试嘉宾生成服务：数量合规、立场差异化、格式校验。"""
import pytest
from unittest.mock import AsyncMock, patch

from src.logic.prompt_lib import GuestDef

# 待测模块（先定义导入路径，当前为 NotImplemented）
# from src.backend.services.guest_generator import (
#     generate_guests,
#     validate_guest_diversity,
#     GuestGenerationError,
# )


# ═══════════════════════════════════════════════════════════
# 测试 1: generate_guests 数量合规
# ═══════════════════════════════════════════════════════════
class TestGenerateGuests:
    """嘉宾生成 — 数量 + 格式校验。"""

    MOCK_LLM_RESPONSE = {
        "choices": [{
            "message": {
                "content": (
                    '[{"name":"李教授","persona":"AI伦理学专家，主张审慎监管","speak_style":"学术严谨","system_prompt":"你是AI伦理学专家"},'
                    '{"name":"王博士","persona":"技术乐观派，相信市场自我调节","speak_style":"理性分析","system_prompt":"你是技术乐观派"},'
                    '{"name":"张律师","persona":"科技合规顾问，关注法律边界","speak_style":"法律实务","system_prompt":"你是科技合规顾问"},'
                    '{"name":"赵研究员","persona":"产业政策分析，宏观视角","speak_style":"政策导向","system_prompt":"你是产业政策研究员"}]'
                )
            }
        }]
    }

    @pytest.mark.asyncio
    async def test_generate_returns_correct_count(self):
        """数量合规：generate_guests('AI监管', 4) 返回 4 个嘉宾。"""
        from src.backend.services.guest_generator import generate_guests

        with patch(
            "src.backend.services.guest_generator.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.MOCK_LLM_RESPONSE
            guests = await generate_guests("AI监管", 4)

        assert len(guests) == 4, f"期望 4 位嘉宾，实际 {len(guests)} 位"

    @pytest.mark.asyncio
    async def test_generate_guests_name_non_empty(self):
        """格式校验：每位嘉宾 name 非空。"""
        from src.backend.services.guest_generator import generate_guests

        with patch(
            "src.backend.services.guest_generator.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.MOCK_LLM_RESPONSE
            guests = await generate_guests("AI监管", 4)

        for i, g in enumerate(guests):
            assert g.name and g.name.strip(), f"嘉宾 #{i} name 为空"

    @pytest.mark.asyncio
    async def test_generate_guests_persona_min_length(self):
        """格式校验：每位嘉宾 persona ≥ 10 字符。"""
        from src.backend.services.guest_generator import generate_guests

        with patch(
            "src.backend.services.guest_generator.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = self.MOCK_LLM_RESPONSE
            guests = await generate_guests("AI监管", 4)

        for i, g in enumerate(guests):
            assert len(g.persona) >= 10, (
                f"嘉宾 #{i} persona 仅 {len(g.persona)} 字符"
            )

    @pytest.mark.asyncio
    async def test_generate_guests_llm_failure_raises(self):
        """错误处理：LLM 调用失败 → 抛出 GuestGenerationError。"""
        from src.backend.services.guest_generator import (
            generate_guests,
            GuestGenerationError,
        )

        with patch(
            "src.backend.services.guest_generator.deepseek_chat",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.side_effect = RuntimeError("DeepSeek API 不可用")
            with pytest.raises(GuestGenerationError, match="DeepSeek"):
                await generate_guests("AI监管", 4)


# ═══════════════════════════════════════════════════════════
# 测试 2: validate_guest_diversity 立场差异化
# ═══════════════════════════════════════════════════════════
class TestValidateGuestDiversity:
    """立场差异化校验。"""

    def test_diverse_guests_returns_true(self):
        """4 个不同 persona → True。"""
        from src.backend.services.guest_generator import validate_guest_diversity

        guests = [
            GuestDef(name="A", persona="主张对高风险人工智能实施严格政府监管以确保公共安全", system_prompt="x"),
            GuestDef(name="B", persona="反对过度监管人工智能认为会严重阻碍科技创新和产业竞争力", system_prompt="x"),
            GuestDef(name="C", persona="从法律合规角度出发关注AI责任归属和数据隐私保护问题", system_prompt="x"),
            GuestDef(name="D", persona="从宏观经济和产业政策视角分析AI对劳动力市场和社会的长期影响", system_prompt="x"),
        ]
        assert validate_guest_diversity(guests) is True

    def test_identical_persona_returns_false(self):
        """边界：2 个完全相同 persona → False。"""
        from src.backend.services.guest_generator import validate_guest_diversity

        guests = [
            GuestDef(name="A", persona="主张严格监管AI发展", system_prompt="x"),
            GuestDef(name="B", persona="主张严格监管AI发展", system_prompt="x"),
        ]
        assert validate_guest_diversity(guests) is False

    def test_single_guest_returns_true(self):
        """边界：单嘉宾 → True（无法比较，视为合规）。"""
        from src.backend.services.guest_generator import validate_guest_diversity

        guests = [GuestDef(name="X", persona="独立研究者", system_prompt="x")]
        assert validate_guest_diversity(guests) is True
