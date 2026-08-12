import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,

      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
          meta: {
            title: '首页',
          },
        },
        {
          path: 'ratingItem',
          name: 'ratingItem',
          component: () => import('@/views/rating/RatingItem.vue'),
          meta: {
            title: '评分项目',
          },
        },
        {
          path: 'setting',
          name: 'setting',
          component: () => import('@/views/SettingView.vue'),
          meta: {
            title: '网页设置',
          },
        },
      ],
    },
  ],
})

export default router
