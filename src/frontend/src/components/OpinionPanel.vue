<template>
  <div class="opinion-panel">
    <h4 class="panel-title">观点汇总</h4>
    <div v-if="loading" class="loading">分析中...</div>
    <div v-else-if="opinions.length === 0" class="empty">暂无观点</div>
    <div
      v-for="op in opinions"
      :key="op.id"
      class="opinion-item"
      :class="'category-' + op.category"
    >
      <div class="opinion-header">
        <el-tag
          :type="categoryTagType(op.category)"
          size="small"
        >
          {{ categoryLabel(op.category) }}
        </el-tag>
        <span v-if="op.confidence" class="confidence">
          置信度 {{ (op.confidence * 100).toFixed(0) }}%
        </span>
      </div>
      <p class="opinion-summary">{{ op.stance_summary }}</p>
      <blockquote v-if="op.evidence" class="opinion-evidence">
        "{{ op.evidence }}"
      </blockquote>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  opinions: Array<{
    id: number
    stance_summary: string
    category: string
    confidence: number | null
    evidence: string | null
  }>
  loading: boolean
}>()

function categoryLabel(cat: string) {
  const map: Record<string, string> = {
    consensus: '共识',
    disagreement: '分歧',
    neutral: '中立',
  }
  return map[cat] || cat
}

function categoryTagType(cat: string): 'success' | 'danger' | 'info' {
  if (cat === 'consensus') return 'success'
  if (cat === 'disagreement') return 'danger'
  return 'info'
}
</script>

<style scoped>
.opinion-panel {
  height: 100%;
  overflow-y: auto;
  padding: var(--card-padding);
}

.panel-title {
  margin: 0 0 12px;
  font-size: var(--font-size-title);
}

.loading, .empty {
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  padding: 24px 0;
  text-align: center;
}

.opinion-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  background: rgba(255, 255, 255, 0.04);
}

.category-consensus {
  border-left-color: var(--color-consensus);
  background: rgba(16, 185, 129, 0.06);
}

.category-disagreement {
  border-left-color: var(--color-disagreement);
  background: rgba(239, 68, 68, 0.06);
}

.category-neutral {
  border-left-color: var(--color-neutral);
  background: rgba(107, 114, 128, 0.06);
}

.opinion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.confidence {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.opinion-summary {
  margin: 0 0 8px;
  font-size: var(--font-size-body);
  line-height: 1.5;
}

.opinion-evidence {
  margin: 0;
  padding: 6px 10px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  font-style: italic;
}
</style>
