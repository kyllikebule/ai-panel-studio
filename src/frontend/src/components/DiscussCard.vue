<template>
  <div class="discuss-card" @click="$emit('click')">
    <div class="card-left">
      <h3 class="card-topic">{{ discussion.topic }}</h3>
      <div class="card-meta">
        <span class="meta-host">主持人：{{ discussion.hostName }}</span>
        <span class="meta-round">轮次：{{ discussion.currentRound }}/{{ discussion.maxRounds }}</span>
        <span class="meta-guests">{{ discussion.guestCount }} 位嘉宾</span>
      </div>
    </div>
    <div class="card-right">
      <el-tag
        :type="statusMap[discussion.status]?.type ?? 'info'"
        size="small"
        effect="dark"
      >
        {{ statusMap[discussion.status]?.label ?? discussion.status }}
      </el-tag>
      <span class="card-time">{{ discussion.createdAt }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface DiscussionItem {
  id: number
  topic: string
  hostName: string
  status: 'pending' | 'active' | 'paused' | 'completed'
  currentRound: number
  maxRounds: number
  guestCount: number
  createdAt: string
}

defineProps<{
  discussion: DiscussionItem
}>()

defineEmits<{
  click: []
}>()

const statusMap: Record<string, { label: string; type: 'info' | 'warning' | 'success' }> = {
  pending:   { label: '待开始', type: 'info' },
  active:    { label: '进行中', type: 'warning' },
  paused:    { label: '已暂停', type: 'info' },
  completed: { label: '已完成', type: 'success' },
}
</script>

<style scoped>
.discuss-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--card-padding);
  background: var(--card-bg);
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  cursor: pointer;
  transition:
    transform var(--pr-duration-fast, 150ms) ease-out,
    box-shadow var(--pr-duration-fast, 150ms) ease-out;
}

.discuss-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--card-shadow-hover);
}

.discuss-card:focus-visible {
  outline: 2px solid var(--color-accent, #00d4ff);
  outline-offset: 2px;
}

.card-left {
  flex: 1;
  min-width: 0;
}

.card-topic {
  margin: 0 0 8px;
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-secondary);
}

.card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.card-time {
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-muted);
}
</style>
