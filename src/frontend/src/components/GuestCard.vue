<template>
  <div
    class="guest-card"
    :class="stateClass"
    :style="{ '--card-color': colorTheme }"
  >
    <div class="guest-avatar">{{ guest.name[0] }}</div>
    <div class="guest-body">
      <div class="guest-top">
        <span class="guest-name">{{ guest.name }}</span>
        <span class="guest-status" :class="statusClass">
          {{ statusLabel }}
        </span>
      </div>
      <span class="guest-profession">{{ guest.persona }}</span>
      <p v-if="guest.thinkSummary" class="guest-think">
        💭 {{ guest.thinkSummary }}
      </p>
    </div>
    <div v-if="speakingState !== 'idle'" class="speaking-dots">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  guest: {
    name: string
    persona: string
    thinkSummary?: string
  }
  speakingState: 'idle' | 'preparing' | 'speaking'
  colorTheme: string
}>()

const stateClass = computed(() => ({
  speaking: props.speakingState === 'speaking',
  preparing: props.speakingState === 'preparing',
  idle: props.speakingState === 'idle',
}))

const statusClass = computed(() => ({
  live: props.speakingState === 'speaking',
  preparing: props.speakingState === 'preparing',
  idle: props.speakingState === 'idle',
}))

const statusLabel = computed(() => {
  switch (props.speakingState) {
    case 'speaking': return '发言中'
    case 'preparing': return '准备中…'
    default: return '待机'
  }
})
</script>

<style scoped>
.guest-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--pr-radius-md, 8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  transition: border-color 0.3s, box-shadow 0.3s, background 0.3s;
}

.guest-card.speaking {
  border-color: var(--card-color);
  background: color-mix(in srgb, var(--card-color) 10%, transparent);
  box-shadow: 0 0 12px color-mix(in srgb, var(--card-color) 30%, transparent);
}

.guest-card.preparing {
  border-color: color-mix(in srgb, var(--card-color) 50%, transparent);
  background: color-mix(in srgb, var(--card-color) 5%, transparent);
  animation: pulse-border 1.2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: color-mix(in srgb, var(--card-color) 30%, transparent); }
  50%      { border-color: var(--card-color); }
}

.guest-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--pr-radius-full, 50%);
  background: var(--card-color);
  color: #000;
  font-weight: var(--pr-font-weight-bold, 700);
  font-size: 18px;
  line-height: 40px;
  text-align: center;
  flex-shrink: 0;
}

.guest-body {
  flex: 1;
  min-width: 0;
}

.guest-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.guest-name {
  font-size: var(--pr-font-size-body, 14px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary, #e5e7eb);
}

.guest-status {
  font-size: 11px;
  font-weight: var(--pr-font-weight-medium, 500);
  padding: 1px 6px;
  border-radius: var(--pr-radius-full, 9999px);
}

.guest-status.live {
  background: color-mix(in srgb, var(--card-color) 25%, transparent);
  color: var(--card-color);
}

.guest-status.preparing {
  background: color-mix(in srgb, var(--card-color) 15%, transparent);
  color: var(--card-color);
  animation: pulse-text 1.2s ease-in-out infinite;
}

.guest-status.idle {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-muted, #6b7280);
}

@keyframes pulse-text {
  0%, 100% { opacity: 0.6; }
  50%      { opacity: 1; }
}

.guest-profession {
  display: block;
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-secondary, #9ca3af);
  margin-bottom: 4px;
}

.guest-think {
  margin: 4px 0 0;
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-muted, #6b7280);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.speaking-dots {
  display: flex;
  gap: 3px;
  align-items: center;
  flex-shrink: 0;
  padding-top: 2px;
}

.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--card-color);
  animation: blink-dot 1s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink-dot {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%      { opacity: 1; transform: scale(1); }
}
</style>
