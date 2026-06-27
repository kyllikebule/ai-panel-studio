# AI Panel Studio — UI 设计规范

> **生成方式:** UI UX Pro Max Design System (Three-Layer Token Architecture)
> **主题:** 科技风直播间 / 圆桌演播厅 · Dark Mode + Glassmorphism + Neon Glow
> **用途:** Vue3 + Element Plus 前端组件开发基准

---

## 1. 设计令牌系统 (Three-Layer)

### 1.1 Layer 1 — 原始令牌 (Primitive Tokens)

```css
:root {
  /* ── 基础色板 ── */
  --pr-color-black: #0a0e17;
  --pr-color-dark-navy: #111827;
  --pr-color-dark-slate: #1a1f2e;
  --pr-color-cyan-400: #22d3ee;
  --pr-color-cyan-500: #00d4ff;
  --pr-color-cyan-600: #0891b2;
  --pr-color-gold-400: #facc15;
  --pr-color-gold-500: #f0b90b;
  --pr-color-gold-600: #ca8a04;
  --pr-color-blue-500: #3b82f6;
  --pr-color-blue-600: #2563eb;
  --pr-color-green-500: #10b981;
  --pr-color-green-600: #059669;
  --pr-color-purple-500: #a855f7;
  --pr-color-purple-600: #7c3aed;
  --pr-color-orange-500: #f97316;
  --pr-color-orange-600: #ea580c;
  --pr-color-red-500: #ef4444;
  --pr-color-red-600: #dc2626;
  --pr-color-gray-400: #9ca3af;
  --pr-color-gray-500: #6b7280;
  --pr-color-gray-600: #4b5563;
  --pr-color-gray-700: #374151;
  --pr-color-white-alpha-04: rgba(255, 255, 255, 0.04);
  --pr-color-white-alpha-06: rgba(255, 255, 255, 0.06);
  --pr-color-white-alpha-08: rgba(255, 255, 255, 0.08);
  --pr-color-white-alpha-10: rgba(255, 255, 255, 0.10);
  --pr-color-white-alpha-15: rgba(255, 255, 255, 0.15);
  --pr-color-cyan-alpha-05: rgba(0, 212, 255, 0.05);
  --pr-color-cyan-alpha-08: rgba(0, 212, 255, 0.08);
  --pr-color-cyan-alpha-15: rgba(0, 212, 255, 0.15);
  --pr-color-cyan-alpha-20: rgba(0, 212, 255, 0.20);
  --pr-color-cyan-alpha-30: rgba(0, 212, 255, 0.30);
  --pr-color-cyan-alpha-40: rgba(0, 212, 255, 0.40);

  /* ── 间距 (4px 基数) ── */
  --pr-space-1: 4px;
  --pr-space-2: 8px;
  --pr-space-3: 12px;
  --pr-space-4: 16px;
  --pr-space-5: 20px;
  --pr-space-6: 24px;
  --pr-space-8: 32px;
  --pr-space-10: 40px;
  --pr-space-12: 48px;

  /* ── 排版 ── */
  --pr-font-family: 'Inter', 'PingFang SC', -apple-system, sans-serif;
  --pr-font-size-title: 20px;
  --pr-font-size-body: 14px;
  --pr-font-size-small: 12px;
  --pr-font-size-h1: 32px;
  --pr-font-size-h2: 24px;
  --pr-font-size-h3: 18px;
  --pr-line-height-title: 1.5;
  --pr-line-height-body: 1.6;
  --pr-font-weight-normal: 400;
  --pr-font-weight-medium: 500;
  --pr-font-weight-semibold: 600;
  --pr-font-weight-bold: 700;

  /* ── 圆角 ── */
  --pr-radius-sm: 6px;
  --pr-radius-md: 8px;
  --pr-radius-lg: 12px;
  --pr-radius-xl: 16px;
  --pr-radius-full: 9999px;

  /* ── 阴影 (毛玻璃 + 霓虹) ── */
  --pr-shadow-card: 0 4px 24px rgba(0, 0, 0, 0.40);
  --pr-shadow-card-hover: 0 4px 24px rgba(0, 212, 255, 0.25);
  --pr-shadow-glow-sm: 0 0 8px rgba(0, 212, 255, 0.20);
  --pr-shadow-glow-md: 0 0 16px rgba(0, 212, 255, 0.30);
  --pr-shadow-glow-lg: 0 0 24px rgba(0, 212, 255, 0.40);

  /* ── 动效时长 ── */
  --pr-duration-fast: 150ms;
  --pr-duration-normal: 250ms;
  --pr-duration-slow: 400ms;
  --pr-easing-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --pr-easing-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### 1.2 Layer 2 — 语义令牌 (Semantic Tokens)

```css
:root {
  /* ── 背景 ── */
  --color-bg-primary: var(--pr-color-black);
  --color-bg-secondary: var(--pr-color-dark-navy);
  --color-bg-tertiary: var(--pr-color-dark-slate);
  --color-bg-card: rgba(17, 24, 39, 0.85);
  --color-bg-card-hover: rgba(26, 31, 46, 0.90);
  --color-bg-input: rgba(255, 255, 255, 0.06);
  --color-bg-overlay: rgba(0, 0, 0, 0.60);

  /* ── 强调色 ── */
  --color-accent: var(--pr-color-cyan-500);
  --color-accent-hover: var(--pr-color-cyan-400);
  --color-accent-muted: var(--pr-color-cyan-600);
  --color-accent-glow: var(--pr-color-cyan-alpha-30);

  /* ── 文字 ── */
  --color-text-primary: #e5e7eb;
  --color-text-secondary: var(--pr-color-gray-400);
  --color-text-muted: var(--pr-color-gray-500);
  --color-text-inverse: var(--pr-color-black);
  --color-text-accent: var(--pr-color-cyan-500);

  /* ── 边框 ── */
  --color-border-default: var(--pr-color-white-alpha-06);
  --color-border-strong: var(--pr-color-white-alpha-10);
  --color-border-accent: var(--pr-color-cyan-alpha-15);
  --color-border-accent-strong: var(--pr-color-cyan-alpha-30);
  --color-border-glow: var(--pr-color-cyan-500);

  /* ── 分割线 ── */
  --color-divider: var(--pr-color-white-alpha-06);
  --color-divider-glow: var(--pr-color-cyan-alpha-15);

  /* ── 语义色 (观点) ── */
  --color-consensus: var(--pr-color-green-500);
  --color-consensus-bg: rgba(16, 185, 129, 0.10);
  --color-consensus-border: rgba(16, 185, 129, 0.30);
  --color-disagreement: var(--pr-color-red-500);
  --color-disagreement-bg: rgba(239, 68, 68, 0.10);
  --color-disagreement-border: rgba(239, 68, 68, 0.30);
  --color-neutral: var(--pr-color-gray-500);
  --color-neutral-bg: rgba(107, 114, 128, 0.10);
  --color-neutral-border: rgba(107, 114, 128, 0.30);

  /* ── 状态色 ── */
  --color-pending: var(--pr-color-gray-500);
  --color-active: var(--pr-color-gold-500);
  --color-success: var(--pr-color-green-500);
  --color-danger: var(--pr-color-red-500);
  --color-warning: var(--pr-color-orange-500);

  /* ── 间距语义 ── */
  --spacing-component: var(--pr-space-3);
  --spacing-section: var(--pr-space-6);
  --spacing-page: var(--pr-space-10);

  /* ── 排版语义 ── */
  --font-size-title: var(--pr-font-size-title);
  --font-size-body: var(--pr-font-size-body);
  --font-size-small: var(--pr-font-size-small);
}
```

### 1.3 Layer 3 — 组件令牌 (Component Tokens)

```css
:root {
  /* ── 卡片 ── */
  --card-bg: var(--color-bg-card);
  --card-bg-hover: var(--color-bg-card-hover);
  --card-border: 1px solid var(--color-border-accent);
  --card-radius: var(--pr-radius-lg);
  --card-padding: var(--pr-space-4);
  --card-gap: var(--pr-space-3);
  --card-shadow: var(--pr-shadow-card);
  --card-shadow-hover: var(--pr-shadow-card-hover);
  --card-backdrop: blur(12px);

  /* ── 按钮 (主) ── */
  --btn-primary-bg: var(--color-accent);
  --btn-primary-bg-hover: var(--color-accent-hover);
  --btn-primary-fg: var(--color-text-inverse);
  --btn-radius: var(--pr-radius-md);
  --btn-padding-y: var(--pr-space-2);
  --btn-padding-x: var(--pr-space-5);

  /* ── 按钮 (Ghost/Text) ── */
  --btn-ghost-fg: var(--color-text-secondary);
  --btn-ghost-fg-hover: var(--color-text-primary);
  --btn-ghost-bg-hover: var(--pr-color-white-alpha-08);

  /* ── 标签 (意见) ── */
  --tag-padding: var(--pr-space-1) var(--pr-space-3);
  --tag-radius: var(--pr-radius-full);
  --tag-font-size: var(--pr-font-size-small);

  /* ── 输入框 ── */
  --input-bg: var(--color-bg-input);
  --input-border: var(--color-border-default);
  --input-border-focus: var(--color-border-accent-strong);
  --input-fg: var(--color-text-primary);
  --input-placeholder: var(--color-text-muted);
  --input-radius: var(--pr-radius-md);
  --input-padding: var(--pr-space-2) var(--pr-space-3);

  /* ── 头像 ── */
  --avatar-size-sm: 32px;
  --avatar-size-default: 40px;
  --avatar-size-lg: 48px;
  --avatar-radius: var(--pr-radius-full);
  --avatar-bg: var(--color-accent);

  /* ── 滚动条 ── */
  --scrollbar-width: 6px;
  --scrollbar-track: transparent;
  --scrollbar-thumb: var(--pr-color-white-alpha-10);
  --scrollbar-thumb-hover: var(--pr-color-white-alpha-15);
}
```

---

## 2. 角色色卡系统 (Role Color Mapping)

每位嘉宾按索引绑定固定色相，通过 `--card-color` 局部变量注入：

| 索引 | 角色 | 色相 | CSS 变量值 | Hex |
|------|------|------|-----------|-----|
| 0 | Host (主持) | Gold | `var(--pr-color-gold-500)` | `#f0b90b` |
| 1 | Guest A | Blue | `var(--pr-color-blue-500)` | `#3b82f6` |
| 2 | Guest B | Green | `var(--pr-color-green-500)` | `#10b981` |
| 3 | Guest C | Purple | `var(--pr-color-purple-500)` | `#a855f7` |
| 4 | Guest D | Orange | `var(--pr-color-orange-500)` | `#f97316` |
| 5 | Guest E | Cyan | `var(--pr-color-cyan-500)` | `#00d4ff` |
| 6 | Guest F | Pink | `#ec4899` | `#ec4899` |

