<template>
  <div class="home-page">
    <header class="home-header">
      <h1 class="home-title">AI Panel Studio</h1>
      <p class="home-subtitle">圆桌演播厅 · 专家讨论</p>
      <el-button type="primary" size="large" @click="$router.push('/config')">
        <el-icon><Plus /></el-icon> 新建讨论
      </el-button>
    </header>

    <section class="discussion-list" v-loading="loading">
      <div
        class="discussion-card"
        v-for="d in store.discussions"
        :key="d.id"
        @click="$router.push(`/studio/${d.id}`)"
      >
        <div class="card-left">
          <h3 class="card-topic">{{ d.topic }}</h3>
          <div class="card-meta">
            <span>主持人：{{ d.host_name }}</span>
            <span>轮次：{{ d.current_round }}/{{ d.max_rounds }}</span>
          </div>
        </div>
        <div class="card-right">
          <el-tag
            :type="statusMap[d.status]?.type"
            size="small"
          >
            {{ statusMap[d.status]?.label }}
          </el-tag>
          <span class="card-time">{{ formatTime(d.created_at) }}</span>
        </div>
      </div>
      <el-empty v-if="!loading && store.discussions.length === 0" description="暂无讨论，点击上方按钮创建" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useDiscussionStore } from '@/stores/discussion'

const store = useDiscussionStore()
const loading = ref(false)

const statusMap: Record<string, { label: string; type: 'info' | 'warning' | 'success' }> = {
  pending: { label: '待开始', type: 'info' },
  active: { label: '进行中', type: 'warning' },
  paused: { label: '已暂停', type: 'info' },
  completed: { label: '已完成', type: 'success' },
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  await store.fetchDiscussions()
  loading.value = false
})
</script>

<style scoped>
.home-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px;
}

.home-header {
  text-align: center;
  margin-bottom: 40px;
}

.home-title {
  font-size: 32px;
  color: var(--color-accent);
  margin: 0 0 8px;
}

.home-subtitle {
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

.discussion-list {
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}

.discussion-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--card-padding);
  background: var(--color-bg-card);
  backdrop-filter: var(--card-backdrop);
  border: var(--card-border);
  border-radius: var(--card-radius);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.discussion-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 24px rgba(0, 212, 255, 0.25);
}

.card-topic {
  margin: 0 0 8px;
  font-size: 16px;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.card-time {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}
</style>
