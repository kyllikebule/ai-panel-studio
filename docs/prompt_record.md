# AI Panel Studio — Prompt 模板归档

本文档按四段式归档项目中所有 LLM Prompt 模板，包含完整 system/user 原文、期望输出格式和关键参数说明。

---

## 第 1 段：嘉宾生成 Prompt

**来源文件:** `src/backend/services/guest_generator.py` `generate_guests()`

### System Prompt

无独立 system prompt，通过 user prompt 一次性要求 LLM 输出 JSON。

### User Prompt 模板

```
讨论主题：{topic}
请生成 {count} 位立场差异化的 AI 专家嘉宾，每位嘉宾需有不同的persona和发言风格。
仅返回 JSON 数组，格式：
[{"name":"姓名","persona":"人设描述（至少10字符）","speak_style":"发言风格","system_prompt":"系统prompt"}]
要求：各位嘉宾的 persona 必须互不相同，代表不同立场和视角。
```

### 期望输出格式

```json
[
  {
    "name": "李教授",
    "persona": "AI伦理学专家，主张审慎监管",
    "speak_style": "学术严谨",
    "system_prompt": "你是AI伦理学专家..."
  }
]
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `topic` | 讨论主题（字符串） |
| `count` | 嘉宾数量（2-6） |
| temperature | 0.8（提高多样性） |
| max_tokens | 2048 |

### 后处理

- JSON 解析 + 格式校验（`validate_guest_diversity` 检查 persona 两两编辑距离 ≥ 10）
- 数量不足时抛出 `GuestGenerationError`

---

## 第 2 段：发言调度 Prompt

**来源文件:** `src/backend/services/speech_engine.py`

### 2a. 发言决策 `decide_next_speaker()`

#### User Prompt 模板

```
嘉宾列表：
{guest_list_text}     ← 格式: "[0] 李教授 — AI伦理学专家（学术严谨）"

讨论记录：
{transcript_text}     ← 格式: "[role] name: content"

{last_hint}           ← 可选: "上一发言人是 [1] 王博士，此轮不可选。"

请选择下一位最应该发言的嘉宾。规则：
1. 禁止连续选同一嘉宾
2. reason 必须是：举手（主动出击）/ 补充（扩展他人观点）/ 反驳（反对他人观点）
3. 无人需要发言时返回 {}
仅返回 JSON：{"guest_index": <int>, "reason": "<举手|补充|反驳>"} 或 {}
```

#### 期望输出格式

```json
{"guest_index": 2, "reason": "补充"}
```

#### 关键参数

| 参数 | 说明 |
|------|------|
| `transcript` | 最近 8 条消息 |
| `guests` | 嘉宾列表（GuestDef） |
| `last_speaker_index` | 上一发言人在 guests 中的索引 |
| temperature | 0.5 |
| max_tokens | 128 |

#### 后处理（硬规则拦截）

- 禁止连续同一嘉宾（即使 LLM 返回相同 index）
- guest_index 越界 → 返回 None
- reason 不在 `('举手', '补充', '反驳')` → 默认 `'补充'`
- JSON 解析失败 → 返回 None

---

### 2b. 发言内容生成 `generate_speech()`

#### User Prompt 模板

```
你是{guest.name}，{guest.persona}。发言风格：{guest.speak_style}。
讨论主题：{topic}
本轮发言原因：{speak_reason}
最近记录：
{transcript_text}

请以{guest.name}的身份发言，仅输出发言内容（1-2句话，≤200字）。
不要带角色名前缀或引号。
```

#### 期望输出格式

纯文本：`我认为AI监管非常必要。它保护了公众利益。`

#### 关键参数

| 参数 | 说明 |
|------|------|
| `guest` | 嘉宾定义（GuestDef） |
| `speak_reason` | 举手 / 补充 / 反驳 |
| temperature | 0.7 |
| max_tokens | 256 |

#### 后处理

- 超过 200 字 → 截断至 200 字
- LLM 调用失败 → 返回 `（{name}暂时无法发言）`

---

## 第 3 段：观点提炼 Prompt

**来源文件:** `src/backend/services/opinion_extractor.py` `extract_opinion()`

### User Prompt 模板

```
讨论主题：{topic}
发言内容：{message_content}

请分析该发言是否包含明确观点。如果有，提取：
stance_summary（一句话核心观点）
category（consensus 表示与其他发言人一致，disagreement 表示对立，neutral 表示中立或无明确立场）
confidence（置信度 0.0-1.0）
evidence（原文中支撑该观点的关键句，可为 null）

仅返回 JSON：{"stance_summary":"...","category":"...","confidence":0.0,"evidence":"..."}
如果没有明确观点，返回：{}
```

### 期望输出格式

```json
{
  "stance_summary": "各方均认同需要监管AI风险",
  "category": "consensus",
  "confidence": 0.92,
  "evidence": "严格监管是必要的"
}
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `message_content` | 单条发言内容 |
| `topic` | 讨论主题 |
| temperature | 0.3（低温度确保分类一致性） |
| max_tokens | 512 |

### 后处理

- category 不在 `('consensus', 'disagreement', 'neutral')` → 默认 `'neutral'`
- confidence 强制钳位至 `[0.0, 1.0]`
- 空对象 `{}` → 返回 `None`

---

## 第 4 段：主持人总结 Prompt

**来源文件:** `src/backend/services/speech_engine.py` `generate_host_summary()`

### User Prompt 模板

```
你是讨论主持人。请基于以下内容，用标准中文总结整场讨论（≤500字）。

讨论主题：{topic}

完整发言记录：
{transcript_text}

已提炼观点：
{opinions_text}

请按以下四段式输出：
1. 各方核心观点（简要概括每位嘉宾的核心主张）
2. 达成的共识（列出各方一致同意的点）
3. 仍存的分歧（列出各方观点不同的点）
4. 总结语（一句话总结整场讨论）

要求：用自然段落书写，不要用 Markdown 编号列表。
```

### 期望输出格式

纯文本四段式：

```
本场讨论围绕...各方核心观点如下：

1. 核心观点：李教授强调...；王博士认为...；张律师提出...

2. 共识：所有嘉宾一致认同...且...是可行方向。

3. 分歧：在...上存在根本分歧，各方对...的判断不同。

4. 总结：...是一个需要...的复杂议题，建议...构建...体系。
```

### 关键参数

| 参数 | 说明 |
|------|------|
| `transcript` | 完整消息列表（最多取最后 20 条） |
| `opinions` | 已提炼观点列表（OpinionResult） |
| `topic` | 讨论主题 |
| temperature | 0.5 |
| max_tokens | 1024 |

### 后处理

- 超过 500 字 → 截断至 500 字
- LLM 调用失败 → 返回错误描述
