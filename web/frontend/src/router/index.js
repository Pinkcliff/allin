import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue')
      },
      {
        path: 'fan',
        name: 'FanControl',
        component: () => import('@/views/fan/Index.vue')
      },
      {
        path: 'env',
        name: 'EnvControl',
        component: () => import('@/views/env/Index.vue')
      },
      {
        path: 'plc',
        name: 'PLCMonitor',
        component: () => import('@/views/plc/Index.vue')
      },
      {
        path: 'motion',
        name: 'MotionView',
        component: () => import('@/views/motion/Index.vue')
      },
      {
        path: 'sensor',
        name: 'SensorData',
        component: () => import('@/views/sensor/Index.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Index.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
