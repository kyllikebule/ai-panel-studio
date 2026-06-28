"""测试嘉宾生成函数。所有 LLM 调用通过 mock 模拟。"""
import pytest
from unittest.mock import AsyncMock
from src.logic.prompt_lib import GuestDef
from src.logic.guest_generator import (
    generate_guests,
    validate_guest_diversity,
    GuestGenerationError,
)


MOCK_GUESTS_JSON = [
    {"name": "李教授", "persona": "AI伦理学专家，主张严格监管", "speak_style": "学术严谨", "system_prompt": "你是李教授..."},
    {"name": "王博士", "persona": "计算机科学家，技术乐观派", "speak_style": "理性分析", "system_prompt": "你是王博士..."},
    {"name": "张律师", "persona": "科技法律顾问，关注合规与平衡", "speak_style": "法律实务", "system_prompt": "你是张律师..."},
    {"name": "赵研究员", "persona": "产业政策研究员，宏观视角", "speak_style": "政策导向", "system_prompt": "你是赵研究员..."},
]

MOCK_GUESTS_SAME_STANCE = [
    {"name": "专家A", "persona": "支持AI发展", "speak_style": "积极", "system_prompt": "你是专家A"},
    {"name": "专家B", "persona": "同样支持AI发展", "speak_style": "积极", "system_prompt": "你是专家B"},
    {"name": "专家C", "persona": "非常支持AI发展", "speak_style": "积极", "system_prompt": "你是专家C"},
    {"name": "专家D", "persona": "也很支持AI发展", "speak_style": "积极", "system_prompt": "你是专家D"},
]


@pytest.fixture
def mock_llm():
    client = AsyncMock()
    client.chat_json = AsyncMock(return_value={"guests": MOCK_GUESTS_JSON})
    return client


@pytest.fixture
def mock_llm_same_stance():
    client = AsyncMock()
    client.chat_json = AsyncMock(return_value={"guests": MOCK_GUESTS_SAME_STANCE})
    return client


class TestGenerateGuests:

    @pytest.mark.asyncio
    async def test_count_compliance_3(self, mock_llm):
        guests = await generate_guests("AI监管", 3, mock_llm)
        assert len(guests) == 3

    @pytest.mark.asyncio
    async def test_count_compliance_5(self, mock_llm):
        guests = await generate_guests("AI监管", 5, mock_llm)
        assert len(guests) == 4  # mock 只有 4 条，取 min

    @pytest.mark.asyncio
    async def test_min_count_raises(self, mock_llm):
        with pytest.raises(ValueError, match="至少需要 2 位"):
            await generate_guests("AI监管", 1, mock_llm)

    @pytest.mark.asyncio
    async def test_max_count_raises(self, mock_llm):
        with pytest.raises(ValueError, match="最多生成 6 位"):
            await generate_guests("AI监管", 7, mock_llm)

    @pytest.mark.asyncio
    async def test_returns_guest_def_list(self, mock_llm):
        guests = await generate_guests("AI监管", 3, mock_llm)
        for g in guests:
            assert isinstance(g, GuestDef)

    @pytest.mark.asyncio
    async def test_all_fields_non_empty(self, mock_llm):
        guests = await generate_guests("AI监管", 3, mock_llm)
        for g in guests:
            assert g.name.strip()
            assert g.persona.strip()
            assert g.speak_style.strip()
            assert g.system_prompt.strip()

    @pytest.mark.asyncio
    async def test_names_unique(self, mock_llm):
        guests = await generate_guests("AI监管", 3, mock_llm)
        names = [g.name for g in guests]
        assert len(names) == len(set(names))

    @pytest.mark.asyncio
    async def test_topic_keyword_in_persona(self, mock_llm):
        guests = await generate_guests("AI监管", 3, mock_llm)
        match_count = sum(1 for g in guests if "监管" in g.persona or "AI" in g.persona)
        assert match_count >= 1

    @pytest.mark.asyncio
    async def test_llm_error_returns_fallback(self, mock_llm):
        mock_llm.chat_json.side_effect = Exception("LLM timeout")
        guests = await generate_guests("AI监管", 2, mock_llm)
        assert len(guests) == 2
        for g in guests:
            assert g.name
            assert g.persona


class TestValidateGuestDiversity:

    def test_diverse_stance_returns_true(self):
        guests = [GuestDef(**g) for g in MOCK_GUESTS_JSON]
        assert validate_guest_diversity(guests) is True

    def test_same_stance_returns_false(self):
        guests = [GuestDef(**g) for g in MOCK_GUESTS_SAME_STANCE]
        assert validate_guest_diversity(guests) is False

    def test_too_few_guests_returns_false(self):
        guests = [GuestDef(**MOCK_GUESTS_JSON[0])]
        assert validate_guest_diversity(guests) is False
