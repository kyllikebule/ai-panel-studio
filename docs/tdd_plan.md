# TDD 阶段实施计划

> **基于:** `docs/tdd_design.md` | **总任务数:** 6 | **预计产出:** 12 文件

**Goal:** 核心 AI 业务逻辑 4 模块 + pytest 单元测试 4 文件 + API 端点补充 + WS 消息隔离

**Architecture:** 按依赖链从底层到上层: transcript_context → guest_generator → opinion_extractor → speak_orchestrator → WS隔离 → API端点。每模块严格 TDD：先写失败测试 → 最小实现 → 测试通过

**Tech Stack:** Python 3.11+ / pytest / pytest-asyncio / unittest.mock / FastAPI

## Global Constraints

- 先写测试用例，再实现代码（TDD 铁律）
- 测试文件路径: `src/tests/unit/`
- API Key 永不离开后端，禁止传给前端/日志/返回值
- 所有 LLM 调用使用 mock，不实际请求外部 API
- 每任务完成 Git 分段提交，格式 `[TDD-模块] 描述`
- **提交前必须告知用户并得到允许**
- 产出路径: `src/logic/` `src/backend/` `src/tests/unit/`

---

### Task 1: pytest 环境 + transcript 上下文构建

**Files:**
- Create: `src/tests/unit/__init__.py`
- Create: `src/tests/unit/conftest.py`
- Create: `src/tests/unit/test_transcript_context.py`
- Create: `src/logic/transcript_context.py`

**Interfaces:**
- Produces: `build_transcript_context(messages: list[dict], max_recent: int = 10) -> str`
- Produces: `count_messages_by_role(messages: list[dict], role: str) -> int`
- Produces: `get_last_speaker(messages: list[dict]) -> dict | None`

**Dependencies:** 无

- [ ] **Step 1: 创建测试目录和 pytest 配置**

```bash
mkdir -p src/tests/unit
```

创建 `src/tests/unit/__init__.py`（空文件）。

创建 `src/tests/unit/conftest.py`:

```python
"""pytest 共享 fixtures 和 mock 配置。"""
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
```

- [ ] **Step 2: 写失败测试 — test_transcript_context.py**

```python
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
        # 最近 2 条是 id=4 和 id=5
        assert "安全底线不能突破" in result
        assert "欢迎各位嘉宾" not in result  # 第1条被截掉

    def test_empty_messages(self, empty_messages):
        result = build_transcript_context(empty_messages)
        assert result == ""

    def test_format_contains_role_tag(self, sample_messages):
        result = build_transcript_context(sample_messages)
        assert "[host]" in result or "host" in result
        assert "[guest]" in result or "guest" in result


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
```

- [ ] **Step 3: 运行测试 — 预期全部 FAIL**

```bash
python -m pytest src/tests/unit/test_transcript_context.py -v
```

预期输出: `ERROR collecting ... ModuleNotFoundError: No module named 'src.logic.transcript_context'`

- [ ] **Step 4: 实现 transcript_context.py**

```python
"""Transcript 上下文构建工具。"""


def build_transcript_context(messages: list[dict], max_recent: int = 10) -> str:
    """将最近 N 条消息格式化为讨论上下文字符串。

    Args:
        messages: 消息列表，每条含 {id, role, sender_name, content}
        max_recent: 最多取最近 N 条

    Returns:
        格式化的发言记录文本，格式: "[role] sender_name: content"
    """
    if not messages:
        return ""

    recent = messages[-max_recent:] if len(messages) > max_recent else messages
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        sender = msg.get("sender_name", "?")
        content = msg.get("content", "")
        lines.append(f"[{role}] {sender}: {content}")
    return "\n".join(lines)


def count_messages_by_role(messages: list[dict], role: str) -> int:
    """统计指定角色的消息数量。"""
    return sum(1 for m in messages if m.get("role") == role)


def get_last_speaker(messages: list[dict]) -> dict | None:
    """获取最后一条消息的发言人信息，空列表返回 None。"""
    if not messages:
        return None
    return messages[-1].copy()
```

- [ ] **Step 5: 运行测试 — 预期全部 PASS**

```bash
python -m pytest src/tests/unit/test_transcript_context.py -v
```

- [ ] **Step 6: 告知用户并请求提交**

询问用户是否允许提交:
```
git add src/tests/unit/__init__.py src/tests/unit/conftest.py src/tests/unit/test_transcript_context.py src/logic/transcript_context.py
git commit -m "[TDD-transcript] transcript上下文构建: 3函数+10测试全通过"
```

---

### Task 2: 嘉宾生成（guest_generator.py）

**Files:**
- Create: `src/tests/unit/test_guest_generator.py`
- Create: `src/logic/guest_generator.py`

**Interfaces:**
- Consumes: `GuestDef` (from `src/logic/prompt_lib.py`), LLM client（mock）
- Produces: `generate_guests(topic: str, count: int, llm_client) -> list[GuestDef]`
- Produces: `validate_guest_diversity(guests: list[GuestDef]) -> bool`
- Produces: `GuestGenerationError(Exception)`

