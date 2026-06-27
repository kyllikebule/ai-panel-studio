# E2E 交付阶段设计文档

**日期:** 2026-06-28
**阶段:** E2E（End-to-End Delivery）
**状态:** 已确认

---

## 执行分层（方案 B）

| 轮次 | 类型 | 任务 |
|------|------|------|
| 第 1 轮 | 代码层 | WS 联调 + 主持人总结 + UI 优化 |
| 第 2 轮 | 文档层 | README + prompt_record + dev_explain + sample_data |
| 第 3 轮 | 质量层 | 全项自检 + 修复不合规点 |

---

## 第 1 轮：代码层

### 1.1 WebSocket 联调（`api/ws/studio.py`）

**当前状态:** `studio.py` 仅回显 action，无 AI 逻辑
**改造后:** WS 收到 `start` → 调用 orchestrator → 逐步骤推送事件

**事件流:**
```
客户端 action: "start"
  → host_opening()          → push host_speak
  → decide_next_speaker()   → push guest_speak + token_stream
  → generate_speech()       → push speak_done
  → extract_opinion()       → push opinion_extracted
  → generate_host_summary() → push discussion_end {summary, opinions[]}
```

**前端 Studio.vue 验证:**
- `host_speak` → 消息列表新增
- `guest_speak` → 消息列表新增 + GuestCard 发言动画
- `opinion_extracted` → OpinionPanel 追加
- `discussion_end` → 底部总结区显示

### 1.2 主持人自然语言总结

**接口（`services/speech_engine.py` 新增）:**
```python
async def generate_host_summary(
    transcript: list[dict], opinions: list[OpinionResult], topic: str
) -> str:
    """四段式标准中文总结：核心观点 → 共识 → 分歧 → 总结语，≤ 500 字。"""
```

**测试用例:** 1 个（mock LLM 返回，验证 ≤ 500 字 + 四段标签存在）

### 1.3 UI 优化（调用 UI UX Pro Max）

**全局:**
- 检查 Vue 文件确保 CSS 引用 `var(--xxx)` 非硬编码色值
- Element Plus 深色覆盖补全：`el-dialog` / `el-slider` / `el-select-dropdown`

**演播厅专项:**
- 四分区面板间距对齐 8px 基准
- 分割线统一 `--color-divider-glow`
- 消息入场动画 `fade-slide-up` 实际生效
- 空态 `el-empty` 统一暗色描述文字
- 滚动条宽度统一 5px

---

## 第 2 轮：文档层

### 2.1 sample_data（5 套测试议题）

```
sample_data/
├── topic_1_ai_regulation.json
├── topic_2_quantum_crypto.json
├── topic_3_web3_governance.json
├── topic_4_agi_safety.json
└── topic_5_climate_ai.json
```

| # | 议题 | 嘉宾视角 |
|---|------|---------|
| 1 | AI 是否应该被严格监管？ | 伦理学/技术乐观/法律合规/产业政策 |
| 2 | 量子计算对密码学的冲击 | 密码学家/量子物理学家/网络安全/金融科技 |
| 3 | Web3 与去中心化治理的未来 | 区块链开发者/经济学家/监管机构/社会学家 |
| 4 | AGI 安全对齐问题 | AI安全研究员/哲学家/工程师/政策制定者 |
| 5 | AI 在气候变化中的角色 | 气候学家/能源专家/AI应用/环保NGO |

### 2.2 README.md

6 章：项目简介 / 技术栈 / 快速启动 / 项目结构 / 开发阶段 / 环境变量

### 2.3 docs/prompt_record.md

四段式 Prompt 归档：

| 段 | 名称 | 内容 |
|----|------|------|
| 第1段 | 嘉宾生成 Prompt | 主题 → 差异化嘉宾 JSON 输出 |
| 第2段 | 发言调度 Prompt | decide_next_speaker + generate_speech |
| 第3段 | 观点提炼 Prompt | extract_opinion 分类 |
| 第4段 | 主持人总结 Prompt | generate_host_summary 四段式 |

### 2.4 docs/dev_explain.md

核心：DDD 阶段使用 UI UX Pro Max 设计页面的完整过程（设计系统生成 → Token 提取 → 页面设计 → 组件开发 → 响应式适配）

---

## 第 3 轮：质量层

### 全项自检清单

| # | 检查项 | 标准 |
|---|--------|------|
| 1 | 24 个 pytest 全部通过 | `pytest src/tests/unit/ -v` |
| 2 | 后端文件导入无错误 | `python -c "from src.backend.main import app"` |
| 3 | `.env.example` 包含全部必要变量 | LLM_PROVIDER / DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DATABASE_URL |
| 4 | API Key 零泄露 | 搜索前端代码无 `DEEPSEEK_API_KEY` / `sk-` |
| 5 | 前端硬编码色值检查 | 搜索 `#` 在 Vue scoped style 中，确保引用 `var(--xxx)` |
| 6 | `.gitignore` 排除 `__pycache__`/`.env`/`node_modules`/`data/` | 存在且生效 |
| 7 | 所有文档非空 | `docs/*.md` 不为空白 |
| 8 | 提交格式一致性 | 全部 `[阶段-任务] 描述` 格式 |

---

## 产出物清单

| # | 产出物 | 路径 |
|---|--------|------|
| 1 | WS 联调改造 | `api/ws/studio.py` + `Studio.vue` |
| 2 | 主持人总结函数 | `services/speech_engine.py` |
| 3 | 主持人总结测试 | `tests/unit/test_speech_engine.py` |
| 4 | 5 套议题样例 | `sample_data/topic_*.json` |
| 5 | 部署文档 | `README.md` |
| 6 | Prompt 归档 | `docs/prompt_record.md` |
| 7 | 开发说明 | `docs/dev_explain.md` |
| 8 | UI 优化 | 多个 `.vue` + `variables.css` |

**共计：~12 个文件（修改 + 新建）**
