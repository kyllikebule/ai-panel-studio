# DDD 阶段设计文档：后端脚手架 + 演播厅风格 UI 页面

**日期:** 2026-06-27
**阶段:** DDD（Design-Driven Development）
**状态:** 已确认

---

## 硬性约束

1. 后端部分：仅搭建分层骨架，不写 AI 业务逻辑
2. 前端页面：所有页面必须调用 UI UX Pro Max 技能，先生成演播厅专属设计系统，再编写 Vue 代码
3. 页面清单：首页讨论列表页、嘉宾配置页、演播厅主页面；演播厅必须四分区独立滚动，直播演播厅视觉风格

---

## 1. 后端 FastAPI 分层骨架

### 1.1 目录结构

```
src/backend/
├── main.py                       # FastAPI 入口，挂载路由，CORS，WS 端点注册
├── core/
│   ├── __init__.py
│   ├── config.py                 # Settings (pydantic-settings): DB路径、DeepSeek API Key、LLM_PROVIDER
│   └── deepseek.py               # DeepSeek 全功能 SDK：同步/流式/重试/速率限制/多模型
├── db/
│   ├── __init__.py
│   ├── database.py               # SQLite 引擎 + 会话工厂，init_db() 执行 init_sqlite.sql
│   └── models.py                 # SQLAlchemy ORM 模型：Host/Discussion/Guest/DiscussionGuest/Message/Opinion
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── discussions.py        # 讨论 CRUD + 讨论内嘉宾管理
│   │   └── guests.py             # 嘉宾模板 CRUD
│   └── ws/
│       ├── __init__.py
│       └── studio.py             # WebSocket /ws/discussion/{id}
└── services/                     # 业务服务层（DDD阶段仅建空桩，不写AI逻辑）
    ├── __init__.py
    ├── discussion_service.py     # 讨论创建/状态管理等
    └── guest_service.py          # 嘉宾模板管理
```

共 **16 个文件**。

### 1.2 各文件职责

| 文件 | DDD 阶段产出 | 后期补 |
|------|-------------|--------|
| `main.py` | FastAPI app, CORS, include routers, WS mount | — |
| `core/config.py` | Settings 类，读 .env | — |
| `core/deepseek.py` | 完整 DeepSeek SDK（同步/流式/重试/限速） | — |
| `db/database.py` | 引擎 + 会话 + init_db() | — |
| `db/models.py` | 6 个 ORM 模型 | — |
| `api/routes/*.py` | CRUD 路由（含请求/响应模型） | — |
| `api/ws/studio.py` | WS 连接管理，消息分发框架 | AI 编排逻辑 |
| `services/*.py` | 空桩函数声明 | AI 业务逻辑 |

### 1.3 DeepSeek SDK（`core/deepseek.py`）

全功能封装：
- 同步调用（chat/chat_json）
- 流式输出（SSE generator）
- 自动重试（exponential backoff）
- 速率限制（token bucket）
- 多模型切换（deepseek-chat / deepseek-reasoner）
- 环境变量读取 API Key

---

## 2. UI 设计规范 `docs/ui_design_spec.md`

DDD 阶段要求：先调用 UI UX Pro Max 生成设计系统，再写 Vue 代码。

### 2.1 设计系统 5 模块

| 模块 | 内容 | 用途 |
|------|------|------|
| **配色方案** | 科技风直播间主题：深色底 + 霓虹强调色，主色/辅色/中性色各定义 3-4 个梯度 | CSS 变量全局注入 |
| **角色色卡** | 主持人（金色系）、嘉宾 A/B/C/D（蓝/绿/紫/橙系），带发言状态色 | GuestCard 组件色相绑定 |
| **卡片组件样式** | 圆角、发光边框、半透明毛玻璃背景、悬停动画、发言中脉冲动画 | GuestCard / ChatMessage 复用 |
| **分区布局规范** | 2×2 Grid，每区独立滚动，区间 1px 发光分割线，响应式断点（≥1440px 2×2 / 768-1439px 2列 / <768px 单列） | StudioPage 容器 |
| **字体 & 间距** | 标题/正文/小字三级字号，行高 1.5-1.8，区域 padding 16px，卡片 gap 12px | 全局排版基准 |

### 2.2 产出流程

```
UI UX Pro Max 输出 → 写入 docs/ui_design_spec.md
                    → 提取 CSS 变量 → src/frontend/src/styles/variables.css
                    → 组件开发时引用该规范
```

### 2.3 设计风格关键词

- 科技风直播间 / 圆桌演播厅
- 深色底 + 霓虹发光边缘
- 毛玻璃卡片，弱化背景、突出内容
- 发言人卡片有呼吸灯效果
- 观点标签用共识绿/分歧红/中立灰三色

---

## 3. 前端页面与组件架构

