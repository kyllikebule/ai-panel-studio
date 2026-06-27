<template>
  <div class="studio-page">
    <!-- 顶部栏 -->
    <header class="studio-topbar">
      <el-button text @click="$router.push('/')">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h2 class="studio-topic">{{ store.currentDiscussion?.topic }}</h2>
      <div class="studio-actions">
        <el-button
          v-if="status === 'pending'"
          type="primary"
          @click="sendAction('start')"
        >
          开始讨论
        </el-button>
        <el-button
          v-if="status === 'active'"
          @click="sendAction('pause')"
        >
          暂停
        </el-button>
        <el-button
          v-if="status === 'paused'"
          type="success"
          @click="sendAction('resume')"
        >
          恢复
        </el-button>
        <el-button
          v-if="status === 'active' || status === 'paused'"
          type="danger"
          @click="sendAction('stop')"
        >
          结束
        </el-button>
      </div>
    </header>

    <!-- 2×2 Grid 四分区 -->
    <div class="studio-grid">
      <!-- 左上：圆桌参会面板 -->
      <section class="grid-panel panel-guests">
        <h4 class="panel-title">🎙️ 参会嘉宾</h4>
        <div class="panel-scroll">
          <GuestCard
            v-for="(g, idx) in guests"
            :key="g.id"
            :guest="g"
            :is-active="true"
            :is-speaking="speakingGuestId === g.id"
            :color-theme="guestColors[idx % guestColors.length]"
          />
        </div>
      </section>

      <!-- 右上：主题 & 议题面板 -->
      <section class="grid-panel panel-topics">
        <h4 class="panel-title">📋 讨论议题</h4>
        <div class="panel-scroll">
          <div class="topic-item current">
            <el-tag type="primary" size="small">当前</el-tag>
            <span>{{ store.currentDiscussion?.topic }}</span>
          </div>
          <div class="topic-item">
            <el-tag size="small">轮次 {{ round }}/{{ store.currentDiscussion?.max_rounds }}</el-tag>
          </div>
          <el-empty v-if="!store.currentDiscussion" description="加载中..." :image-size="60" />
        </div>
      </section>

      <!-- 左下：实时对话流 -->
      <section class="grid-panel panel-chat">
        <h4 class="panel-title">💬 讨论记录</h4>
        <div class="panel-scroll" ref="chatScrollRef">
          <ChatMessage
            v-for="msg in store.messages"
            :key="msg.id"
            :message="{
              id: msg.id,
              role: msg.role,
              content: msg.content,
              sender_name: msg.role === 'host' ? '主持人' : ('嘉宾#' + msg.guest_id),
              seq_num: msg.seq_num,
              token_count: msg.token_count,
            }"
            :sender-color="msg.role === 'host' ? '#f0b90b' : '#3b82f6'"
            :is-streaming="false"
          />
          <el-empty v-if="store.messages.length === 0" description="暂无消息" :image-size="60" />
        </div>
      </section>

      <!-- 右下：观点面板 -->
      <section class="grid-panel panel-opinions">
        <h4 class="panel-title">🔍 观点共识 & 分歧</h4>
        <OpinionPanel :opinions="store.opinions" :loading="false" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'
import GuestCard from '@/components/GuestCard.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import OpinionPanel from '@/components/OpinionPanel.vue'

const route = useRoute()
const router = useRouter()
const store = useDiscussionStore()

const status = ref('pending')
const round = ref(0)
const speakingGuestId = ref<number | null>(null)
const chatScrollRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

const guestColors = [
  '#3b82f6', // blue
  '#10b981', // green
  '#a855f7', // purple
  '#f97316', // orange
  '#ec4899', // pink
  '#06b6d4', // cyan
]

const guests = computed(() => {
  const d = store.currentDiscussion
  if (!d || !('guests' in d)) return []
  return (d as any).guests || []
})

function sendAction(action: string) {
  ws?.send(JSON.stringify({ action }))
}

function connectWS() {
  const discussionId = route.params.discussionId
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/discussion/${discussionId}`)

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    switch (data.event) {
      case 'host_speak':
      case 'guest_speak':
        store.messages.push({
          id: Date.now(),
          role: data.event === 'host_speak' ? 'host' : 'guest',
          content: data.content,
          guest_id: data.guest_id,
          seq_num: data.seq_num,
          token_count: 0,
        })
        speakingGuestId.value = data.guest_id || null
        nextTick(() => {
          if (chatScrollRef.value) {
            chatScrollRef.value.scrollTop = chatScrollRef.value.scrollHeight
          }
        })
        break
      case 'speak_done':
        speakingGuestId.value = null
        break
      case 'opinion_extracted':
        store.opinions.push(data)
        break
      case 'round_change':
        round.value = data.round
        break
      case 'discussion_end':
        status.value = 'completed'
        break
      case 'system':
        if (data.message?.includes('已开始')) status.value = 'active'
        if (data.message?.includes('已暂停')) status.value = 'paused'
        if (data.message?.includes('已恢复')) status.value = 'active'
        if (data.message?.includes('已结束')) status.value = 'completed'
        break
    }
  }
}

onMounted(async () => {
  const id = Number(route.params.discussionId)
  await store.loadDiscussion(id)
  await store.fetchDiscussions() // 获取讨论内消息
  connectWS()
})

onUnmounted(() => {
  ws?.close()
})
</script>

<style scoped>
.studio-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.studio-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.studio-topic {
  flex: 1;
  margin: 0;
  font-size: 18px;
  color: var(--color-accent-cyan);
}

.studio-actions {
  display: flex;
  gap: 8px;
}

.studio-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  grid-template-rows: 1fr 1fr;
  gap: var(--grid-gap);
  background: var(--grid-divider);
  overflow: hidden;
}

@media (max-width: 1439px) {
  .studio-grid {
    grid-template-columns: 250px 1fr;
  }
}

@media (max-width: 767px) {
  .studio-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow-y: auto;
  }
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.panel-guests .panel-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-item.current {
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
}
</style>
