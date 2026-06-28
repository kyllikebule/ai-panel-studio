# TDD 阶段设计文档：核心 AI 业务逻辑 + pytest 单元测试

**日期:** 2026-06-28
**阶段:** TDD（Test-Driven Development）
**状态:** 已确认

---

## 硬性约束

1. 先写测试用例，再实现代码
2. 测试文件路径：`src/tests/unit/`
3. API Key 永不离开后端，禁止传给前端
4. 测试中所有 LLM 调用使用 mock，不实际请求外部 API

---

## 1. 模块架构

### 1.1 产出物总览

```
src/
├── logic/                          # SDD 已有
│   ├── prompt_lib.py               # 已有 — Prompt 模板
│   ├── guest_generator.py          # 新增 — 嘉宾生成
│   ├── speak_orchestrator.py       # 新增 — 发言调度编排
│   ├── opinion_extractor.py        # 新增 — 共识增量提取
│   └── transcript_context.py       # 新增 — transcript 上下文构建

src/backend/
├── api/routes/
│   └── guests.py                   # 补充 — 含 POST /api/guests/generate 端点
├── api/ws/
│   └── studio.py                   # 补充 — 含 AI 编排+消息隔离
└── services/
    ├── guest_service.py            # 补充 — 调用 guest_generator
    └── discussion_service.py       # 补充 — 调用 speak_orchestrator

src/tests/unit/                     # 新增
├── test_guest_generator.py
├── test_speak_orchestrator.py
├── test_opinion_extractor.py
└── test_ws_isolation.py
```

### 1.2 依赖链

```
guest_generator.py ─── 依赖 ──→ prompt_lib.py + deepseek.py (mock)
                                      ↓
speak_orchestrator.py ─── 依赖 ──→ guest_generator + prompt_lib + transcript_context
                                      ↓
opinion_extractor.py ─── 依赖 ──→ transcript_context
                                      ↓
ws/studio.py ─── 依赖 ──→ speak_orchestrator + opinion_extractor
```

### 1.3 4 个新模块接口

| 模块 | 核心函数 | 输入 | 输出 |
|------|---------|------|------|
| `guest_generator.py` | `generate_guests(topic, count, llm)` | 议题 + 人数 + LLM 客户端 | `list[GuestDef]`（立场差异化） |
| `speak_orchestrator.py` | `decide_next_speaker(transcript, guests)` | 历史发言 + 嘉宾列表 | `{guest_id, reason, trigger_msg_id}` |
| `speak_orchestrator.py` | `run_discussion_flow(disc_id, db, llm, ws_broadcast)` | 讨论ID + DB会话 + LLM + WS回调 | 异步生成器，yield 事件 |
| `opinion_extractor.py` | `extract_opinions(recent_messages, existing_opinions)` | 最近消息 + 已有观点 | `list[Opinion]`（增量，去重） |
| `transcript_context.py` | `build_transcript_context(messages, max_recent)` | 消息列表 + 最大条数 | 格式化的 context 字符串 |

---

## 2. 嘉宾生成接口（guest_generator.py）

### 2.1 测试用例设计

| # | 测试 | 输入 | 预期 |
|---|------|------|------|
| 1 | `test_count_compliance` | topic="AI监管", count=3 | 返回 3 位嘉宾 |
| 2 | `test_count_compliance_2` | topic="AI监管", count=5 | 返回 5 位嘉宾 |
| 3 | `test_min_count` | count=1 | 至少生成 2 位（raise ValueError） |
| 4 | `test_max_count` | count=7 | 最多生成 6 位（raise ValueError） |
| 5 | `test_stance_diversity` | topic="AI监管", count=4 | 4 位嘉宾立场不全相同（至少 2 种立场） |
| 6 | `test_format_compliance` | topic="AI监管", count=3 | 每位嘉宾含 name/persona/speak_style/system_prompt 四个键 |
| 7 | `test_name_uniqueness` | topic="AI监管", count=4 | 4 个嘉宾 name 互不相同 |
| 8 | `test_field_non_empty` | topic="AI监管", count=3 | 每位嘉宾所有字段非空字符串 |
| 9 | `test_topic_in_persona` | topic="AI监管" | 至少 1 位嘉宾 persona 含"监管"关键字 |
| 10 | `test_llm_error_graceful` | LLM 返回非 JSON / 超时 | 返回预设 fallback 嘉宾列表 |

