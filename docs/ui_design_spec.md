# AI Panel Studio — UI 设计规范文档

> **生成方式:** UI UX Pro Max Design System（Cyberpunk UI + Dark Mode OLED 融合）
> **产品定位:** 虚拟专家圆桌辩论直播间 · 沉浸式演播厅风格
> **技术栈:** Vue 3 + Element Plus + Vite
> **设计基准日期:** 2026-06-27

---

## 1. 主题风格

### 1.1 视觉定位

**风格名称:** 简约科技风线上演播厅（Cyberpunk Dark Minimal）

**核心关键词:** 沉浸式 · 霓虹微光 · 深色背景 · 毛玻璃卡片 · 科技演播厅

**设计哲学:** 
- 深色底降低视觉疲劳，突出内容（嘉宾发言、观点数据）
- 霓虹强调色仅用于关键交互元素，克制使用
- 毛玻璃卡片弱化容器感，强化信息层级
- 禁止纯装饰性动画，所有动效服务于状态传达

### 1.2 主色调配色方案

| 颜色角色 | 色值 | CSS 变量 | 用途 |
|---------|------|----------|------|
| 页面底色 | `#0a0e17` | `--color-bg-primary` | 全站背景 |
| 次级底色 | `#111827` | `--color-bg-secondary` | 导航栏/面板底 |
| 卡片底色 | `rgba(17,24,39,0.85)` | `--color-bg-card` | 毛玻璃卡片 |
| 主强调色 | `#00d4ff` | `--color-accent` | 按钮/链接/发光边框 |
| 主强调悬停 | `#22d3ee` | `--color-accent-hover` | hover 增亮 |
| 文字主色 | `#e5e7eb` | `--color-text-primary` | 标题/正文 |
| 文字辅色 | `#9ca3af` | `--color-text-secondary` | 元信息/时间戳 |
| 文字弱色 | `#6b7280` | `--color-text-muted` | 占位/禁用态 |
| 边框默认 | `rgba(255,255,255,0.06)` | `--color-border-default` | 卡片/分割线 |
| 边框发光 | `rgba(0,212,255,0.15)` | `--color-border-accent` | 悬停/激活态 |
| 成功/共识 | `#10b981` | `--color-consensus` | 观点-共识标签 |
| 危险/分歧 | `#ef4444` | `--color-disagreement` | 观点-分歧标签 |
| 中性/中立 | `#6b7280` | `--color-neutral` | 观点-中立标签 |
| 待开始 | `#6b7280` | `--color-pending` | 讨论状态 |
| 进行中 | `#f0b90b` | `--color-active` | 讨论状态 |
| 已完成 | `#10b981` | `--color-success` | 讨论状态 |

### 1.3 嘉宾角色区分色板（7 色固定映射）

每位嘉宾按其在讨论中的加入顺序自动分配固定色相，通过组件 prop `colorTheme` 注入：

| 索引 | 角色 | 色相 | 色值 | 适用 |
|------|------|------|------|------|
| 0 | 主持人 | 金色 | `#f0b90b` | Host |
| 1 | 嘉宾 A | 蓝色 | `#3b82f6` | Guest |
| 2 | 嘉宾 B | 绿色 | `#10b981` | Guest |
| 3 | 嘉宾 C | 紫色 | `#a855f7` | Guest |
| 4 | 嘉宾 D | 橙色 | `#f97316` | Guest |
| 5 | 嘉宾 E | 青色 | `#00d4ff` | Guest |
| 6 | 嘉宾 F | 粉色 | `#ec4899` | Guest |

**TypeScript 色板常量（供 GuestCard 引用）:**
```typescript
export const ROLE_COLORS: string[] = [
  '#f0b90b', // Gold   — 主持人
  '#3b82f6', // Blue   — 嘉宾A
  '#10b981', // Green  — 嘉宾B
  '#a855f7', // Purple — 嘉宾C
  '#f97316', // Orange — 嘉宾D
  '#00d4ff', // Cyan   — 嘉宾E
  '#ec4899', // Pink   — 嘉宾F
]
```

### 1.4 辅助色

| 用途 | 色值 | 说明 |
|------|------|------|
| 数据图表辅色 1 | `#f59e0b` | 琥珀色 |
| 数据图表辅色 2 | `#06b6d4` | 天蓝 |
| 数据图表辅色 3 | `#8b5cf6` | 紫罗兰 |
| 骨架屏/加载态 | `rgba(255,255,255,0.04)` | 微弱白底 |
| 遮罩层 | `rgba(0,0,0,0.60)` | 模态框/抽屉背景 |
| 输入框底 | `rgba(255,255,255,0.06)` | 表单控件 |