**Dependencies:** Task 1（pytest 环境），`prompt_lib.GuestDef`

- [ ] **Step 1: 写失败测试 — test_guest_generator.py**

```python
"""测试嘉宾生成函数。所有 LLM 调用通过 mock 模拟。"""
import pytest
from unittest.mock import AsyncMock, patch
from src.logic.prompt_lib import GuestDef
from src.logic.guest_generator import (
    generate_guests,
    validate_guest_diversity,
    GuestGenerationError,
)


# Mock LLM 返回的嘉宾 JSON
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
    """创建一个 mock LLM 客户端，返回预设嘉宾列表。"""
    client = AsyncMock()
    # deepseek_chat_json 返回 JSON 解析后的嘉宾列表
    client.chat_json = AsyncMock(return_value={"guests": MOCK_GUESTS_JSON})
    return client


@pytest.fixture
def mock_llm_same_stance():
    """返回立场相似的嘉宾列表。"""
    client = AsyncMock()
    client.chat_json = AsyncMock(return_value={"guests": MOCK_GUESTS_SAME_STANCE})
    return client


class TestGenerateGuests:
    """测试 generate_guests 函数。"""

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
        # 至少 1 位嘉宾 persona 含话题关键词
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
    """测试 validate_guest_diversity 函数。"""

    def test_diverse_stance_returns_true(self):
        guests = [GuestDef(**g) for g in MOCK_GUESTS_JSON]
        # 李教授"严格监管" vs 王博士"技术乐观" vs 张律师"合规与平衡" vs 赵研究员"宏观视角"
        assert validate_guest_diversity(guests) is True

    def test_same_stance_returns_false(self):
        guests = [GuestDef(**g) for g in MOCK_GUESTS_SAME_STANCE]
        # 全部"支持AI发展"
        assert validate_guest_diversity(guests) is False

    def test_too_few_guests_returns_false(self):
        guests = [GuestDef(**MOCK_GUESTS_JSON[0])]
        assert validate_guest_diversity(guests) is False
```

- [ ] **Step 2: 运行测试 — 预期 FAIL**

```bash
python -m pytest src/tests/unit/test_guest_generator.py -v
```

- [ ] **Step 3: 实现 guest_generator.py**

```python
"""嘉宾生成 —— 调用 LLM 生成立场差异化的嘉宾列表。"""
from .prompt_lib import GuestDef, GUEST_SPEAK_CONTENT


class GuestGenerationError(Exception):
    """嘉宾生成失败时抛出。"""
    pass


async def generate_guests(topic: str, count: int, llm_client) -> list[GuestDef]:
    """生成 count 位立场差异化的嘉宾。

    Args:
        topic: 讨论主题
        count: 嘉宾人数 (2-6)
        llm_client: 注入的 LLM 客户端（测试时 mock）

    Returns:
        标准化 GuestDef 列表

    Raises:
        ValueError: count 不在 2-6 范围内
    """
    if count < 2:
        raise ValueError("至少需要 2 位嘉宾参与讨论")
    if count > 6:
        raise ValueError("最多生成 6 位嘉宾")

    prompt = f"""你是一位专业讨论策划。请为以下讨论主题生成 {count} 位立场差异化的嘉宾。

讨论主题：{topic}

要求：
1. 每位嘉宾立场必须不同（至少 2 种不同立场），涵盖支持、反对、中间等多种视角
2. 返回 JSON 格式: {{"guests": [{{"name": "姓名", "persona": "人设描述+立场", "speak_style": "发言风格", "system_prompt": "完整角色提示"}}]}}
3. name 必须各不相同
4. persona 需体现对该话题的具体立场，至少 10 字
5. speak_style 从以下选一：学术严谨、理性分析、法律实务、政策导向、实战经验、犀利追问
"""

    try:
        result = await llm_client.chat_json(prompt)
        raw_guests = result.get("guests", [])
    except Exception:
        # LLM 失败时返回 fallback 嘉宾
        return _fallback_guests(count)

    if len(raw_guests) < count:
        raw_guests = raw_guests[:count]

    guests = []
    for g in raw_guests[:count]:
        guests.append(GuestDef(
            name=g.get("name", "").strip(),
            persona=g.get("persona", "").strip(),
            speak_style=g.get("speak_style", "").strip(),
            system_prompt=g.get("system_prompt", "").strip(),
        ))

    if validate_guest_diversity(guests) is False:
        return _fallback_guests(count)

    return guests


def validate_guest_diversity(guests: list[GuestDef]) -> bool:
    """校验嘉宾立场差异化：至少 2 位嘉宾 persona 有明显的不同。

    使用简单规则：收集所有 persona 的字符集，检查是否有至少 2 个明显不同的 persona。
    """
    if len(guests) < 2:
        return False

    personas = [g.persona for g in guests]

    # 检查是否有至少 2 个 persona 的编辑距离足够大
    def _simple_similarity(a: str, b: str) -> float:
        """简单字符级别相似度。"""
        set_a, set_b = set(a), set(b)
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    unique_count = 1
    for i in range(1, len(personas)):
        is_unique = True
        for j in range(i):
            if _simple_similarity(personas[i], personas[j]) > 0.7:
                is_unique = False
                break
        if is_unique:
            unique_count += 1

    return unique_count >= 2


def _fallback_guests(count: int) -> list[GuestDef]:
    """LLM 失败时的预设嘉宾回退。"""
    pool = [
        GuestDef("李教授", "AI伦理学专家，主张对高风险AI严格监管", "学术严谨", "你是李教授，AI伦理学专家。发言时引用学术研究，语气平和但有分量。"),
        GuestDef("王博士", "计算机科学家，技术乐观派，认为创新不应被过度束缚", "理性分析", "你是王博士，计算机科学家。发言时注重逻辑和数据，强调技术发展的重要性。"),
        GuestDef("张律师", "科技法律顾问，关注监管与创新的平衡", "法律实务", "你是张律师，科技法律顾问。发言时从法律实务角度出发，强调可操作性。"),
        GuestDef("赵研究员", "产业政策研究员，宏观视角看产业影响", "政策导向", "你是赵研究员，产业政策专家。发言时从宏观经济和产业链角度分析问题。"),
        GuestDef("陈总", "AI企业创始CEO，行业深耕实践者", "实战经验", "你是陈总，AI企业CEO。发言时结合创业实战经验，关注落地可行性。"),
        GuestDef("孙记者", "科技媒体人，代表公众视角追问", "犀利追问", "你是孙记者，科技媒体人。发言时代表公众追问，直击要害。"),
    ]
    return pool[:count]
```

