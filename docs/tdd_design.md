# TDD 阶段设计文档：核心 AI 业务逻辑 + pytest 单元测试

**日期:** 2026-06-28
**阶段:** TDD（Test-Driven Development）
**状态:** 已确认

---

## 约束

- 先写测试用例，再实现代码
- 测试文件路径：`src/tests/unit/`
- API Key 禁止以任何形式传到前端/浏览器/日志/返回值
- 所有 LLM 调用通过 `core/deepseek.py`，测试中全部 mock
- 产出路径：`src/backend/services/`（实现）、`src/tests/unit/`（测试）

---

## 架构总览

```
src/backend/services/                    src/tests/unit/
├── guest_generator.py     ──对应──     test_guest_generator.py
│   ├── generate_guests(topic, count) → list[GuestDef]
│   └── validate_guest_diversity(guests) → bool
│
├── speech_engine.py       ──对应──     test_speech_engine.py
│   ├── decide_next_speaker(transcript, guests, last_speaker_id) → (guest_id, reason) | None
│   ├── generate_speech(guest, transcript, reason, topic) → str
│   └── run_discussion_round(discussion_id) → list[dict]
│
├── opinion_extractor.py   ──对应──     test_opinion_extractor.py
│   ├── extract_opinion(message_content, topic) → OpinionResult | None
│   └── merge_opinions(existing, new) → list[OpinionResult]
│
└── orchestrator.py        ──测试内联── (集成在 speech_engine 和 ws 测试中)
    ├── start_discussion(discussion_id)
    └── run_full_flow(discussion_id)

src/tests/unit/
└── test_ws_isolation.py   ──对应──     api/ws/studio.py
    ├── test_broadcast_isolation()
    └── test_connection_pool_separation()
```

### TDD 执行顺序（按依赖链）

1. `guest_generator` — 无依赖
2. `opinion_extractor` — 依赖 message content 字符串，无外部模块依赖
3. `speech_engine` — 依赖 guest_generator + opinion_extractor 函数签名
4. `ws_isolation` — 独立于上述 3 模块
5. orchestrator 集成 — 依赖 1-3 全部模块

---

## 模块 1: guest_generator（嘉宾生成）

### 接口

```python
async def generate_guests(topic: str, count: int) -> list[GuestDef]:
    """调用 LLM 生成 count 位差异化嘉宾，返回标准化列表。"""

def validate_guest_diversity(guests: list[GuestDef]) -> bool:
    """校验嘉宾立场差异化：persona 字段两两编辑距离 ≥ 10 字符。"""
```

### GuestDef（复用 src/logic/prompt_lib.py）

```python
@dataclass
class GuestDef:
    name: str
    persona: str
    system_prompt: str
    speak_style: str = ""
    avatar: str = ""
```

### 测试用例（`src/tests/unit/test_guest_generator.py`）

| # | 测试 | 类型 | 预期 |
|---|------|------|------|
| 1 | `generate_guests("AI监管", 4)` 返回 4 个嘉宾 | 数量合规 | `len == 4` |
| 2 | 每个嘉宾 `name` 非空、`persona` ≥ 10 字符 | 格式校验 | 全部通过 |
| 3 | 4 个嘉宾的 persona 两两不相同（编辑距离检查） | 立场差异化 | `validate_guest_diversity` 返回 True |
| 4 | `generate_guests` 中 LLM 调用失败 → 抛出异常 | 错误处理 | `GuestGenerationError` |
| 5 | `validate_guest_diversity` 对相同 persona 返回 False | 边界 | `False` |

### 错误处理

```python
class GuestGenerationError(Exception):
    """嘉宾生成失败时抛出，含原因描述。"""
```

---

## 模块 2: speech_engine（发言调度）

### 接口

```python
async def decide_next_speaker(
    transcript: list[dict], guests: list[GuestDef], last_speaker_id: int | None
) -> tuple[int, str] | None:
    """返回 (guest_index, reason: '举手'|'补充'|'反驳')，无人需要发言返回 None。
    规则：禁止连续同一嘉宾、禁止轮值（不以固定顺序循环）。"""

async def generate_speech(
    guest: GuestDef, transcript: list[dict], speak_reason: str, topic: str
) -> str:
    """生成 1-2 句发言内容，≤ 200 字。"""

async def run_discussion_round(discussion_id: int) -> list[dict]:
    """编排单轮：decide → generate → 存入 DB → 返回消息。"""
```