---

## 2. 布局规范

### 2.1 演播厅页面 — 2×2 Grid 四分区

```
┌─────────────────────────┬─────────────────────────┐
│  左上 (fixed 280px)      │  右上 (1fr 弹性)         │
│  RoundTablePanel         │  TopicPanel              │
│  圆桌参会面板             │  主题 & 实时议题面板       │
│  主持人 + 嘉宾卡片列表    │  讨论主题/分阶段议题       │
│  overflow-y: auto        │  overflow-y: auto        │
├─────────────────────────┼─────────────────────────┤
│  左下 (fixed 280px)      │  右下 (1fr 弹性)         │
│  ChatFlow                │  OpinionPanel            │
│  实时对话流               │  观点共识 & 分歧汇总      │
│  消息逐条堆叠             │  共识/分歧/中立三色标签    │
│  overflow-y: auto        │  overflow-y: auto        │
└─────────────────────────┴─────────────────────────┘
```

**Grid CSS 规范:**
```css
.studio-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 1px;
  /* 1px 发光分割线 */
  background: rgba(0, 212, 255, 0.15);
  flex: 1;
  overflow: hidden;
}
```

### 2.2 面板内部容器标准

每个 Grid 单元格（`.grid-panel`）内部结构固定：

```
┌──────────────────────────┐
│ Panel Header (固定高度)    │  padding: 12px 16px
│ 标题 + 可选操作按钮        │  border-bottom: 1px 弱分割
├──────────────────────────┤
│                          │
│ Panel Scroll (flex: 1)   │  overflow-y: auto
│ 内容区，独立纵向滚动       │  padding: 8px
│                          │  scrollbar-width: thin
│                          │
└──────────────────────────┘
```

**滚动条定制:**
```css
.panel-scroll {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.10) transparent;
}
.panel-scroll::-webkit-scrollbar { width: 6px; }
.panel-scroll::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.10);
  border-radius: 3px;
}
.panel-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.15);
}
```

### 2.3 其他页面布局

| 页面 | 最大宽度 | 间距 | 说明 |
|------|---------|------|------|
| 首页（讨论列表） | `max-width: 960px` | `padding: 40px 24px` | 居中单列 |
| 嘉宾配置页 | `max-width: 800px` | `padding: 40px 24px` | 居中单列 |
| 演播厅 | `100vw × 100vh` | 无边距 | 全屏沉浸 |

---

## 3. 组件规范

### 3.1 讨论卡片（Discussion Card）

用于首页讨论列表，可点击进入演播厅。

```
┌─────────────────────────────────────────────┐
│  讨论主题（16px semibold）        状态标签     │
│  主持人：xxx · 轮次：2/5                     │  ← 元信息行
│                              创建日期        │
└─────────────────────────────────────────────┘
```

**样式令牌:**
```css
.discussion-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: transform 150ms ease-out, box-shadow 150ms ease-out;
}
.discussion-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 24px rgba(0, 212, 255, 0.25);
}
```

**状态标签色彩映射:**
| 讨论状态 | Element Plus Tag Type | 显示文字 |
|---------|----------------------|---------|
| pending | `info` | 待开始 |
| active | `warning` | 进行中 |
| paused | `info` | 已暂停 |
| completed | `success` | 已完成 |

### 3.2 嘉宾状态小窗（Guest Card）

用于演播厅左上角"圆桌参会面板"，展示嘉宾头像、名称、发言状态。

```
┌──────────────────────────────────┐
│ ┌──┐                              │
│ │金│  嘉宾名称（14px semibold）    │
│ └──┘  人设简述（12px 辅色）       │
│ 40px                    ● ● ●    │  ← 发言中呼吸灯
│ 头像                              │
└──────────────────────────────────┘
```

**三种视觉状态:**
| 状态 | 边框 | 背景 | 动效 |
|------|------|------|------|
| 待机（idle） | `1px rgba(255,255,255,0.06)` | `rgba(255,255,255,0.04)` | 无 |
| 激活（active） | `1px var(--card-color)` | `color-mix(in srgb, var(--card-color) 8%, transparent)` | 无 |
| 发言中（speaking） | `1px var(--card-color)` | 同上 | `pulse-glow` 1.5s 循环 |

