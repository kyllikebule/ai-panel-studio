import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/Home.vue'),
    },
    {
      path: '/config/:discussionId?',
      name: 'config',
      component: () => import('@/views/GuestConfigPage.vue'),
    },
    {
      path: '/studio/:discussionId',
      name: 'studio',
      component: () => import('@/views/StudioPage.vue'),
    },
  ],
})

export default router