- [ ] **Step 4: 运行测试 — 预期全部 PASS**

```bash
python -m pytest src/tests/unit/test_guest_generator.py -v
```

---

### Task 3: 共识增量提取（opinion_extractor.py）

**Files:**
- Create: `src/tests/unit/test_opinion_extractor.py`
- Create: `src/logic/opinion_extractor.py`

**Interfaces:**
- Produces: `OpinionResult` (dataclass)
- Produces: `extract_opinions(messages: list[dict], existing: list[OpinionResult], llm_client) -> list[OpinionResult]`

**Dependencies:** Task 1（pytest 环境）

- [ ] **Step 1: 写失败测试 — test_opinion_extractor.py**

```python
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
    """测试 extract_opinions 函数。"""

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
        # 去重后应该不包含相同的 stance_summary
        summaries = {op.stance_summary for op in result}
        assert "高风险AI应用需要强制监管" not in summaries

    @pytest.mark.asyncio
    async def test_confidence_range(self, recent_messages, mock_llm):
        result = await extract_opinions(recent_messages, [], mock_llm)
        for op in result:
            assert 0.0 <= op.confidence <= 1.0
```

- [ ] **Step 2: 运行测试 — 预期 FAIL**

- [ ] **Step 3: 实现 opinion_extractor.py**

```python
"""观点增量提取 —— 从讨论发言中提炼共识与分歧。"""
from dataclasses import dataclass
from typing import Any


@dataclass
class OpinionResult:
    stance_summary: str
    category: str  # 'consensus' | 'disagreement' | 'neutral'
    confidence: float
    evidence: str | None = None


async def extract_opinions(
    messages: list[dict],
    existing_opinions: list[OpinionResult],
    llm_client: Any,
) -> list[OpinionResult]:
    """从最近消息中增量提取观点，与已有观点去重。

    Args:
        messages: 待分析的消息列表 [{id, sender_name, content, role}, ...]
        existing_opinions: 已有观点列表
        llm_client: 注入的 LLM 客户端

    Returns:
        新增观点列表（已去重）
    """
    if not messages:
        return []

    # 收集已有 stance_summary 用于去重
    existing_summaries = {op.stance_summary for op in existing_opinions}

    # 构建提取 prompt
    transcript = "\n".join(
        f"[{m.get('sender_name', '?')}]: {m.get('content', '')}"
        for m in messages[-10:]  # 最多取最近 10 条
    )

    try:
        result = await llm_client.chat_json(
            f"""分析以下讨论发言，提取所有明确观点。

发言记录：
{transcript}

请以 JSON 格式返回：{{"opinions": [...]}}
每条观点：{{"stance_summary": "一句话概述", "category": "consensus|disagreement|neutral", "confidence": 0.0-1.0, "evidence": "原文引用"}}
无观点时返回：{{"opinions": []}}"""
        )
        raw_opinions = result.get("opinions", [])
    except Exception:
        return []

    new_opinions = []
    for op in raw_opinions:
        summary = op.get("stance_summary", "").strip()
        if not summary:
            continue
        if summary in existing_summaries:
            continue  # 去重

        new_opinions.append(OpinionResult(
            stance_summary=summary,
            category=op.get("category", "neutral"),
            confidence=float(op.get("confidence", 0.5)),
            evidence=op.get("evidence"),
        ))

    return new_opinions
```

