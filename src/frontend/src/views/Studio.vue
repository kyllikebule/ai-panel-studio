<template>
  <div class="studio-page">
    <!-- ═══ 顶部栏 ═══ -->
    <header class="studio-topbar">
      <el-button text @click="$router.push('/')">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <h2 class="studio-topic">{{ topic }}</h2>
      <span class="studio-round">第 {{ currentRound }} / {{ maxRounds }} 轮</span>
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
import { ref, nextTick, watch } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import ChatMessage from '@/components/ChatMessage.vue'
import GuestCard from '@/components/GuestCard.vue'
import OpinionItem from '@/components/OpinionItem.vue'

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
// 讨论元信息
// ═══════════════════════════════════════
const topic = ref('AI 是否应该被严格监管？')
const currentRound = ref(2)
const maxRounds = ref(5)
const speakingIndex = ref<number | null>(0)
const summaryReady = ref(false)
const summaryText = ref('')
const transcriptRef = ref<HTMLElement | null>(null)

// ═══════════════════════════════════════
// 消息列表（静态演示数据）
// ═══════════════════════════════════════
interface StudioMessage {
  id: number
  senderName: string
  senderRole: 'host' | 'guest' | 'system'
  content: string
  senderColor: string
  seqNum: number
  tokenCount?: number
  time: string
  isStreaming?: boolean
}

const messages = ref<StudioMessage[]>([
  {
    id: 1, senderName: '张主持人', senderRole: 'host',
    content: '各位嘉宾好，今天我们讨论的主题是"AI 是否应该被严格监管"。这是一个备受关注的话题，让我们先请李教授谈谈您的看法。',
    senderColor: ROLE_COLORS[0], seqNum: 1, tokenCount: 68, time: '14:00',
  },
  {
    id: 2, senderName: '李教授', senderRole: 'guest',
    content: '谢谢主持人。我认为对于高风险 AI 应用，严格的监管是必要的。医疗诊断、自动驾驶等领域涉及生命安全，我们不能让算法在黑箱中做出可能致命的决策。',
    senderColor: ROLE_COLORS[1], seqNum: 2, tokenCount: 82, time: '14:02',
  },
  {
    id: 3, senderName: '王博士', senderRole: 'guest',
    content: '我理解李教授的担忧，但也想提醒大家——过度监管可能会扼杀创新。AI 的发展速度极快，如果监管框架过于僵化，优秀的初创公司可能根本没有资源来满足复杂的合规要求。',
    senderColor: ROLE_COLORS[2], seqNum: 3, tokenCount: 91, time: '14:04',
  },
  {
    id: 4, senderName: '张律师', senderRole: 'guest',
    content: '从法律实务角度看，目前最大的问题不是"要不要监管"，而是"如何监管"。我们需要分层分级的监管体系——对高风险应用严格审批，对低风险应用备案即可。这样既保护了公众安全，也给创新留出了空间。',
    senderColor: ROLE_COLORS[3], seqNum: 4, tokenCount: 105, time: '14:06',
  },
  {
    id: 5, senderName: '张主持人', senderRole: 'host',
    content: '张律师提出了一个很好的中间路径——分层分级监管。赵研究员，您在产业政策方面有深入研究，您怎么看这种"按风险等级分级管理"的思路？',
    senderColor: ROLE_COLORS[0], seqNum: 5, tokenCount: 72, time: '14:08',
  },
  {
    id: 6, senderName: '赵研究员', senderRole: 'guest',
    content: '分级管理的思路是可行的。欧盟的 AI Act 就是按照风险等级来分类监管的。我们可以借鉴，但要结合中国的产业特点。建议将监管重点放在算法的可解释性和数据的合规性上，而不是过度的前置审批。',
    senderColor: ROLE_COLORS[4], seqNum: 6, tokenCount: 97, time: '14:10',
  },
])

// ═══════════════════════════════════════
// 嘉宾列表
// ═══════════════════════════════════════
interface StudioGuest {
  name: string
  profession: string
  thinkSummary?: string
}

const guests = ref<StudioGuest[]>([
  { name: '张主持人', profession: '资深媒体人 / 讨论主持', thinkSummary: '正在引导嘉宾讨论监管分层问题' },
  { name: '李教授', profession: 'AI 伦理学专家', thinkSummary: '强调高风险 AI 的安全底线' },
  { name: '王博士', profession: '计算机科学家 / 技术乐观派', thinkSummary: '担忧过度监管抑制创新' },
  { name: '张律师', profession: '科技法律顾问', thinkSummary: '主张分层分级监管框架' },
  { name: '赵研究员', profession: '产业政策研究员', thinkSummary: '建议聚焦可解释性与合规' },
])

// ═══════════════════════════════════════
// 观点列表
// ═══════════════════════════════════════
interface StudioOpinion {
  id: number
  category: 'consensus' | 'disagreement' | 'neutral'
  stanceSummary: string
  confidence: number
  evidence?: string
}

const opinions = ref<StudioOpinion[]>([
  {
    id: 1, category: 'consensus',
    stanceSummary: '各方均认同对高风险 AI 应用需要进行某种形式的监管',
    confidence: 0.92,
    evidence: '严格监管是必要的...涉及生命安全',
  },
  {
    id: 2, category: 'disagreement',
    stanceSummary: '监管的力度和范围存在分歧——从严格审批到备案制',
    confidence: 0.85,
    evidence: '过度监管可能会扼杀创新...分层分级监管',
  },
  {
    id: 3, category: 'consensus',
    stanceSummary: '倾向借鉴欧盟 AI Act 的分级监管框架',
    confidence: 0.78,
    evidence: '欧盟的 AI Act 就是按照风险等级来分类监管的',
  },
])

// ═══════════════════════════════════════
// 自动滚动
// ═══════════════════════════════════════
watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    const el = transcriptRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  },
)
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