### 2.2 实现接口

```python
# src/logic/guest_generator.py
async def generate_guests(
    topic: str,
    count: int,
    llm_client: Any,  # 注入的 LLM 客户端（测试时 mock）
) -> list[GuestDef]:
    """
    调用 LLM 生成 count 位立场差异化的嘉宾。
    
    约束：
    - 2 <= count <= 6，否则 ValueError
    - 每位嘉宾 name 唯一
    - 立场至少 2 种不同
    - LLM 异常时返回 fallback 列表
    """
```

### 2.3 API 端点

```
POST /api/guests/generate
Request:  {"topic": "AI监管", "count": 4}
Response: {"guests": [{name, persona, speak_style, system_prompt}, ...]}
```

---

## 3. 发言调度 AI 逻辑（speak_orchestrator.py）

### 3.1 测试用例设计

| # | 测试 | 输入 | 预期 |
|---|------|------|------|
| 1 | `test_no_consecutive_same_speaker` | 上一条发言人=嘉宾A | 下一位 ≠ 嘉宾A |
| 2 | `test_host_first` | transcript=空 | 第一条发言来自 host |
| 3 | `test_host_not_in_decide_loop` | transcript 含多条 | `decide_next_speaker` 不返回 host |
| 4 | `test_short_response_1_2_sentences` | 生成发言内容 | 内容为 1-2 句（不超过 3 个句号） |
| 5 | `test_no_think_summary_in_content` | 生成发言内容 | content 不含"思考"/"认为应该"等元描述 |
| 6 | `test_flow_yields_all_events` | 模拟完整 2 轮讨论 | yield 事件含 host_speak×2 + guest_speak×N + opinion_extracted + round_change |
| 7 | `test_flow_ends_after_max_rounds` | max_rounds=2 | 2 轮后 yield discussion_end |
| 8 | `test_flow_can_be_stopped` | 外部设置 stop_flag | 运行中的 flow 在下一轮检查时退出 |
| 9 | `test_guest_speak_decision_reason` | transcript 含反驳 | 下一位发言者 reason 含"反驳" |
| 10 | `test_empty_transcript_returns_host` | transcript=[] | decide_next_speaker → host |

### 3.2 实现接口

```python
# src/logic/speak_orchestrator.py
async def decide_next_speaker(
    transcript: list[dict],
    guests: list[GuestDef],
) -> dict:
    """
    根据当前 transcript 决定下一位发言者。
    
    规则：
    - 禁止连续同一位嘉宾发言
    - 禁止按索引轮值（必须由上下文驱动）
    - 主持人不在 decide 循环中
    - 返回 {"guest_id": int, "reason": str, "trigger_msg_id": int|None}
    """

async def generate_speak_content(
    guest: GuestDef,
    transcript: list[dict],
    speak_reason: str,
    topic: str,
    llm: Any,
) -> str:
    """
    生成嘉宾发言内容，1-2 句话，不含元描述。
    """

async def run_discussion_flow(
    discussion_id: int,
    max_rounds: int,
    topic: str,
    host: dict,
    guests: list[GuestDef],
    llm: Any,
    broadcast: Callable,
    stop_flag: asyncio.Event,
) -> AsyncGenerator[dict, None]:
    """
    完整讨论编排异步生成器：
    
    1. 主持人开场 → yield host_open
    2. 每轮：decide_next_speaker → generate_speak_content → yield guest_speak
    3. 每轮结束：extract_opinions → yield opinion_extracted
    4. N 轮后：主持人总结 → yield host_summary
    5. yield discussion_end
    
    支持 stop_flag 中断。
    """
```

---

## 4. 共识增量提取（opinion_extractor.py）

### 4.1 测试用例设计