JavaScript 色卡常量：

```typescript
export const ROLE_COLORS = [
  '#f0b90b', // Gold   — Host
  '#3b82f6', // Blue   — Guest A
  '#10b981', // Green  — Guest B
  '#a855f7', // Purple — Guest C
  '#f97316', // Orange — Guest D
  '#00d4ff', // Cyan   — Guest E
  '#ec4899', // Pink   — Guest F
]
```

---

## 3. 组件规范

### 3.1 卡片 (Card — 毛玻璃 + 霓虹发光)

```
┌──────────────────────────────────────────────┐
│  Card Header (可选)                        │
│    Title / Meta                            │
├──────────────────────────────────────────────┤
│  Card Body                                │
│    backdrop-filter: blur(12px);           │
│    border: 1px solid cyan-alpha-15;       │
│    border-radius: 12px;                   │
│    box-shadow: 0 4px 24px rgba(0,0,0,.4);│
│    padding: 16px;                         │
├──────────────────────────────────────────────┤
│  Card Footer (可选)                       │
└──────────────────────────────────────────────┘
```

**交互态：**

| 状态 | 变化 |
|------|------|
| default | 暗底 + 微光边框 |
| hover | `transform: translateY(-2px)` + 增强发光 `box-shadow: neon` |
| active/speaking | 脉冲发光动画 `animation: pulse-glow 1.5s infinite` |
| selected | 边框变亮 `border-color: cyan-500` |
| disabled | `opacity: 0.5` + `cursor: not-allowed` |

