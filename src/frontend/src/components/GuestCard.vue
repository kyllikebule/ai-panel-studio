<template>
  <div
    class="guest-card"
    :class="{ active: isActive, speaking: isSpeaking }"
    :style="{ '--card-color': colorTheme }"
  >
    <div class="guest-card-avatar">{{ guest.name[0] }}</div>
    <div class="guest-card-info">
      <div class="guest-card-name">{{ guest.name }}</div>
      <div class="guest-card-role">{{ guest.speak_style || guest.persona }}</div>
    </div>
    <div v-if="isSpeaking" class="speaking-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
    <el-tag v-if="!isActive" size="small" type="info">离线</el-tag>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  guest: { id: number; name: string; avatar?: string | null; persona: string; speak_style?: string }
  isActive: boolean
  isSpeaking: boolean
  colorTheme: string
}>()
</script>

<style scoped>
.guest-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px var(--card-padding);
  border-radius: var(--card-radius);
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.04);
  transition: border-color 0.3s, box-shadow 0.3s;
}

.guest-card.active {
  border-color: var(--card-color);
  background: color-mix(in srgb, var(--card-color) 8%, transparent);
}

.guest-card.speaking {
  border-color: var(--card-color);
  box-shadow: 0 0 16px color-mix(in srgb, var(--card-color) 40%, transparent);
  animation: pulse-glow 1.5s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 8px color-mix(in srgb, var(--card-color) 20%, transparent); }
  50% { box-shadow: 0 0 20px color-mix(in srgb, var(--card-color) 50%, transparent); }
}

.guest-card-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--card-color);
  color: #000;
  font-weight: bold;
  font-size: 18px;
  line-height: 40px;
  text-align: center;
  flex-shrink: 0;
}

.guest-card-info {
  flex: 1;
  min-width: 0;
}

.guest-card-name {
  font-weight: 600;
  font-size: 14px;
}

.guest-card-role {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.speaking-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--card-color);
  animation: blink 1s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
