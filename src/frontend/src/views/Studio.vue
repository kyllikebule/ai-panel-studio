<template>
  <div class="studio-page">
    <!-- ═══ 顶部栏 ═══ -->
    <header class="studio-topbar">
      <el-button text @click="$router.push('/')">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h2 class="studio-topic">{{ topic }}</h2>
      <span class="studio-round">第 {{ currentRound }} / {{ maxRounds }} 轮</span>
      <div class="studio-actions">
        <el-button
          v-if="status === 'idle'"
          type="primary" size="small"
          @click="ws?.send(JSON.stringify({action:'start'}))"
        >
          开始讨论
        </el-button>
        <el-button
          v-if="status === 'active'"
          size="small"
          @click="ws?.send(JSON.stringify({action:'stop'}))"
        >
          结束讨论
        </el-button>
        <el-tag v-if="status === 'done'" type="success" size="small">已完成</el-tag>
      </div>
    </header>

    <!-- ═══ 主体：左右分栏 + 底部总结 ═══ -->
    <div class="studio-body">
      <!-- 左栏 + 右栏 -->
      <div class="studio-main">
        <!-- 区域1：左侧 Transcript 主区 -->
        <section class="zone zone-transcript">
          <div class="zone-header">
            <span class="zone-title">💬 对话记录</span>
            <span class="zone-count">{{ messages.length }} 条</span>
          </div>
          <div class="zone-scroll" ref="transcriptRef">
            <ChatMessage
              v-for="msg in messages"
              :key="msg.id"
              :sender-name="msg.senderName"
              :sender-role="msg.senderRole"
              :content="msg.content"
              :sender-color="msg.senderColor"
              :seq-num="msg.seqNum"
              :token-count="msg.tokenCount"
              :time="msg.time"
              :is-streaming="msg.isStreaming"
            />
            <el-empty
              v-if="messages.length === 0"
              description="讨论即将开始..."
              :image-size="60"
            />
          </div>
        </section>

        <!-- 右侧上下两栏 -->
        <aside class="zone-right">
          <!-- 区域2：右上 嘉宾状态小窗 -->
          <section class="zone zone-guests">
            <div class="zone-header">
              <span class="zone-title">🎙️ 嘉宾状态</span>
            </div>
            <div class="zone-scroll">
              <GuestCard
                v-for="(g, idx) in guests"
                :key="idx"
                :guest="g"
                :is-speaking="speakingIndex === idx"
                :color-theme="ROLE_COLORS[idx]"
              />
              <el-empty
                v-if="guests.length === 0"
                description="暂无嘉宾"
                :image-size="50"
              />
            </div>
          </section>

          <!-- 区域3：右下 共识/分歧面板 -->
          <section class="zone zone-opinions">
            <div class="zone-header">
              <span class="zone-title">🔍 共识 & 分歧</span>
            </div>
            <div class="zone-scroll">
              <OpinionItem
                v-for="op in opinions"
                :key="op.id"
                :item="op"
              />
              <el-empty
                v-if="opinions.length === 0"
                description="暂无观点"
                :image-size="50"
              />
            </div>
          </section>
        </aside>
      </div>

      <!-- 区域4：底部 主持人总结 -->
      <section class="zone zone-summary">
        <div class="zone-header">
          <span class="zone-title">📋 主持人总结</span>
          <el-tag
            v-if="summaryReady"
            type="success"
            size="small"
            effect="dark"
          >
            已完成
          </el-tag>
        </div>
        <div class="zone-scroll summary-scroll">
          <p v-if="summaryText" class="summary-text">{{ summaryText }}</p>
          <el-empty
            v-else
            description="讨论结束后主持人将在此处总结"
            :image-size="50"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import ChatMessage from '@/components/ChatMessage.vue'
import GuestCard from '@/components/GuestCard.vue'
import OpinionItem from '@/components/OpinionItem.vue'

const route = useRoute()

// ═══════════════════════════════════════
// 角色色板
// ═══════════════════════════════════════
const ROLE_COLORS = [
  '#f0b90b', '#3b82f6', '#10b981', '#a855f7', '#f97316', '#00d4ff',
]

// ═══════════════════════════════════════
// 讨论状态
// ═══════════════════════════════════════
const topic = ref('AI 是否应该被严格监管？')
const currentRound = ref(0)
const maxRounds = ref(5)
const status = ref<'idle' | 'active' | 'done'>('idle')
const speakingIndex = ref<number | null>(null)
const summaryReady = ref(false)
const summaryText = ref('')
const transcriptRef = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null
let msgSeq = 0

// ═══════════════════════════════════════
// 数据容器（初始为空，由 WS 填充）
// ═══════════════════════════════════════
interface StudioMessage {
  id: number; senderName: string; senderRole: 'host'|'guest'|'system'
  content: string; senderColor: string; seqNum: number
  tokenCount?: number; time: string; isStreaming?: boolean
}
interface StudioGuest {
  name: string; profession: string; thinkSummary?: string
}
interface StudioOpinion {
  id: number; category: 'consensus'|'disagreement'|'neutral'
  stanceSummary: string; confidence: number; evidence?: string
}

const messages = ref<StudioMessage[]>([])
const guests = ref<StudioGuest[]>([])
const opinions = ref<StudioOpinion[]>([])

