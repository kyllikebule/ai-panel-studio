# AI Panel Studio — 虚拟专家圆桌辩论演播厅

AI 驱动的专家讨论直播平台。用户输入议题，生成多位 AI 嘉宾进行圆桌辩论，实时展示发言记录和观点提炼。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy / SQLite |
| 前端 | Vue 3 / Element Plus / Pinia / Vue Router / Vite |
| AI | DeepSeek API（支持 OpenAI / Anthropic 切换） |
| 测试 | pytest + pytest-asyncio |

## 快速启动

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

必填变量：
- `LLM_PROVIDER` — LLM 后端（deepseek / openai / anthropic）
- `DEEPSEEK_API_KEY` — DeepSeek API 密钥
- `DEEPSEEK_BASE_URL` — API 基础地址
- `DATABASE_URL` — SQLite 数据库路径

### 3. 启动后端

```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 安装前端依赖（需要 Node.js ≥ 18）

```bash
cd src/frontend
npm install
```

### 5. 启动前端

```bash
cd src/frontend
npm run dev
```

访问 `http://localhost:3000`

### 6. 运行测试

```bash
pytest src/tests/unit/ -v
```

## 项目结构

```
ai-panel-studio/
├── docs/                          # 设计与开发文档
│   ├── er_model.md               # ER 数据模型
│   ├── api_contract.md           # REST + WebSocket API 契约
│   ├── ui_design_spec.md         # UI 设计规范（UI UX Pro Max 生成）
│   ├── dev_explain.md            # 开发过程说明
│   ├── prompt_record.md          # Prompt 模板归档
│   ├── ddd_design.md             # DDD 阶段设计
│   ├── ddd_plan.md               # DDD 阶段执行计划
│   ├── tdd_design.md             # TDD 阶段设计
│   └── e2e_design.md             # E2E 阶段设计
├── schema/
│   └── init_sqlite.sql           # SQLite 建表脚本
├── sample_data/                  # 测试议题样例
│   ├── topic_1_ai_regulation.json
│   ├── topic_2_quantum_crypto.json
│   ├── topic_3_web3_governance.json
│   ├── topic_4_agi_safety.json
│   └── topic_5_climate_ai.json
├── src/
│   ├── backend/                  # FastAPI 后端
│   │   ├── main.py              # 应用入口
│   │   ├── core/                # 配置 + DeepSeek SDK
│   │   ├── db/                  # SQLAlchemy 模型 + 会话
│   │   ├── api/routes/          # REST 路由
│   │   ├── api/ws/              # WebSocket
│   │   └── services/            # AI 业务逻辑
│   ├── frontend/                 # Vue 3 前端
│   │   └── src/
│   │       ├── views/           # 页面（Home / CreateDiscuss / Studio）
│   │       ├── components/      # 组件（DiscussCard / GuestCard / ChatMessage / OpinionItem）
│   │       ├── stores/          # Pinia 状态管理
│   │       ├── router/          # 路由配置
│   │       └── styles/          # 设计令牌 CSS 变量
│   ├── logic/                    # Prompt 模板库 + JSON 校验
│   └── tests/unit/               # pytest 单元测试
├── requirements.txt
├── .env.example
└── pytest.ini
```

## 开发阶段

项目按 SDD → DDD → TDD → E2E 四阶段开发：

| 阶段 | 内容 | 输出 |
|------|------|------|
| **SDD** | 数据建模 + ER 图 + SQL + API 契约 + Prompt 模板 | docs/ schema/ src/logic/ |
| **DDD** | 后端脚手架 + UI 设计规范 + 3 个前端页面 | src/backend/ src/frontend/ |
| **TDD** | AI 业务逻辑 + 25 个 pytest 单元测试 | src/backend/services/ src/tests/unit/ |
| **E2E** | 联调 + UI 优化 + 交付文档 | 全项 |

## 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Home | 讨论列表首页 |
| `/create-discuss` | CreateDiscuss | 创建圆桌讨论：议题输入 + 嘉宾选择 |
| `/studio/:discId` | Studio | 演播厅核心页：Transcript + 嘉宾状态 + 共识/分歧 + 主持人总结 |

## License

MIT