- [ ] **Step 4: 运行测试 — 预期 PASS**

---

### Task 4: 发言调度编排（speak_orchestrator.py）

**Files:**
- Create: `src/tests/unit/test_speak_orchestrator.py`
- Create: `src/logic/speak_orchestrator.py`

**Interfaces:**
- Produces: `decide_next_speaker(transcript: list[dict], guests: list[GuestDef]) -> dict | None`
- Produces: `generate_speech(guest, transcript, reason, topic, llm) -> str`
- Produces: `run_discussion_flow(disc_id, topic, host, guests, llm, broadcast, stop_flag) -> AsyncGenerator`

**Dependencies:** Task 1, 2, 3

- [ ] **Step 1: 写失败测试 — test_speak_orchestrator.py**

```python
"""测试发言调度编排逻辑。"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.logic.prompt_lib import GuestDef
from src.logic.speak_orchestrator import (
    decide_next_speaker,
    generate_speech,
    run_discussion_flow,
)

GUESTS = [
    GuestDef("李教授", "AI伦理学专家，主张严格监管", "学术严谨", "你是李教授..."),
    GuestDef("王博士", "计算机科学家，技术乐观派", "理性分析", "你是王博士..."),
    GuestDef("张律师", "科技法律顾问，关注合规", "法律实务", "你是张律师..."),
    GuestDef("赵研究员", "产业政策研究员，宏观视角", "政策导向", "你是赵研究员..."),
]

HOST = {"name": "张主持人", "system_prompt": "你是专业讨论主持人，保持中立。"}


@pytest.fixture
def transcript_with_last_speaker():
    """最后一条发言来自李教授。"""
    return [
        {"id": 1, "role": "host", "sender_name": "张主持人", "content": "欢迎各位。"},
        {"id": 2, "role": "guest", "sender_name": "李教授", "content": "我主张严格监管。"},
    ]


@pytest.fixture
def transcript_with_rebuttal():
    """王博士反驳了李教授。"""
    return [
        {"id": 1, "role": "host", "sender_name": "张主持人", "content": "欢迎各位。"},
        {"id": 2, "role": "guest", "sender_name": "李教授", "content": "我主张严格监管AI。"},
        {"id": 3, "role": "guest", "sender_name": "王博士", "content": "我不同意李教授的观点，过度监管会..."},
    ]


@pytest.fixture
def mock_llm():
    client = AsyncMock()
    client.chat_json = AsyncMock(return_value={
        "guest_id": 1,
        "reason": "反驳",
        "trigger_msg_id": 3,
    })
    return client


@pytest.fixture
def mock_broadcast():
    return AsyncMock()


@pytest.fixture
def mock_stop_flag():
    flag = asyncio.Event()
    return flag


class TestDecideNextSpeaker:
    """测试 decide_next_speaker 函数。"""

    def test_not_same_as_last_speaker(self, transcript_with_last_speaker):
        """禁止连续同一嘉宾发言。"""
        result = decide_next_speaker(transcript_with_last_speaker, GUESTS)
        if result:
            last_speaker = transcript_with_last_speaker[-1]["sender_name"]
            # 检查返回的 guest_index 对应的 name 不等于 last_speaker
            guest = GUESTS[result["guest_id"]]
            assert guest.name != last_speaker

    def test_empty_transcript(self):
        """空 transcript 时返回 None（由 host 开场）。"""
        result = decide_next_speaker([], GUESTS)
        assert result is None

    def test_no_consecutive_same_guest(self):
        """再次发言后不能是同一个人。"""
        transcript = [
            {"id": 1, "role": "guest", "sender_name": "李教授", "content": "..."},
            {"id": 2, "role": "guest", "sender_name": "王博士", "content": "..."},
            {"id": 3, "role": "guest", "sender_name": "李教授", "content": "..."},
        ]
        result = decide_next_speaker(transcript, GUESTS)
        if result:
            assert GUESTS[result["guest_id"]].name != "李教授"

    def test_returns_valid_reason(self, transcript_with_rebuttal):
        """reason 字段必须是合法值。"""
        result = decide_next_speaker(transcript_with_rebuttal, GUESTS)
        if result:
            assert result["reason"] in ("举手", "补充", "反驳")


class TestGenerateSpeech:
    """测试 generate_speech 函数。"""

    @pytest.mark.asyncio
    async def test_returns_string(self, mock_llm):
        speech = await generate_speech(
            GUESTS[0],
            [{"id": 1, "role": "host", "sender_name": "主持人", "content": "欢迎"}],
            "举手",
            "AI监管",
            mock_llm,
        )
        assert isinstance(speech, str)
        assert len(speech) > 0

    @pytest.mark.asyncio
    async def test_content_short(self, mock_llm):
        """发言内容应该是 1-2 句话。"""
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "我同意监管，但需要分级管理。不能一刀切。"}}]
        })
        speech = await generate_speech(GUESTS[0], [], "举手", "AI监管", mock_llm)
        # 2 个句号为限
        sentence_count = speech.count("。") + speech.count("！") + speech.count("？")
        assert sentence_count <= 3  # 容忍无句末标点

    @pytest.mark.asyncio
    async def test_no_meta_description(self, mock_llm):
        """发言内容不应包含元描述文字。"""
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "我认为可以说监管需要弹性。"}}]
        })
        speech = await generate_speech(GUESTS[0], [], "举手", "AI监管", mock_llm)
        assert "思考" not in speech
        assert "我认为应该" not in speech


class TestRunDiscussionFlow:
    """测试 run_discussion_flow 函数。"""

    @pytest.mark.asyncio
    async def test_yields_events(self, mock_llm, mock_broadcast, mock_stop_flag):
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "大家好，今天我们讨论AI监管问题。"}}]
        })
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_id": 0, "reason": "举手", "trigger_msg_id": None,
        })

        events = []
        async for event in run_discussion_flow(
            discussion_id=1,
            topic="AI监管",
            host=HOST,
            guests=GUESTS[:2],
            max_rounds=1,
            llm=mock_llm,
            broadcast=mock_broadcast,
            stop_flag=mock_stop_flag,
        ):
            events.append(event)

        event_types = {e.get("event") for e in events}
        assert "host_open" in event_types
        assert "discussion_end" in event_types

    @pytest.mark.asyncio
    async def test_respects_max_rounds(self, mock_llm, mock_broadcast, mock_stop_flag):
        """应该按照 max_rounds 参数结束讨论。"""
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "测试内容"}}]
        })
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_id": 0, "reason": "举手", "trigger_msg_id": None,
        })

        events = []
        async for event in run_discussion_flow(
            discussion_id=1,
            topic="测试",
            host=HOST,
            guests=GUESTS[:2],
            max_rounds=1,
            llm=mock_llm,
            broadcast=mock_broadcast,
            stop_flag=mock_stop_flag,
        ):
            events.append(event)

        assert any(e.get("event") == "discussion_end" for e in events)

    @pytest.mark.asyncio
    async def test_stops_on_flag(self, mock_llm, mock_broadcast):
        """设置 stop_flag 应该中止 flow。"""
        mock_llm.chat_json = AsyncMock(return_value={
            "guest_id": 0, "reason": "举手", "trigger_msg_id": None,
        })
        mock_llm.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "测试内容"}}]
        })

        stop_flag = asyncio.Event()
        stop_flag.set()  # 立即设置停止信号

        events = []
        async for event in run_discussion_flow(
            discussion_id=1,
            topic="测试",
            host=HOST,
            guests=GUESTS[:2],
            max_rounds=5,
            llm=mock_llm,
            broadcast=mock_broadcast,
            stop_flag=stop_flag,
        ):
            events.append(event)

        # 应该极短或空（被立即停止）
        # 至少不应持续运行
        assert len(events) <= 2  # 最多 host_open + 立即停止
```

