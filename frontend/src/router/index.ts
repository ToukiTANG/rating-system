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
          name: 'Home',
          component: () => import('@/views/HomeView.vue'),
          meta: {
            title: '首页',
          },
        },
        {
          path: 'RatingTopic',
          name: 'RatingTopic',
          component: () => import('@/views/rating/topic/RatingTopic.vue'),
          meta: {
            title: '评分主题',
          },
        },
        {
          path: 'RatingItem',
          name: 'RatingItem',
          component: () => import('@/views/rating/Item/RatingItem.vue'),
          meta: {
            title: '评分项目',
          },
        },
        {
          path: 'RatingResult',
          name: 'RatingResult',
          component: () => import('@/views/rating/result/RatingResult.vue'),
          meta: {
            title: '评分记录',
          },
        },
        {
          path: 'Setting',
          name: 'Setting',
          component: () => import('@/views/SettingView.vue'),
          meta: {
            title: '网页设置',
          },
        },
      ],
    },
    {
      path: '/Rating/:id',
      name: 'Rating',
      component: () => import('@/views/rating/RatingView.vue'),
      meta: {
        title: '评分',
      },
    },
    {
      path: '/score/topic/:topicId',
      name: 'SubmitRating',
      component: () => import('@/views/rating/SubmitRating.vue'),
    },
  ],
})

export default router