### 测试用例（`src/tests/unit/test_speech_engine.py`）

| # | 测试 | 类型 | 预期 |
|---|------|------|------|
| 1 | `decide_next_speaker` 禁止连续同嘉宾 | 禁止轮值抢答 | 下一位 != 上一发言人 |
| 2 | 所有嘉宾都已发言 1 次后不应返回 None | 发言充足 | 非 None |
| 3 | `generate_speech` 返回 1-2 句 | 短句发言 | ≤ 2 句 |
| 4 | `generate_speech` 返回内容 ≤ 200 字 | 短句发言 | `len ≤ 200` |
| 5 | `decide_next_speaker` 返回 reason 合法 | 格式校验 | 属于 `('举手','补充','反驳')` |
| 6 | transcript 为空时 `decide_next_speaker` 返回 None | 边界 | None |

---

## 模块 3: opinion_extractor（共识增量提取）

### 接口

```python
@dataclass
class OpinionResult:
    stance_summary: str
    category: str  # 'consensus' | 'disagreement' | 'neutral'
    confidence: float
    evidence: str | None

async def extract_opinion(message_content: str, topic: str) -> OpinionResult | None:
    """从单条消息提取观点，无明确观点返回 None。"""

def merge_opinions(
    existing: list[OpinionResult], new: OpinionResult
) -> list[OpinionResult]:
    """增量合并：相同 stance_summary 更新置信度（取 max），不同则追加。"""
```

### 测试用例（`src/tests/unit/test_opinion_extractor.py`）

| # | 测试 | 类型 | 预期 |
|---|------|------|------|
| 1 | 共识型发言 → `category == 'consensus'` | 分类正确 | `consensus` |
| 2 | 对立型发言 → `category == 'disagreement'` | 分类正确 | `disagreement` |
| 3 | `confidence` 在 0.0-1.0 之间 | 格式校验 | `0 ≤ c ≤ 1` |
| 4 | `merge_opinions` 追加不重复观点 | 增量合并 | `len` 增加 1 |
| 5 | `merge_opinions` 相同摘要更新置信度 | 去重合并 | `len` 不变，confidence 取 max |
| 6 | 无明确观点发言 → `extract_opinion` 返回 None | 边界 | `None` |

---

## 模块 4: WebSocket 消息隔离

### 测试接口（操作 `api/ws/studio.py` 的 `active_connections` 和 `broadcast()`）

### 测试用例（`src/tests/unit/test_ws_isolation.py`）

| # | 测试 | 类型 | 预期 |
|---|------|------|------|
| 1 | 2 个 discussion_id 各自连接 → 消息隔离不泄露 | 纯函数隔离 | discussion_1 broadcast 仅到达自己 |
| 2 | broadcast 到空房间不抛异常 | 边界 | 无异常 |
| 3 | 客户端断开后连接池清理 | 连接管理 | 列表移除此 ws |
| 4 | 2 个 discussion 并发 broadcast | 并发安全 | 各自收到正确消息，无串扰 |

---

## Mock 策略

| 模块 | Mock 对象 | 方式 |
|------|----------|------|
| guest_generator | LLM API 调用 | `unittest.mock.patch` 替换 `deepseek_chat` |
| speech_engine | LLM API 调用 | 同上 |
| opinion_extractor | LLM API 调用 | 同上 |
| ws_isolation | WebSocket 连接 | `asyncio` + 模拟 send/recv |

---

## 产出物清单

| # | 产出物 | 路径 |
|---|--------|------|
| 1 | 嘉宾生成服务 | `src/backend/services/guest_generator.py` |
| 2 | 发言调度引擎 | `src/backend/services/speech_engine.py` |
| 3 | 共识提取器 | `src/backend/services/opinion_extractor.py` |
| 4 | 讨论编排器 | `src/backend/services/orchestrator.py` |
| 5 | 嘉宾生成测试 | `src/tests/unit/test_guest_generator.py` |
| 6 | 发言调度测试 | `src/tests/unit/test_speech_engine.py` |
| 7 | 共识提取测试 | `src/tests/unit/test_opinion_extractor.py` |
| 8 | WS 隔离测试 | `src/tests/unit/test_ws_isolation.py` |

**总计：8 个文件（4 实现 + 4 测试）**