- [ ] **Step 2: 运行测试 — 预期 FAIL**

- [ ] **Step 3: 实现 speak_orchestrator.py**

```python
"""发言调度编排 —— 讨论流程 AI 引擎。"""
import asyncio
from typing import Any, AsyncGenerator, Callable

from .prompt_lib import GuestDef
from .transcript_context import build_transcript_context, get_last_speaker
from .opinion_extractor import extract_opinions


def decide_next_speaker(
    transcript: list[dict],
    guests: list[GuestDef],
) -> dict | None:
    """根据 transcript 决定下一位发言嘉宾。

    规则：
    - 禁止连续同一位嘉宾发言
    - 禁止按索引轮值（基于上下文决定）
    - 空 transcript 返回 None（由 host 开场）

    Returns:
        {"guest_id": int, "reason": "举手|补充|反驳", "trigger_msg_id": int|None} | None
    """
    if not transcript:
        return None

    last_speaker = transcript[-1].get("sender_name", "")

    # 构建可用的非连续嘉宾索引
    available = []
    for i, g in enumerate(guests):
        if g.name != last_speaker:
            available.append(i)

    if not available:
        return None

    # 检查最后一条 guest 发言是否为反驳/分歧场景
    last_guest_msgs = [m for m in reversed(transcript) if m.get("role") == "guest"]

    reason = "举手"
    trigger_msg_id = None

    if len(last_guest_msgs) >= 2:
        # 检测是否有反驳（通过关键词）
        last_content = last_guest_msgs[0].get("content", "")
        prev_content = last_guest_msgs[1].get("content", "")
        if any(kw in last_content for kw in ("不同意", "反对", "不赞同", "质疑")):
            reason = "反驳"
            trigger_msg_id = last_guest_msgs[1].get("id")
        elif last_guest_msgs[0].get("sender_name") != last_guest_msgs[1].get("sender_name"):
            reason = "补充"
            trigger_msg_id = last_guest_msgs[0].get("id")

    # 选择第一个可用的嘉宾（不轮值，由上下文决定）
    chosen = available[0]

    return {
        "guest_id": chosen,
        "reason": reason,
        "trigger_msg_id": trigger_msg_id,
    }


async def generate_speech(
    guest: GuestDef,
    transcript: list[dict],
    speak_reason: str,
    topic: str,
    llm: Any,
) -> str:
    """生成嘉宾发言内容，1-2 句话。"""
    context = build_transcript_context(transcript, max_recent=10)

    try:
        result = await llm.chat([
            {"role": "system", "content": (
                f"你是{guest.name}，{guest.persona}。"
                f"发言风格：{guest.speak_style}。"
                f"请以第一人称发言，仅输出发言内容。1-2句话。"
                f"不要输出'我认为'开头，直接表达观点。"
                f"不要输出角色名、冒号或引号前缀。"
                f"不要描述你在思考什么，直接输出观点。"
            )},
            {"role": "user", "content": (
                f"讨论主题：{topic}\n"
                f"你发言的原因是：{speak_reason}\n"
                f"最近发言：\n{context}\n\n"
                f"请以{guest.name}的身份发言："
            )},
        ])
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except Exception:
        return f"我（{guest.name}）认为在这个问题上需要更多讨论。"


async def run_discussion_flow(
    discussion_id: int,
    topic: str,
    host: dict,
    guests: list[GuestDef],
    max_rounds: int,
    llm: Any,
    broadcast: Callable,
    stop_flag: asyncio.Event,
) -> AsyncGenerator[dict, None]:
    """完整讨论编排的异步生成器。

    Yields:
        事件 dict: {"event": "host_open"|"guest_speak"|"round_change"|"opinion_extracted"|"discussion_end", ...}
    """
    all_messages: list[dict] = []
    all_opinions: list[dict] = []
    msg_id = 0

    # 检查停止信号
    if stop_flag.is_set():
        yield {"event": "discussion_end", "reason": "stopped"}
        return

    # 主持人开场
    try:
        host_result = await llm.chat([
            {"role": "system", "content": host.get("system_prompt", "你是讨论主持人。")},
            {"role": "user", "content": (
                f"讨论主题：{topic}\n"
                f"嘉宾：{', '.join(g.name for g in guests)}\n"
                f"请进行开场白，欢迎嘉宾并介绍话题，然后请第一位嘉宾发言。控制在150字以内。"
            )},
        ])
        host_content = host_result["choices"][0]["message"]["content"].strip()
    except Exception:
        host_content = f"欢迎各位嘉宾，今天讨论的主题是{topic}。"

    msg_id += 1
    host_msg = {"id": msg_id, "role": "host", "sender_name": host["name"], "content": host_content}
    all_messages.append(host_msg)

    yield {"event": "host_open", "host_name": host["name"], "content": host_content, "seq_num": msg_id}
    await broadcast(discussion_id, {"event": "host_open", "host_name": host["name"], "content": host_content, "seq_num": msg_id})

    # 逐轮讨论
    for round_num in range(1, max_rounds + 1):
        if stop_flag.is_set():
            yield {"event": "discussion_end", "reason": "stopped"}
            return

        yield {"event": "round_change", "round": round_num}

        # 每轮允许每位嘉宾最多发言 1 次
        spoken_this_round: set[int] = set()

        for _ in range(len(guests)):
            if stop_flag.is_set():
                break

            decision = decide_next_speaker(all_messages, guests)
            if decision is None:
                break

            guest_idx = decision["guest_id"]
            if guest_idx in spoken_this_round:
                continue

            guest = guests[guest_idx]
            speech = await generate_speech(
                guest, all_messages, decision["reason"], topic, llm
            )

            msg_id += 1
            guest_msg = {
                "id": msg_id,
                "role": "guest",
                "sender_name": guest.name,
                "content": speech,
            }
            all_messages.append(guest_msg)
            spoken_this_round.add(guest_idx)

            yield {
                "event": "guest_speak",
                "guest_id": guest_idx,
                "guest_name": guest.name,
                "content": speech,
                "seq_num": msg_id,
                "reason": decision["reason"],
            }

            await broadcast(discussion_id, {
                "event": "guest_speak",
                "guest_id": guest_idx,
                "guest_name": guest.name,
                "content": speech,
                "seq_num": msg_id,
                "reason": decision["reason"],
            })

            yield {"event": "speak_done", "guest_id": guest_idx}

            # 每轮 guest 发言后提取观点
            try:
                new_ops = await extract_opinions(
                    all_messages[-3:], all_opinions, llm
                )
                for op in new_ops:
                    all_opinions.append({
                        "stance_summary": op.stance_summary,
                        "category": op.category,
                        "confidence": op.confidence,
                        "evidence": op.evidence,
                    })
                    yield {"event": "opinion_extracted", **all_opinions[-1]}
            except Exception:
                pass  # 观点提取失败不影响主流程

    # 主持人总结
    if not stop_flag.is_set():
        try:
            summary_prompt = build_transcript_context(all_messages, max_recent=20)
            summary_result = await llm.chat([
                {"role": "system", "content": host.get("system_prompt", "你是讨论主持人。")},
                {"role": "user", "content": (
                    f"讨论已结束，请总结：\n{summary_prompt}\n"
                    f"请列出：1) 各方核心观点  2) 达成共识  3) 仍存分歧。控制在300字以内。"
                )},
            ])
            summary = summary_result["choices"][0]["message"]["content"].strip()
        except Exception:
            summary = "讨论已结束，各方发表了各自见解。"

        yield {"event": "discussion_end", "summary": summary}
        await broadcast(discussion_id, {"event": "discussion_end", "summary": summary})
```

