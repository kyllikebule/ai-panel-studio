<template>
  <div class="config-page">
    <header class="config-header">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h1>配置讨论</h1>
    </header>

    <el-form :model="form" label-position="top" class="config-form">
      <!-- 议题输入 -->
      <el-form-item label="讨论议题">
        <el-input
          v-model="form.topic"
          placeholder="输入讨论主题，如：AI 是否应该被严格监管？"
          size="large"
        />
      </el-form-item>

      <!-- 主持人配置 -->
      <el-form-item label="主持人名称">
        <el-input v-model="form.hostName" placeholder="如：张主持人" />
      </el-form-item>
      <el-form-item label="主持风格 Prompt">
        <el-input
          v-model="form.hostPrompt"
          type="textarea"
          :rows="2"
          placeholder="描述主持人的风格..."
        />
      </el-form-item>

      <!-- 轮次 -->
      <el-form-item label="讨论轮次">
        <el-slider v-model="form.maxRounds" :min="2" :max="10" show-stops :marks="roundMarks" />
      </el-form-item>

      <!-- 嘉宾选择 -->
      <el-form-item label="选择嘉宾">
        <div class="guest-grid">
          <div
            class="guest-select-card"
            v-for="g in guestStore.guestTemplates"
            :key="g.id"
            :class="{ selected: selectedGuestIds.includes(g.id) }"
            @click="toggleGuest(g.id)"
          >
            <div class="guest-avatar">{{ g.name[0] }}</div>
            <div class="guest-name">{{ g.name }}</div>
            <div class="guest-style">{{ g.speak_style || g.persona }}</div>
          </div>
        </div>
      </el-form-item>

      <!-- 已选嘉宾预览 -->
      <el-form-item label="已选嘉宾 ({{ selectedGuestIds.length }}人)">
        <div class="preview-list">
          <div class="preview-card" v-for="g in selectedGuests" :key="g.id">
            <span class="preview-name">{{ g.name }}</span>
            <span class="preview-persona">{{ g.persona }}</span>
            <el-button text type="danger" size="small" @click.stop="toggleGuest(g.id)">移除</el-button>
          </div>
        </div>
      </el-form-item>

      <!-- 提交 -->
      <el-button
        type="primary"
        size="large"
        :disabled="!canStart"
        :loading="submitting"
        @click="startDiscussion"
      >
        进入演播厅
      </el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'
import { useGuestStore } from '@/stores/guest'

const router = useRouter()
const discussionStore = useDiscussionStore()
const guestStore = useGuestStore()
const submitting = ref(false)
const selectedGuestIds = ref<number[]>([])

const form = reactive({
  topic: '',
  hostName: '张主持人',
  hostPrompt: '你是专业讨论主持人，保持中立，用标准中文开场、追问、串联、总结。',
  maxRounds: 5,
})

const roundMarks = {
  2: '2轮',
  5: '5轮',
  8: '8轮',
  10: '10轮',
}

const canStart = computed(() => form.topic.trim() && selectedGuestIds.value.length >= 2)

const selectedGuests = computed(() =>
  guestStore.guestTemplates.filter(g => selectedGuestIds.value.includes(g.id))
)

function toggleGuest(id: number) {
  const idx = selectedGuestIds.value.indexOf(id)
  if (idx >= 0) {
    selectedGuestIds.value.splice(idx, 1)
  } else {
    selectedGuestIds.value.push(id)
  }
}

async function startDiscussion() {
  submitting.value = true
  try {
    const discussion = await discussionStore.createDiscussion({
      topic: form.topic,
      host: {
        name: form.hostName,
        system_prompt: form.hostPrompt,
      },
      max_rounds: form.maxRounds,
    })
    // 逐个添加嘉宾
    for (const guestId of selectedGuestIds.value) {
      await fetch(`/api/discussions/${discussion.id}/guests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_id: guestId }),
      })
    }
    router.push(`/studio/${discussion.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  guestStore.fetchGuests()
})
</script>

<style scoped>
.config-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 24px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.config-header h1 {
  margin: 0;
  font-size: 24px;
}

.config-form {
  background: var(--color-bg-card);
  backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: 32px;
}

.guest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  width: 100%;
}

.guest-select-card {
  text-align: center;
  padding: 16px 12px;
  border: 2px solid transparent;
  border-radius: var(--card-radius);
  background: rgba(0, 212, 255, 0.05);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.guest-select-card.selected {
  border-color: var(--color-accent-cyan);
  background: rgba(0, 212, 255, 0.15);
}

.guest-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent-gold);
  color: #000;
  font-size: 20px;
  font-weight: bold;
  line-height: 48px;
  margin: 0 auto 8px;
}

.guest-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.guest-style {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 8px;
}

.preview-name {
  font-weight: 600;
  min-width: 80px;
}

.preview-persona {
  flex: 1;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}
</style>
