<template>
  <div class="opinion-item" :class="`category-${item.category}`">
    <div class="opinion-top">
      <el-tag
        :type="tagType"
        size="small"
        effect="dark"
      >
        {{ tagLabel }}
      </el-tag>
      <span v-if="hasConfidence" class="opinion-confidence">
        置信度 {{ (item.confidence * 100).toFixed(0) }}%
      </span>
    </div>
    <p class="opinion-summary">{{ item.stanceSummary }}</p>
    <blockquote v-if="item.evidence" class="opinion-evidence">
      "{{ item.evidence }}"
    </blockquote>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  item: {
    category: 'consensus' | 'disagreement' | 'neutral'
    stanceSummary: string
    confidence?: number | null
    evidence?: string | null
  }
}>()

const hasConfidence = computed(() => props.item.confidence != null)

const tagType = computed(() => {
  const map: Record<string, 'success' | 'danger' | 'info'> = {
    consensus: 'success',
    disagreement: 'danger',
    neutral: 'info',
  }
  return map[props.item.category]
})

const tagLabel = computed(() => {
  const map: Record<string, string> = {
    consensus: '共识',
    disagreement: '分歧',
    neutral: '中立',
  }
  return map[props.item.category]
})
</script>

<style scoped>
.opinion-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: var(--pr-radius-md, 8px);
  border-left: 3px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  animation: fade-in 200ms ease-out;
}

.category-consensus {
  border-left-color: var(--color-consensus, #10b981);
  background: rgba(16, 185, 129, 0.06);
}

.category-disagreement {
  border-left-color: var(--color-disagreement, #ef4444);
  background: rgba(239, 68, 68, 0.06);
}

.category-neutral {
  border-left-color: var(--color-neutral, #6b7280);
  background: rgba(107, 114, 128, 0.06);
}

.opinion-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.opinion-confidence {
  font-size: 11px;
  color: var(--color-text-muted, #6b7280);
}

.opinion-summary {
  margin: 0 0 6px;
  font-size: var(--pr-font-size-body, 14px);
  line-height: 1.5;
  color: var(--color-text-primary, #e5e7eb);
}

.opinion-evidence {
  margin: 0;
  padding: 4px 8px;
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-secondary, #9ca3af);
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  font-style: italic;
  line-height: 1.4;
}

@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
</style>
