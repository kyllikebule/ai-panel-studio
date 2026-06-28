<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <header class="home-topbar">
      <div class="topbar-left">
        <span class="topbar-logo">APS</span>
        <h1 class="topbar-title">AI Panel Studio</h1>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/create-discuss')">
        <el-icon><Plus /></el-icon>
        新建讨论
      </el-button>
    </header>

    <!-- 页面主体 -->
    <main class="home-body">
      <!-- 页面标题区 -->
      <section class="home-hero">
        <h2 class="hero-title">圆桌演播厅</h2>
        <p class="hero-subtitle">AI 专家圆桌辩论直播间 — 创建讨论，邀请嘉宾，观摩思想交锋</p>
      </section>

      <!-- 讨论列表 -->
      <section class="discussion-section">
        <div class="section-header">
          <h3 class="section-title">讨论列表</h3>
          <span class="section-count" v-if="discussions.length">{{ discussions.length }} 场讨论</span>
        </div>

        <div v-if="discussions.length" class="discussion-list">
          <DiscussCard
            v-for="d in discussions"
            :key="d.id"
            :discussion="d"
            @click="$router.push(`/studio/${d.id}`)"
          />
        </div>

        <el-empty
          v-else
          description="暂无讨论，点击上方按钮创建第一场讨论"
          :image-size="80"
        />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import DiscussCard from '@/components/DiscussCard.vue'
import type { DiscussionItem } from '@/components/DiscussCard.vue'
import { useDiscussionStore } from '@/stores/discussion'

const store = useDiscussionStore()
const discussions = ref<DiscussionItem[]>([])

onMounted(async () => {
  await store.fetchDiscussions()
  discussions.value = store.discussions.map(d => ({
    id: d.id,
    topic: d.topic,
    hostName: d.host_name,
    status: d.status as DiscussionItem['status'],
    currentRound: d.current_round,
    maxRounds: d.max_rounds,
    guestCount: d.guest_count ?? 0,
    createdAt: d.created_at?.slice(0, 10) ?? '',
  }))
})
</script>

<style scoped>
/* ═══════════════════════════════════════════
   页面布局
   ═══════════════════════════════════════════ */
.home-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

/* ══ 顶部导航栏 ══ */
.home-topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: var(--color-bg-secondary);
  border-bottom: var(--grid-divider, 1px solid rgba(0,212,255,0.15));
  backdrop-filter: var(--card-backdrop);
  -webkit-backdrop-filter: var(--card-backdrop);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--pr-radius-md, 8px);
  background: var(--color-accent);
  color: var(--color-text-inverse);
  font-weight: var(--pr-font-weight-bold, 700);
  font-size: 14px;
  letter-spacing: 0.5px;
}

.topbar-title {
  margin: 0;
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
}

/* ══ 页面主体 ══ */
.home-body {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px;
}

/* ══ Hero 区 ══ */
.home-hero {
  text-align: center;
  margin-bottom: var(--spacing-section, 24px);
}

.hero-title {
  margin: 0 0 8px;
  font-size: var(--pr-font-size-h1, 32px);
  font-weight: var(--pr-font-weight-bold, 700);
  color: var(--color-accent);
}

.hero-subtitle {
  margin: 0;
  font-size: var(--pr-font-size-body, 14px);
  color: var(--color-text-secondary);
  line-height: var(--pr-line-height-body, 1.6);
}

/* ══ 讨论列表区 ══ */
.discussion-section {
  margin-top: var(--spacing-section, 24px);
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: var(--card-gap, 12px);
}

.section-title {
  margin: 0;
  font-size: var(--pr-font-size-h3, 18px);
  font-weight: var(--pr-font-weight-semibold, 600);
  color: var(--color-text-primary);
}

.section-count {
  font-size: var(--pr-font-size-small, 12px);
  color: var(--color-text-muted);
}

.discussion-list {
  display: flex;
  flex-direction: column;
  gap: var(--card-gap, 12px);
}

/* ═══════════════════════════════════════════
   响应式
   ═══════════════════════════════════════════ */
@media (max-width: 767px) {
  .home-topbar {
    padding: 0 16px;
    height: 56px;
  }

  .home-body {
    padding: 24px 16px;
  }

  .hero-title {
    font-size: 24px;
  }

  .card-meta {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