### 3.1 技术栈

- Vue 3 + Element Plus + Vue Router + Pinia
- Vite 构建工具
- TypeScript

### 3.2 目录结构

```
src/frontend/src/
├── main.ts                          # createApp + Element Plus + Router + Pinia
├── App.vue                          # <router-view>
├── router/index.ts                  # 3 条路由
├── styles/
│   └── variables.css                # CSS 变量（从 ui_design_spec 提取）
├── stores/
│   ├── discussion.ts                # 讨论列表、当前讨论状态
│   └── guest.ts                     # 嘉宾模板库、当前讨论嘉宾
├── views/
│   ├── HomePage.vue                 # 讨论列表页
│   ├── GuestConfigPage.vue          # 嘉宾配置页
│   └── StudioPage.vue               # 演播厅核心页（2×2 Grid 容器）
└── components/
    ├── ChatMessage.vue              # 单条消息组件
    ├── GuestCard.vue                # 单个嘉宾卡片
    └── OpinionPanel.vue             # 观点面板
```

### 3.3 路由表

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 讨论列表 + 新建入口 + 历史回放 |
| `/config/:discussionId?` | GuestConfigPage | 创建/编辑讨论：主题输入、嘉宾选择、人数 |
| `/studio/:discussionId` | StudioPage | 演播厅 2×2 Grid 四分区 |

### 3.4 Pinia Store 设计

**discussionStore**
```
state:  discussions[], currentDiscussion, messages[], opinions[]
actions: fetchDiscussions(), createDiscussion(), loadDiscussion(id)
```

**guestStore**
```
state:  guestTemplates[], activeGuests[]
actions: fetchGuests(), createGuest(), addGuestToDiscussion()
```

### 3.5 三页面组件树

```
HomePage
└── DiscussionCard（v-for 讨论列表项）

GuestConfigPage
├── TopicInput（议题输入框 + 标签）
├── GuestSelector（嘉宾模板选择 + 人数滑块）
└── GuestPreviewList（已选嘉宾卡片预览）

StudioPage（2×2 Grid 容器）
├── [左上] RoundTablePanel
│   ├── HostCard（主持人卡片，金色系）
│   └── GuestCard（v-for 嘉宾，独立色相）
├── [右上] TopicPanel
│   └── TopicItem（v-for 议题/阶段列表）
├── [左下] ChatFlow
│   └── ChatMessage（v-for 消息列表，自滚动）
└── [右下] OpinionPanel
    └── OpinionItem（v-for 观点列表，共识绿/分歧红/中立灰）
```

### 3.6 演播厅四分区定义

| 位置 | 名称 | 内容 | 滚动 |
|------|------|------|------|
| 左上 | 圆桌参会面板 | 主持人卡片 + 全部嘉宾卡片，含头像/发言状态/身份标签 | 独立纵向滚动 |
| 右上 | 主题 & 实时议题面板 | 本场讨论主题、分阶段议题、待讨论要点 | 独立纵向滚动 |
| 左下 | 实时对话流 | 完整聊天/发言记录，消息逐条堆叠，可回溯历史 | 独立纵向滚动 |
| 右下 | 观点共识 & 分歧汇总 | 各方观点、分类共识/对立意见，长列表 | 独立纵向滚动 |

### 3.7 三个子组件接口

**ChatMessage.vue**
```
Props:  { message: MessageDef, senderColor: string, isStreaming: boolean }
Events: 无
Slots:  无
```

**GuestCard.vue**
```
Props:  { guest: GuestDef, isActive: boolean, isSpeaking: boolean, colorTheme: string }
Events: @click → 查看嘉宾详情
Slots:  无
```

**OpinionPanel.vue**
```
Props:  { opinions: OpinionDef[], loading: boolean }
Events: 无
Slots:  无
```

### 3.8 用户流程

```
首页讨论列表 → 点击新建 → 嘉宾配置页（议题输入 + 嘉宾选择 + 人数） → 确认 → 演播厅
演播厅结束后 → 可回看历史讨论记录，支持重放
```

---

## 4. 产出物清单

| # | 产出物 | 路径 |
|---|--------|------|
| 1 | 后端分层骨架（16 文件） | `src/backend/` |
| 2 | UI 设计规范文档（UI UX Pro Max 产出） | `docs/ui_design_spec.md` |
| 3 | CSS 变量文件 | `src/frontend/src/styles/variables.css` |
| 4 | 前端项目骨架（main/Router/Stores） | `src/frontend/src/` |
| 5 | 首页讨论列表页 | `src/frontend/src/views/HomePage.vue` |
| 6 | 嘉宾配置页 | `src/frontend/src/views/GuestConfigPage.vue` |
| 7 | 演播厅核心页 + 3 子组件 | `src/frontend/src/views/StudioPage.vue` + `components/` |
