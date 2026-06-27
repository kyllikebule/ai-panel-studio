# AI Panel Studio — 开发说明

本文档记录项目各阶段的关键开发决策和技术过程。

---

## DDD 阶段：使用 UI UX Pro Max 设计页面

DDD（Design-Driven Development）阶段的核心任务是前端页面开发。根据开发规则要求，所有前端页面的设计必须先调用 UI UX Pro Max 技能生成设计系统，再编写 Vue 代码。

### 1. 设计系统生成

**命令：**
```bash
python scripts/search.py "虚拟专家圆桌辩论直播间 简约科技风 沉浸式演播厅 dark mode 霓虹" --design-system -p "AI Panel Studio" -f markdown
```

**AI 推荐结果：** Cyberpunk UI + Dark Mode (OLED) 融合风格。

核心输出：

| 维度 | 推荐值 |
|------|--------|
| Style | Cyberpunk UI（霓虹、暗色、HUD 感）+ Dark Mode OLED（深黑、高对比、低发光） |
| Heading Font | Inter（600-700 字重） |
| Body Font | Inter（400-500 字重） |
| Base Background | `#0a0e17`（非纯黑，避免 OLED 拖影） |
| Accent Color | `#00d4ff`（Cyan 霓虹强调） |
| Effects | 毛玻璃 blur(12px) + 霓虹 text-shadow（克制使用） |
| Anti-patterns | 禁止浅色模式、禁止纯装饰动画、禁止 emoji 图标 |

### 2. Token 提取：三层架构

根据 UI UX Pro Max Design System 的三层令牌体系，将设计推荐转化为可执行的 CSS 变量：

```
Primitive Tokens（原始值）
  → 颜色：#0a0e17, #00d4ff, #f0b90b...
  → 间距：4px / 8px / 12px / 16px...
  → 排版：Inter / 14px body / 1.6 line-height

Semantic Tokens（语义别名）
  → --color-bg-primary → 页面底色
  → --color-accent       → 霓虹强调色
  → --color-consensus    → 共识绿
  → --color-role-host    → 主持人金

Component Tokens（组件专属）
  → --card-bg + --card-border + --card-backdrop → 毛玻璃卡片
  → --btn-primary-bg → 按钮主色
  → --tag-padding → 标签内距
```

完整输出：`src/frontend/src/styles/variables.css`（300+ 行 CSS 变量）

### 3. 页面设计过程

DDD 阶段共开发 3 个页面，每页都基于设计规范和 AI UX 建议：

#### 首页（Home.vue）

- **参考规范：** §5 布局 & §6 排版 — max-width 容器、响应式断点
- **组件：** DiscussCard.vue — 毛玻璃卡片 + hover 抬升 + 霓虹发光边框
- **UX 参考：** empty state → 无讨论时显示引导文案和新建按钮

#### 创建讨论页（CreateDiscuss.vue）

- **参考规范：** §8 表单 — 每输入有 visible label、必填星号、blur 校验
- **嘉宾选择：** toggle grid 卡片 + 角色色卡预览
- **AI 建议：** progressive disclosure — 先填写议题 → 生成嘉宾 → 再确认进入，分步骤避免信息过载

#### 演播厅核心页（Studio.vue）

- **参考规范：** §5 布局 — `100vh` 整页禁止滚动，四分区内部独立 scroll
- **分区设计：**
  - 左侧 Transcript（flex:1）— 消息流，自动滚底
  - 右上嘉宾状态（flex:1）— GuestCard 含发言中脉冲动画
  - 右下观点面板（flex:1）— 三色共识/分歧/中立标签
  - 底部总结（max-h:160px）— 主持人总结固底
- **AI 建议：** 分割线使用 `--color-divider-glow`（1px rgba cyan 15%）而非纯白，保持暗色氛围

### 4. 组件开发规范

每个组件都遵循 UI UX Pro Max 的 Component Spec Pattern：

| 组件 | 状态 | Props | 参考 |
|------|------|-------|------|
| DiscussCard | default / hover / focus-visible | `discussion: DiscussionItem` | §6 卡片组件规范 |
| GuestCard | idle / speaking（脉冲发光 + 3 点呼吸灯） | `guest / isSpeaking / colorTheme` | §7 动画 §2 touch target ≥ 44px |
| ChatMessage | host / guest / system / streaming | `senderName / senderRole / senderColor / isStreaming` | §6 角色色卡体系 |
| OpinionItem | consensus / disagreement / neutral | `item: {category, stanceSummary, confidence, evidence}` | §6 观点三色标签 |

### 5. 响应式适配

基于 UI UX Pro Max §5 布局规范的三档断点：

| 断点 | Studio.vue Grid | 左列宽 |
|------|-----------------|--------|
| ≥ 1024px | Transcript 左 + Guest/Opinion 右 (300px) | flex: 1 + 300px |
| ≤ 1023px | 上下堆叠 + 右侧横排 | 100% |
| ≤ 767px | 单列全堆叠 | 100% |

### 6. 设计规范文档

DDD 阶段生成的完整设计规范文档：`docs/ui_design_spec.md`

包含：主题风格、配色方案、角色色板、布局规范、组件样式、响应式规则、交互规范、排版系统、CSS 变量完整导出。