function now() { return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }

// ═══════════════════════════════════════
// WebSocket 连接 + 事件处理
// ═══════════════════════════════════════
function connectWS() {
  const discId = route.params.discId as string
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/discussion/${discId}`)

  ws.onopen = () => {
    ws?.send(JSON.stringify({ action: 'start' }))
  }

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    switch (data.event) {
      case 'system':
        if (data.message?.includes('已开始')) { status.value = 'active'; currentRound.value = 1 }
        break

      case 'guests_ready':
        guests.value = data.guests || []
        break

      case 'host_speak':
        msgSeq++
        messages.value.push({
          id: Date.now(), senderName: '主持人', senderRole: 'host',
          content: data.content, senderColor: ROLE_COLORS[0],
          seqNum: data.seq_num || msgSeq, time: now(),
        })
        scrollBottom()
        break

      case 'guest_speak':
        msgSeq++
        const gIdx = data.guest_id ?? 0
        messages.value.push({
          id: Date.now(), senderName: data.guest_name || '嘉宾', senderRole: 'guest',
          content: data.content, senderColor: ROLE_COLORS[gIdx + 1] || ROLE_COLORS[1],
          seqNum: data.seq_num || msgSeq, time: now(),
        })
        speakingIndex.value = gIdx
        scrollBottom()
        break

      case 'speak_done':
        speakingIndex.value = null
        break

      case 'token_stream':
        // 流式 token 仅做视觉占位，最终消息由 host_speak / guest_speak 推送
        break

      case 'opinion_extracted':
        opinions.value.push({
          id: data.opinion_id || Date.now(),
          category: data.category || 'neutral',
          stanceSummary: data.stance_summary || '',
          confidence: data.confidence ?? 0.5,
          evidence: data.evidence || null,
        })
        break

      case 'round_change':
        currentRound.value = data.round || currentRound.value
        break

      case 'discussion_end':
        status.value = 'done'
        summaryReady.value = true
        if (data.summary) summaryText.value = data.summary
        break

      case 'error':
        console.warn('WS error:', data.message)
        break
    }
  }

  ws.onerror = () => { /* 静默处理 */ }
  ws.onclose = () => { if (status.value === 'active') status.value = 'done' }
}

// ═══════════════════════════════════════
// 自动滚动
// ═══════════════════════════════════════
function scrollBottom() {
  nextTick(() => {
    const el = transcriptRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// ═══════════════════════════════════════
// 生命周期
// ═══════════════════════════════════════
onMounted(() => connectWS())
onUnmounted(() => ws?.close())
</script>

<style scoped>
/* ═══════════════════════════════════════
   页面根容器：100vh 禁止整页滚动
   ═══════════════════════════════════════ */
.studio-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary, #0a0e17);
  overflow: hidden;
}

/* ══ 顶部栏 ══ */
.studio-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  height: 52px;
  flex-shrink: 0;
  background: var(--color-bg-secondary, #111827);
  border-bottom: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
}

.studio-topic {
  flex: 1;
  margin: 0;
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-accent, #00d4ff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.studio-round {
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-muted, #6b7280);
  white-space: nowrap;
}

/* ═══════════════════════════════════════
   studio-body: flex:1 弹性填充
   ═══════════════════════════════════════ */
.studio-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ══ 左右分栏区域 ══ */
.studio-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ══ 区域1：左侧 Transcript ══ */
.zone-transcript {
  flex: 1;
  min-width: 0;
}

/* ══ 右侧双栏 ══ */
.zone-right {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-left: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
}

.zone-guests {
  flex: 1;
  min-height: 0;
}

.zone-opinions {
  flex: 1;
  min-height: 0;
  border-top: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
}

/* ══ 区域4：底部总结 ══ */
.zone-summary {
  flex-shrink: 0;
  max-height: 160px;
  border-top: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
}

.summary-scroll {
  max-height: 110px;
}

/* ═══════════════════════════════════════
   通用 Zone 面板
   ═══════════════════════════════════════ */
.zone {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary, #0a0e17);
  overflow: hidden;
}

.zone-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.zone-title {
  font-size: var(--pr-font-size-small, 12px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-secondary, #9ca3af);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.zone-count {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
}

.zone-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.10) transparent;
}

.zone-scroll::-webkit-scrollbar {
  width: 5px;
}

.zone-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.10);
  border-radius: 3px;
}

.zone-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* ══ 总结文字 ══ */
.summary-text {
  margin: 0;
  font-size: var(--pr-font-size-body, 14px);
  line-height: 1.6;
  color: var(--color-text-primary, #e5e7eb);
  white-space: pre-wrap;
}

/* ═══════════════════════════════════════
   响应式：窄屏
   ═══════════════════════════════════════ */
@media (max-width: 1023px) {
  .studio-main {
    flex-direction: column;
  }

  .zone-transcript {
    flex: 1;
  }

  .zone-right {
    width: 100%;
    flex-shrink: 1;
    flex-direction: row;
    max-height: 240px;
    border-left: none;
    border-top: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
  }

  .zone-guests,
  .zone-opinions {
    flex: 1;
    border-top: none;
  }

  .zone-opinions {
    border-left: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
  }

  .zone-summary {
    max-height: 120px;
  }

  .summary-scroll {
    max-height: 70px;
  }
}
</style>