| # | 测试 | 输入 | 预期 |
|---|------|------|------|
| 1 | `test_no_duplicate_stance_summary` | 同一观点 2 次出现 | 仅提取 1 次 |
| 2 | `test_category_mapping` | 含共识/分歧/中立 | 返回正确 category |
| 3 | `test_empty_messages_returns_empty` | messages=[] | 返回 [] |
| 4 | `test_new_opinion_vs_existing` | existing有1条，新消息含1新观点 | 仅返回 1 条新观点 |
| 5 | `test_confidence_range` | 正常消息 | 0.0 <= confidence <= 1.0 |
| 6 | `test_evidence_not_empty` | 正常消息 | evidence 字段非空 |

### 4.2 实现接口

```python
# src/logic/opinion_extractor.py
async def extract_opinions(
    recent_messages: list[dict],
    existing_opinions: list[dict],
    llm: Any,
) -> list[dict]:
    """
    增量提取观点：
    - 对 recent_messages 中尚未提取观点的消息进行分析
    - 与 existing_opinions 去重（stance_summary 语义相似度 > 0.8 视为重复）
    - 返回新增观点列表
    """
```

---

## 5. WebSocket 消息隔离（ws/studio.py）

### 5.1 测试用例设计

| # | 测试 | 输入 | 预期 |
|---|------|------|------|
| 1 | `test_broadcast_same_room_only` | disc-1 有 WS-A，disc-2 有 WS-B | broadcast(disc-1) 仅 WS-A 收到 |
| 2 | `test_multiple_clients_same_room` | disc-1 有 WS-A 和 WS-B | broadcast(disc-1) → 两人都收到 |
| 3 | `test_disconnect_cleanup` | WS-A 断开 | disc-1 的 active_connections 不含 WS-A |
| 4 | `test_broadcast_resilience` | 1 个 WS 已断但未清理 | broadcast 不抛异常，跳过断开连接 |
| 5 | `test_no_cross_room_leak` | disc-1 和 disc-2 各有消息 | disc-1 的消息不出现在 disc-2 的队列中 |
| 6 | `test_connect_then_isolate` | 集成测试：2 个 TestClient WebSocket | 并发 2 房间，验证消息不交叉 |

---

## 6. API Key 安全约束

```
前端 → POST /api/guests/generate → 后端 services/ → core/deepseek.py
                                                         ↓
                                                   读取 .env Key
                                                         ↓
                                                   DeepSeek API
                                                         ↓
                                    返回 GuestDef[]（不含任何 Key 信息）
```

- `.env` 中的 `DEEPSEEK_API_KEY` 仅由 `core/config.py` 读取
- `settings.deepseek_api_key` 仅传入 `deepseek.py` 的 `get_deepseek_client()` 工厂函数
- 业务函数通过注入的 `llm_client` 参数调用，不直接访问 settings
- 所有响应 Pydantic Schema 不含 key 字段
- 前端永不接触 API Key

---

## 7. 产出物清单

| # | 产出物 | 路径 | 操作 |
|---|--------|------|------|
| 1 | 嘉宾生成逻辑 | `src/logic/guest_generator.py` | 新增 |
| 2 | 发言调度编排 | `src/logic/speak_orchestrator.py` | 新增 |
| 3 | 观点增量提取 | `src/logic/opinion_extractor.py` | 新增 |
| 4 | transcript 上下文构建 | `src/logic/transcript_context.py` | 新增 |
| 5 | 嘉宾生成端点 | `src/backend/api/routes/guests.py` | 补充 |
| 6 | WS AI 编排 + 隔离 | `src/backend/api/ws/studio.py` | 补充 |
| 7 | 嘉宾服务层 | `src/backend/services/guest_service.py` | 补充 |
| 8 | 讨论服务层 | `src/backend/services/discussion_service.py` | 补充 |
| 9 | 嘉宾生成测试 | `src/tests/unit/test_guest_generator.py` | 新增 |
| 10 | 发言调度测试 | `src/tests/unit/test_speak_orchestrator.py` | 新增 |
| 11 | 观点提取测试 | `src/tests/unit/test_opinion_extractor.py` | 新增 |
| 12 | WS 隔离测试 | `src/tests/unit/test_ws_isolation.py` | 新增 |
