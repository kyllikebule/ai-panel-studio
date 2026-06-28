<template>
  <div class="create-discuss-page">
    <!-- 顶部栏 -->
    <header class="page-topbar">
      <el-button text @click="$router.push('/')">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1 class="topbar-title">创建圆桌讨论</h1>
    </header>

    <!-- 主体 -->
    <main class="page-body">
      <!-- Step 1: 配置表单 -->
      <section class="config-card">
        <h2 class="section-heading">讨论配置</h2>

        <!-- 议题输入 -->
        <div class="form-group">
          <label class="form-label" for="topic-input">
            讨论议题 <span class="required">*</span>
          </label>
          <el-input
            id="topic-input"
            v-model="topic"
            placeholder="输入讨论主题，如：AI 是否应该被严格监管？"
            size="large"
            maxlength="200"
            show-word-limit
            @blur="validateTopic"
          />
          <p v-if="topicError" class="form-error">{{ topicError }}</p>
        </div>

        <!-- 专家人数选择 -->
        <div class="form-group">
          <label class="form-label" for="count-select">
            专家人数 <span class="required">*</span>
          </label>
          <el-select
            id="count-select"
            v-model="expertCount"
            placeholder="选择专家人数"
            size="large"
            style="width: 100%"
          >
            <el-option
              v-for="n in [2, 3, 4, 5, 6]"
              :key="n"
              :label="`${n} 位专家`"
              :value="n"
            />
          </el-select>
        </div>

        <!-- 生成嘉宾按钮 -->
        <el-button
          type="primary"
          size="large"
          :disabled="!canGenerate"
          :loading="generating"
          @click="generateGuests"
        >
          <el-icon><MagicStick /></el-icon>
          生成嘉宾
        </el-button>
      </section>

      <!-- Step 2: 嘉宾预览区 -->
      <section v-if="guestPreviews.length" class="preview-section">
        <div class="section-header">
          <h2 class="section-heading">已生成嘉宾 ({{ guestPreviews.length }} 位)</h2>
          <el-button text type="primary" size="small" @click="generateGuests">
            <el-icon><Refresh /></el-icon>
            重新生成
          </el-button>
        </div>

        <div class="guest-grid">
          <div
            v-for="(guest, idx) in guestPreviews"
            :key="idx"
            class="guest-preview-card"
            :style="{ '--card-color': ROLE_COLORS[idx] }"
          >
            <div class="guest-avatar">{{ guest.name[0] }}</div>
            <div class="guest-info">
              <span class="guest-name">{{ guest.name }}</span>
              <span class="guest-role">{{ guest.persona }}</span>
            </div>
            <el-tag
              :color="ROLE_COLORS[idx]"
              size="small"
              effect="dark"
            >
              {{ guest.speakStyle }}
            </el-tag>
          </div>
        </div>

        <!-- 确认按钮 -->
        <el-button
          type="primary"
          size="large"
          class="confirm-btn"
          :loading="entering"
          @click="enterStudio"
        >
          <el-icon><VideoPlay /></el-icon>
          确认进入演播厅
        </el-button>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, MagicStick, Refresh, VideoPlay } from '@element-plus/icons-vue'

const router = useRouter()

// ═══════════════════════════════════════
// 角色色板
// ═══════════════════════════════════════
const ROLE_COLORS = [
  '#f0b90b', // Gold
  '#3b82f6', // Blue
  '#10b981', // Green
  '#a855f7', // Purple
  '#f97316', // Orange
  '#00d4ff', // Cyan
]

// ═══════════════════════════════════════
// 表单状态
// ═══════════════════════════════════════
const topic = ref('')
const expertCount = ref(3)
const topicError = ref('')
const generating = ref(false)
const entering = ref(false)

// ═══════════════════════════════════════
// 嘉宾预览
// ═══════════════════════════════════════
interface GuestPreview {
  name: string
  persona: string
  speakStyle: string
}

const guestPreviews = ref<GuestPreview[]>([])

// ═══════════════════════════════════════
// 计算属性
// ═══════════════════════════════════════
const canGenerate = computed(() => topic.value.trim().length >= 4 && expertCount.value >= 2)

// ═══════════════════════════════════════
// 表单校验
// ═══════════════════════════════════════
function validateTopic() {
  const val = topic.value.trim()
  if (!val) {
    topicError.value = '请输入讨论议题'
  } else if (val.length < 4) {
    topicError.value = '议题至少需要 4 个字符'
  } else {
    topicError.value = ''
  }
}

