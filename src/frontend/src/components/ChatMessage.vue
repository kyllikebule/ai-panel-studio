<template>
  <div class="chat-message" :class="{ host: message.role === 'host', streaming: isStreaming }">
    <div class="msg-header">
      <span class="msg-sender" :style="{ color: senderColor }">
        {{ message.sender_name || (message.role === 'host' ? '主持人' : '嘉宾') }}
      </span>
      <span class="msg-seq">#{{ message.seq_num }}</span>
    </div>
    <div class="msg-content">{{ message.content }}<span v-if="isStreaming" class="cursor-blink">|</span></div>
    <div class="msg-footer">
      <span class="msg-tokens">{{ message.token_count }} tokens</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: {
    id: number
    role: string
    content: string
    sender_name?: string
    seq_num: number
    token_count?: number
  }
  senderColor: string
  isStreaming: boolean
}>()
</script>

<style scoped>
.chat-message {
  padding: 12px var(--card-padding);
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border-left: 3px solid transparent;
}

.chat-message.host {
  border-left-color: var(--color-role-host);
  background: rgba(240, 185, 11, 0.06);
}

.chat-message.streaming {
  border-left-color: var(--color-accent-cyan);
}

.msg-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.msg-sender {
  font-weight: 600;
  font-size: var(--font-size-small);
}

.msg-seq {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.msg-content {
  font-size: var(--font-size-body);
  line-height: 1.6;
  color: var(--color-text-primary);
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: var(--color-accent-cyan);
}

.msg-footer {
  margin-top: 8px;
}

.msg-tokens {
  font-size: 11px;
  color: var(--color-text-secondary);
}
</style>