**发言中脉冲动画:**
```css
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 8px color-mix(in srgb, var(--card-color) 20%, transparent);
  }
  50% {
    box-shadow: 0 0 20px color-mix(in srgb, var(--card-color) 50%, transparent);
  }
}
```

**呼吸灯三点指示器:**
```css
.speaking-indicator {
  display: flex; gap: 4px;
}
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--card-color);
  animation: blink-dot 1s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink-dot {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%      { opacity: 1.0; transform: scale(1.0); }
}
```

**头像样式（首字圆形）:**
```css
.guest-card-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--card-color);
  color: #000; font-weight: 700; font-size: 18px;
  line-height: 40px; text-align: center;
  flex-shrink: 0;
}
```

### 3.3 发言消息气泡（Chat Message）

用于演播厅左下角"实时对话流"，逐条展示发言记录。

```
┌──────────────────────────────────────┐
│ ● 主持人                   #12       │  ← 发送者 + 序号
│                                      │
│ 各位嘉宾，今天我们讨论AI监管...       │  ← 正文 14px / 行高 1.6
│                                      │
│                         42 tokens    │  ← 元信息
└──────────────────────────────────────┘
```

**角色区分（左侧色条）:**
| 角色 | 左边框色 | 背景色 |
|------|---------|--------|
| host（主持人） | `#f0b90b` (金色) | `rgba(240,185,11,0.06)` |
| guest（嘉宾） | 继承嘉宾色卡 | `rgba(255,255,255,0.04)` |
| system（系统） | `#6b7280` (灰色) | `rgba(255,255,255,0.04)` |
| streaming（流式） | `#00d4ff` (青色) | `rgba(0,212,255,0.04)` |

**流式输出光标:**
```css
.cursor-blink {
  animation: blink 1s step-end infinite;
  color: var(--color-accent);
}
```

### 3.4 观点标签（Opinion Item）

用于演播厅右下角"观点共识 & 分歧汇总面板"。

```
┌──────────────────────────────────────┐
│ [共识]  置信度 85%                   │  ← 分类标签 + 置信度
│                                      │
│ AI监管有助于防止技术滥用...           │  ← 观点摘要
│                                      │
│ "原文引用片段..."                    │  ← 证据引用（斜体）
└──────────────────────────────────────┘
```

**三色分类体系:**
| 分类 | 标签色 | 左边框 | 背景 | 文字色 |
|------|--------|--------|------|--------|
| 共识 (consensus) | success (绿) | `#10b981` | `rgba(16,185,129,0.06)` | `#10b981` |
| 分歧 (disagreement) | danger (红) | `#ef4444` | `rgba(239,68,68,0.06)` | `#ef4444` |
| 中立 (neutral) | info (灰) | `#6b7280` | `rgba(107,114,128,0.06)` | `#6b7280` |

**置信度显示:** `(confidence * 100).toFixed(0) + '%'`，灰色小字，位于标签右侧。

---

## 4. 响应式规则（三档断点）

### 4.1 断点表

| 档位 | 宽度范围 | Grid 布局 | 左侧列宽 |
|------|---------|-----------|---------|
| 超宽屏 | ≥ 1440px | 2列 × 2行 四象限 | 280px |
| 桌面窄屏 | 768px – 1439px | 2列 × 2行 四象限 | 250px |
| 笔记本/平板 | < 768px | 单列堆叠（四区纵向排列） | 100% |

### 4.2 各断点 CSS

```css
/* 超宽屏 ≥1440px（默认值，无需媒体查询） */
.studio-grid {
  grid-template-columns: 280px 1fr;
  grid-template-rows: 1fr 1fr;
}

/* 桌面窄屏 768-1439px */
@media (max-width: 1439px) {
  .studio-grid {
    grid-template-columns: 250px 1fr;
  }
}

/* 笔记本/平板 <768px */
@media (max-width: 767px) {
  .studio-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow-y: auto;
  }
  .grid-panel {
    max-height: 50vh; /* 每区限高半屏，防止单区占满 */
  }
}
```

### 4.3 首页 & 配置页响应式

- 首页 `max-width: 960px` 在 < 768px 下改为 `max-width: 100%; padding: 24px 16px`
- 配置页 `max-width: 800px` 同理调整
- 嘉宾选择网格 `grid-template-columns: repeat(auto-fill, minmax(140px, 1fr))` 自适应

---

## 5. 交互规范

### 5.1 嘉宾待机 ↔ 发言中状态切换