```css
.card-glass {
  background: var(--card-bg);
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--card-padding);
  box-shadow: var(--card-shadow);
  transition:
    transform var(--pr-duration-fast) var(--pr-easing-standard),
    box-shadow var(--pr-duration-fast) var(--pr-easing-standard),
    border-color var(--pr-duration-normal) var(--pr-easing-standard);
}

.card-glass:hover {
  transform: translateY(-2px);
  box-shadow: var(--card-shadow-hover);
}

.card-glass.speaking {
  border-color: var(--color-border-glow);
  animation: pulse-glow 1.5s ease-in-out infinite;
}
```

### 3.2 按钮 (Button)

继承 Element Plus 默认尺寸，套用项目色板：

```css
/* Element Plus 覆盖 */
.el-button--primary {
  --el-button-bg-color: var(--color-accent);
  --el-button-border-color: var(--color-accent);
  --el-button-hover-bg-color: var(--color-accent-hover);
  --el-button-hover-border-color: var(--color-accent-hover);
  --el-button-active-bg-color: var(--color-accent-muted);
}
```

### 3.3 标签 (Tag — 观点分类)

| 观点类型 | CSS 类 | 边框色 | 背景色 | 文字色 |
|---------|--------|--------|--------|--------|
| 共识 | `.tag-consensus` | `--color-consensus-border` | `--color-consensus-bg` | `--color-consensus` |
| 分歧 | `.tag-disagreement` | `--color-disagreement-border` | `--color-disagreement-bg` | `--color-disagreement` |
| 中立 | `.tag-neutral` | `--color-neutral-border` | `--color-neutral-bg` | `--color-neutral` |

### 3.4 讨论状态标签

| 状态 | 色系 | 文字 |
|------|------|------|
| pending | gray (info) | 待开始 |
| active | gold (warning) | 进行中 |
| paused | gray (info) | 已暂停 |
| completed | green (success) | 已完成 |

