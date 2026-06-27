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
      path: '/create-discuss',
      name: 'create-discuss',
      component: () => import('@/views/CreateDiscuss.vue'),
    },
    {
      path: '/config/:discussionId?',
      name: 'config',
      component: () => import('@/views/GuestConfigPage.vue'),
    },
    {
      path: '/studio/:discId',
      name: 'studio',
      component: () => import('@/views/Studio.vue'),
    },
  ],
})

export default router