```
待机态（idle）                  发言中（speaking）
┌──────────────┐              ┌──────────────┐
│ 微弱白边框    │  ──触发──→   │ 角色色发光边框 │
│ 暗底卡片      │              │ 脉冲光晕动画   │
│ 无指示器      │              │ 三点呼吸灯     │
└──────────────┘              └──────────────┘
                 ←──结束──
```

**状态切换规则:**
- 每次仅 1 人处于"发言中"状态（speakingGuestId 全局唯一）
- 发言结束 → `speak_done` WebSocket 事件 → 清除 speakingGuestId → GuestCard 回到待机态
- 状态过渡使用 `transition: border-color 300ms, box-shadow 300ms`

### 5.2 消息入场轻动效

| 场景 | 动效 | 时长 | 缓动 |
|------|------|------|------|
| 新消息出现 | `fade-slide-up`（淡入 + 上滑 8px） | 250ms | `ease-out` |
| 观点提炼出现 | `fade-in`（仅淡入） | 200ms | `ease-out` |
| 流式 token 光标 | `cursor-blink`（闪烁） | 1s | `step-end` |
| 卡片悬停 | `translateY(-2px)` + 增强发光 | 150ms | `ease-out` |
| 按钮按下 | Element Plus 默认 ripple | — | — |

**入场动画 CSS:**
```css
@keyframes fade-slide-up {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.message-enter-active {
  animation: fade-slide-up 250ms ease-out;
}
.opinion-enter-active {
  animation: fade-in 200ms ease-out;
}
```

### 5.3 动效约束

- ✅ 所有动画 ≤ 300ms（除脉冲循环 1.5s、光标闪烁 1s）
- ✅ 仅使用 `transform` 和 `opacity`，禁止动画 `width/height/top/left`
- ✅ 尊重 `prefers-reduced-motion`：检测到 `reduce` 时禁用所有非必要动画
- ❌ 禁止纯装饰性动画（如背景渐变旋转、无意义弹跳）
- ❌ 禁止同时动画 3 个以上元素

### 5.4 可访问性要求

| 项目 | 标准 |
|------|------|
| 文字对比度 | 主文字 ≥ 4.5:1（WCAG AA） |
| 焦点指示器 | 所有可交互元素有可见 focus ring |
| 键盘导航 | Tab 顺序 = 视觉顺序 |
| 触摸目标 | 最小 44×44px（移动端） |
| 色觉无障碍 | 观点分类同时使用颜色 + 文字标签 |
| 减弱动效 | `@media (prefers-reduced-motion: reduce)` |

---

## 6. 排版系统

| 层级 | 字号 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 32px | 700 | 1.4 | 页面大标题 |
| H2 | 24px | 600 | 1.4 | 区块标题 |
| H3 / 面板标题 | 18px | 600 | 1.5 | 卡片标题 |
| 正文 | 14px | 400 | 1.6 | 消息内容/描述 |
| 小字 | 12px | 400 | 1.5 | 时间戳/元信息 |
| 标签 | 12px | 500 | 1.4 | 状态标签/观点分类 |

**字体族:** `'Inter', 'PingFang SC', -apple-system, sans-serif`

**Google Fonts 引入:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
```

---

## 7. CSS 变量完整导出（供 `variables.css` 引用）

见 `src/frontend/src/styles/variables.css`——该文件包含本规范的全部三层令牌（Primitive → Semantic → Component），由设计规范自动提取。

---

## 附录 A: UI UX Pro Max 原始推荐

| 维度 | 推荐值 |
|------|--------|
| Style | Cyberpunk UI + Dark Mode (OLED) 融合 |
| Heading Font | Inter (700/600) |
| Body Font | Inter (400/500) |
| Base Background | `#0a0e17`（非纯黑 #000000，避免 OLED 拖影） |
| Accent | `#00d4ff`（Cyan 霓虹） |
| Effects | 毛玻璃 blur(12px) + 霓虹 text-shadow（克制使用） |
| Anti-patterns | 禁止浅色模式、禁止纯装饰动画、禁止 emoji 图标 |
| Accessibility | WCAG AA（深色+霓虹需谨慎对比度） |

## 附录 B: 与 Element Plus 的兼容规则

- `el-button--primary` 背景色覆盖为 `--color-accent`
- `el-tag` 背景/边框使用暗色透明底，保持与深色主题一致
- `el-input__wrapper` 背景覆盖为半透明白底
- `el-empty__description` 文字使用辅色
- Element Plus 默认圆角 `--el-border-radius-base` 保持 4px（卡片使用独立的 12px 圆角）
