<template>
  <div
    class="chat-message"
    :class="[roleClass, { streaming: isStreaming }]"
    :style="{ '--sender-color': senderColor }"
  >
    <div class="msg-header">
      <span class="msg-sender">{{ senderName }}</span>
      <span class="msg-time">{{ time }}</span>
    </div>
    <p class="msg-content">
      {{ content }}<span v-if="isStreaming" class="cursor-blink">|</span>
    </p>
    <div class="msg-footer">
      <span class="msg-index">#{{ seqNum }}</span>
      <span v-if="tokenCount" class="msg-tokens">{{ tokenCount }} tokens</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  senderName: string
  senderRole: 'host' | 'guest' | 'system'
  content: string
  senderColor: string
  seqNum: number
  tokenCount?: number
  time?: string
  isStreaming?: boolean
}>()

const roleClass = computed(() => `role-${props.senderRole}`)
</script>

<style scoped>
.chat-message {
  padding: 12px var(--card-padding, 16px);
  margin-bottom: 8px;
  border-radius: var(--pr-radius-md, 8px);
  border-left: 3px solid var(--sender-color);
  background: rgba(255, 255, 255, 0.04);
  transition: border-color var(--pr-duration-normal, 250ms) ease-out;
}

.chat-message.role-host {
  border-left-color: var(--color-role-host, #f0b90b);
  background: rgba(240, 185, 11, 0.06);
}

.chat-message.role-system {
  border-left-color: var(--color-text-muted, #6b7280);
  background: rgba(107, 114, 128, 0.06);
}

.chat-message.streaming {
  border-left-color: var(--color-accent, #00d4ff);
}

.msg-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.msg-sender {
  font-size: var(--pr-font-size-small, 12px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--sender-color);
}

.msg-time {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
}

.msg-content {
  margin: 0;
  font-size: var(--pr-font-size-body, 14px);
  line-height: 1.6;
  color: var(--color-text-primary, #e5e7eb);
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor-blink {
  display: inline;
  animation: blink 1s step-end infinite;
  color: var(--color-accent, #00d4ff);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}

.msg-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.msg-index,
.msg-tokens {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
}
</style>