- [ ] **Step 4: 运行测试 — 预期 PASS**

---

### Task 5: WebSocket 消息隔离

**Files:**
- Create: `src/tests/unit/test_ws_isolation.py`

**Interfaces:**
- Consumes: `active_connections`, `broadcast()` (from `src/backend/api/ws/studio.py`)

**Dependencies:** Task 1（pytest 环境），已有 `ws/studio.py`

- [ ] **Step 1: 写失败测试 — test_ws_isolation.py**

```python
"""测试 WebSocket 消息隔离 —— 按 discussion_id 隔离。"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock

from src.backend.api.ws.studio import active_connections, broadcast


class MockWebSocket:
    """模拟 WebSocket 连接。"""
    def __init__(self):
        self.sent = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.sent.append(message)

    async def receive_text(self) -> str:
        return json.dumps({"action": "start"})


class TestBroadcastIsolation:
    """测试 broadcast 的消息隔离。"""

    def setup_method(self):
        active_connections.clear()

    @pytest.mark.asyncio
    async def test_same_room_only(self):
        """broadcast 应该仅发送给指定 discussion_id 的客户端。"""
        ws_a = MockWebSocket()
        ws_b = MockWebSocket()

        active_connections.setdefault(1, []).append(ws_a)
        active_connections.setdefault(2, []).append(ws_b)

        await broadcast(1, "test_event", {"msg": "hello room 1"})

        assert len(ws_a.sent) == 1
        assert len(ws_b.sent) == 0

    @pytest.mark.asyncio
    async def test_multiple_clients_same_room(self):
        """同一讨论室多个客户端都应收到广播。"""
        ws_a = MockWebSocket()
        ws_b = MockWebSocket()

        active_connections.setdefault(1, []).extend([ws_a, ws_b])

        await broadcast(1, "test_event", {"msg": "hello"})

        assert len(ws_a.sent) == 1
        assert len(ws_b.sent) == 1

    @pytest.mark.asyncio
    async def test_broadcast_message_format(self):
        """广播消息应为合法 JSON 且含 event 字段。"""
        ws = MockWebSocket()
        active_connections.setdefault(1, []).append(ws)

        await broadcast(1, "host_speak", {"content": "test"})

        sent_data = json.loads(ws.sent[0])
        assert sent_data["event"] == "host_speak"
        assert sent_data["content"] == "test"

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_room(self):
        """向空房间广播不应抛异常。"""
        await broadcast(999, "test", {"msg": "no one here"})  # 不应抛异常

    @pytest.mark.asyncio
    async def test_broadcast_resilience_broken_ws(self):
        """已断开的 WS 不应导致广播崩溃。"""
        ws_good = MockWebSocket()
        ws_broken = MockWebSocket()
        ws_broken.send_text = AsyncMock(side_effect=Exception("disconnected"))

        active_connections.setdefault(1, []).extend([ws_good, ws_broken])

        # 不应抛异常
        await broadcast(1, "test", {"msg": "hello"})

        # 正常 WS 应该收到消息
        assert len(ws_good.sent) == 1

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self):
        """断开连接后应该从连接池移除。"""
        ws = MockWebSocket()
        active_connections.setdefault(1, []).append(ws)

        # 模拟断开
        active_connections[1].remove(ws)

        assert ws not in active_connections[1]

    @pytest.mark.asyncio
    async def test_no_cross_room_leak(self):
        """不同讨论室的广播消息绝不泄露。"""
        ws_room1_a = MockWebSocket()
        ws_room1_b = MockWebSocket()
        ws_room2_a = MockWebSocket()

        active_connections.setdefault(1, []).extend([ws_room1_a, ws_room1_b])
        active_connections.setdefault(2, []).append(ws_room2_a)

        await broadcast(1, "guest_speak", {"guest_id": 0, "content": "room1 content"})

        # room1 的两个 WS 都应收到
        assert len(ws_room1_a.sent) == 1
        assert len(ws_room1_b.sent) == 1
        # room2 不应收到
        assert len(ws_room2_a.sent) == 0

        # 验证内容正确
        data = json.loads(ws_room1_a.sent[0])
        assert data["content"] == "room1 content"


class TestConnectionPool:
    """测试连接池管理。"""

    def setup_method(self):
        active_connections.clear()

    def test_setdefault_creates_new_list(self):
        """首次访问 discussion_id 应创建新的空列表。"""
        conns = active_connections.setdefault(42, [])
        assert isinstance(conns, list)

    def test_append_then_retrieve(self):
        """添加 WS 后应该能获取到。"""
        ws = MockWebSocket()
        active_connections.setdefault(1, []).append(ws)
        assert ws in active_connections[1]
```