### 3.5 头像 (Avatar — 角色色底 + 首字)

```css
.avatar-role {
  width: var(--avatar-size-default);
  height: var(--avatar-size-default);
  border-radius: var(--avatar-radius);
  background: var(--card-color, var(--color-accent));
  color: var(--color-text-inverse);
  font-weight: var(--pr-font-weight-bold);
  font-size: 18px;
  line-height: var(--avatar-size-default);
  text-align: center;
  flex-shrink: 0;
}
```

---

## 4. 演播厅 Grid 布局系统

### 4.1 2×2 四分区规范

```
┌──────────────────────┬──────────────────────┐
│  左上 (280px/250px)   │  右上 (1fr)           │
│  RoundTablePanel      │  TopicPanel           │
│  参会嘉宾卡片          │  讨论议题 & 阶段       │
│  overflow-y: auto     │  overflow-y: auto     │
├──────────────────────┼──────────────────────┤
│  左下 (280px/250px)   │  右下 (1fr)           │
│  ChatFlow             │  OpinionPanel         │
│  实时对话流            │  观点共识 & 分歧       │
│  overflow-y: auto     │  overflow-y: auto     │
└──────────────────────┴──────────────────────┘
```

**Grid CSS：**

```css
.studio-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1px;
  background: var(--color-divider-glow);  /* 1px 发光分割线 */
  overflow: hidden;
  flex: 1;
}

.grid-panel {
  background: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-title {
  margin: 0;
  padding: 12px var(--card-padding);
  font-size: 14px;
  font-weight: var(--pr-font-weight-semibold);
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-divider);
  flex-shrink: 0;
}

.panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--pr-space-2);
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}

.panel-scroll::-webkit-scrollbar {
  width: var(--scrollbar-width);
}

.panel-scroll::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 3px;
}

.panel-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}
```

### 4.2 响应式断点

```css
/* ≥1440px — 2×2 Grid (default) */
/* 已在上方定义 */

/* 768px – 1439px — 2列 (左上+右上叠、左下+右下叠) */
@media (max-width: 1439px) {
  .studio-grid {
    grid-template-columns: 250px 1fr;
  }
}

/* <768px — 单列堆叠 */
@media (max-width: 767px) {
  .studio-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow-y: auto;
  }

  .grid-panel {
    max-height: 50vh;
  }
}
```

---

## 5. 动画关键帧

### 5.1 脉冲发光 (发言中卡片)

```css
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 8px color-mix(in srgb, var(--card-color, var(--color-accent)) 20%, transparent);
  }
  50% {
    box-shadow: 0 0 20px color-mix(in srgb, var(--card-color, var(--color-accent)) 50%, transparent);
  }
}

@keyframes pulse-glow-accent {
  0%, 100% {
    box-shadow: var(--pr-shadow-glow-sm);
  }
  50% {
    box-shadow: var(--pr-shadow-glow-lg);
  }
}
```

### 5.2 呼吸灯点 (发言指示器)

```css
@keyframes blink-dot {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%      { opacity: 1.0; transform: scale(1.0); }
}
```

### 5.3 淡入上滑 (消息/观点入场)

```css
@keyframes fade-slide-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

### 5.4 光标闪烁 (流式 Token)

```css
@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}
```

### 5.5 流式文本入场 (Token 逐字)

```css
.streaming-text::after {
  content: '|';
  animation: cursor-blink 1s step-end infinite;
  color: var(--color-accent);
}
```

---

## 6. 全局重置 & Body

```css
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--pr-font-family);
  font-size: var(--font-size-body);
  line-height: var(--pr-line-height-body);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  overflow: hidden;  /* 演播厅全屏模式 */
}

/* Element Plus 深色覆盖 */
.el-button--primary {
  --el-button-bg-color: var(--color-accent);
  --el-button-border-color: var(--color-accent);
}
.el-tag {
  --el-tag-bg-color: var(--pr-color-white-alpha-08);
  --el-tag-border-color: var(--color-border-default);
  --el-tag-text-color: var(--color-text-primary);
}
.el-input__wrapper {
  background: var(--input-bg) !important;
  box-shadow: 0 0 0 1px var(--input-border) inset !important;
}
.el-input__inner {
  color: var(--input-fg) !important;
}
.el-empty__description p {
  color: var(--color-text-muted);
}
```

---

## 7. 导出清单

| 文件 | 内容 |
|------|------|
| `docs/ui_design_spec.md` | 本文档 — 设计系统完整规范 |
| `src/frontend/src/styles/variables.css` | CSS 变量提取 (Primitive + Semantic + Component + Animations) |
| 组件 `.vue` 文件 | 引用 `var(--xxx)` + 动画 `@keyframes` |