// ═══════════════════════════════════════
// 生成嘉宾 — 调用 AI API 动态生成
// ═══════════════════════════════════════
async function generateGuests() {
  validateTopic()
  if (topicError.value) return

  generating.value = true
  guestPreviews.value = []

  try {
    const res = await fetch('/api/guests/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: topic.value.trim(), count: expertCount.value }),
    })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    const data = await res.json()
    guestPreviews.value = (data.guests || []).map((g: any) => ({
      name: g.name,
      persona: g.persona,
      speakStyle: g.speak_style,
    }))
  } catch (e) {
    console.error('生成嘉宾失败:', e)
  } finally {
    generating.value = false
  }
}

// ═══════════════════════════════════════
// 进入演播厅：生成主持人 → 创建讨论 → 创建嘉宾模板 → 关联嘉宾 → 跳转演播厅
// ═══════════════════════════════════════
async function enterStudio() {
  entering.value = true
  try {
    // 0. 调用 AI 生成主持人
    let hostName = '张主持人'
    let hostPrompt = '你是专业讨论主持人，保持中立，用标准中文开场、追问、串联、总结。'
    try {
      const hRes = await fetch('/api/discussions/generate-host', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.value }),
      })
      if (hRes.ok) {
        const h = await hRes.json()
        hostName = h.name
        hostPrompt = h.system_prompt
      }
    } catch (e) {
      console.warn('Host generation failed, using fallback:', e)
    }

    // 1. POST /api/discussions → 创建讨论（含主持人）
    const dRes = await fetch('/api/discussions/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.value,
        host: { name: hostName, system_prompt: hostPrompt },
        max_rounds: expertCount.value,
      }),
    })
    const discussion = await dRes.json()

    // 2. 逐个创建嘉宾模板 + 关联到讨论
    for (const guest of guestPreviews.value) {
      const gRes = await fetch('/api/guests/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: guest.name,
          persona: guest.persona,
          system_prompt: `你是${guest.name}，${guest.persona}。发言风格：${guest.speakStyle}`,
          speak_style: guest.speakStyle,
        }),
      })
      const g = await gRes.json()
      await fetch(`/api/discussions/${discussion.id}/guests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_id: g.id }),
      })
    }

    router.push(`/studio/${discussion.id}`)
  } finally {
    entering.value = false
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════
   页面布局
   ═══════════════════════════════════════ */
.create-discuss-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

/* ══ 顶部栏 ══ */
.page-topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
  height: 64px;
  background: var(--color-bg-secondary);
  border-bottom: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
}

.topbar-title {
  margin: 0;
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
}

/* ══ 页面主体 ══ */
.page-body {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--spacing-section, 24px) 24px;
}

/* ══ 配置卡片 ══ */
.config-card {
  background: var(--card-bg);
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--card-padding);
}

.section-heading {
  margin: 0 0 var(--card-gap, 12px);
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
}

/* ══ 表单 ══ */
.form-group {
  margin-bottom: var(--card-gap, 12px);
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: var(--pr-font-size-body, 14px);
  font-weight: var(--pr-font-weight-medium, 500);
  color: var(--color-text-secondary);
}

.required {
  color: var(--color-danger, #ef4444);
}

.form-error {
  margin: 4px 0 0;
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-danger, #ef4444);
}

/* ══ 嘉宾预览区 ══ */
.preview-section {
  margin-top: var(--spacing-section, 24px);
  background: var(--card-bg);
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--card-padding);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--card-gap, 12px);
}

.guest-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.guest-preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px var(--card-padding, 16px);
  border-radius: var(--pr-radius-md, 8px);
  background: color-mix(in srgb, var(--card-color, var(--color-accent)) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--card-color, var(--color-accent)) 25%, transparent);
  transition: border-color var(--pr-duration-fast, 150ms) ease-out;
}

.guest-preview-card:hover {
  border-color: var(--card-color, var(--color-accent));
}

.guest-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--pr-radius-full, 9999px);
  background: var(--card-color, var(--color-accent));
  color: #000;
  font-weight: var(--pr-font-weight-bold, 700);
  font-size: 20px;
  line-height: 44px;
  text-align: center;
  flex-shrink: 0;
}

.guest-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.guest-name {
  font-size: var(--pr-font-size-body, 14px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
}

.guest-role {
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.confirm-btn {
  margin-top: var(--card-gap, 12px);
  width: 100%;
}

/* ═══════════════════════════════════════
   响应式
   ═══════════════════════════════════════ */
@media (max-width: 767px) {
  .page-topbar {
    padding: 0 16px;
    height: 56px;
  }

  .page-body {
    padding: var(--spacing-section, 24px) 16px;
  }
}
</style>