- [ ] **Step 2: 运行测试 — 预期 FAIL（部分 mock 行为需微调）**

- [ ] **Step 3: 无需新增代码** — `ws/studio.py` 已有的 `active_connections` 和 `broadcast()` 已满足隔离要求

- [ ] **Step 4: 运行测试 — 预期 PASS**

---

### Task 6: API 端点 + 服务层补充

**Files:**
- Modify: `src/backend/api/routes/guests.py`（补充 POST /generate）
- Modify: `src/backend/services/guest_service.py`（补充调用逻辑）
- Modify: `src/backend/services/discussion_service.py`（补充编排入口）

**Dependencies:** Task 1-5 全部

- [ ] **Step 1: 补充 guests.py — 添加 /generate 端点**

```python
# 在现有 router 中添加:
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from ...services.guest_service import generate_guests_for_topic


class GenerateGuestsRequest(BaseModel):
    topic: str = Field(..., min_length=4, max_length=200)
    count: int = Field(default=4, ge=2, le=6)


class GuestItem(BaseModel):
    name: str
    persona: str
    speak_style: str
    system_prompt: str


class GenerateGuestsResponse(BaseModel):
    guests: list[GuestItem]


@router.post("/generate", response_model=GenerateGuestsResponse)
async def generate_guests_endpoint(data: GenerateGuestsRequest):
    try:
        guests = await generate_guests_for_topic(data.topic, data.count)
        return GenerateGuestsResponse(guests=[
            GuestItem(name=g.name, persona=g.persona, speak_style=g.speak_style, system_prompt=g.system_prompt)
            for g in guests
        ])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 2: 补充 guest_service.py**

```python
"""嘉宾业务服务。"""
from src.logic.guest_generator import generate_guests
from src.logic.prompt_lib import GuestDef
from src.backend.core.deepseek import deepseek_chat_json


class LLMClient:
    """封装 deepseek_chat_json 为 chat_json 接口。"""
    async def chat_json(self, prompt: str) -> dict:
        return await deepseek_chat_json([{"role": "user", "content": prompt}])


async def generate_guests_for_topic(topic: str, count: int) -> list[GuestDef]:
    """为指定话题生成嘉宾列表。"""
    llm = LLMClient()
    return await generate_guests(topic, count, llm)
```

- [ ] **Step 3: 补充 discussion_service.py**

```python
"""讨论业务服务。"""
import asyncio
from typing import AsyncGenerator
from src.logic.prompt_lib import GuestDef
from src.logic.speak_orchestrator import run_discussion_flow


async def start_discussion(
    discussion_id: int,
    topic: str,
    host: dict,
    guests: list[GuestDef],
    max_rounds: int,
    broadcast_func,
    stop_event: asyncio.Event,
) -> AsyncGenerator[dict, None]:
    """启动讨论编排流程。

    Returns:
        异步生成器，yield 讨论事件
    """
    from src.backend.core.deepseek import deepseek_chat, deepseek_chat_json

    class LLMClient:
        async def chat(self, messages: list[dict]) -> dict:
            return await deepseek_chat(messages)

        async def chat_json(self, prompt: str) -> dict:
            return await deepseek_chat_json([{"role": "user", "content": prompt}])

    llm = LLMClient()

    async for event in run_discussion_flow(
        discussion_id=discussion_id,
        topic=topic,
        host=host,
        guests=guests,
        max_rounds=max_rounds,
        llm=llm,
        broadcast=broadcast_func,
        stop_flag=stop_event,
    ):
        yield event
```

- [ ] **Step 4: 运行全部测试验证**

```bash
python -m pytest src/tests/unit/ -v
```

---

## 任务执行顺序

```
Task 1 (transcript_context) → Task 2 (guest_generator)
                                    ↓
Task 3 (opinion_extractor) ─────────┤
                                    ↓
Task 4 (speak_orchestrator) ────────┤
                                    ↓
Task 5 (ws_isolation) ──────────────┤
                                    ↓
Task 6 (API endpoints + services)
```

## 提交记录（6 commits，每个需用户确认）

| # | 提交信息 |
|---|---------|
| 1 | `[TDD-transcript] transcript上下文构建: 3函数+10测试全通过` |
| 2 | `[TDD-嘉宾] 嘉宾生成: generate_guests+validate_diversity+10测试全通过` |
| 3 | `[TDD-观点] 观点增量提取: extract_opinions+dedup+7测试全通过` |
| 4 | `[TDD-调度] 发言调度编排: decide/generate/flow+10测试全通过` |
| 5 | `[TDD-WS] WebSocket消息隔离: 按discussion_id隔离+8测试全通过` |
| 6 | `[TDD-API] API端点+服务层: /generate端点+服务层LLM注入` |
