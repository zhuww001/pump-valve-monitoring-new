import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue')
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard/:device_id',
    name: 'DeviceDashboard',
    component: () => import('./views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/device-list',
    name: 'DeviceList',
    component: () => import('./views/DeviceList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('./views/History.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/history/:device_id',
    name: 'DeviceHistory',
    component: () => import('./views/History.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/warning',
    name: 'Warning',
    component: () => import('./views/Warning.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/warning/:device_id',
    name: 'DeviceWarning',
    component: () => import('./views/Warning.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data-source-config',
    name: 'DataSourceConfig',
    component: () => import('./views/DataSourceConfig.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/device-threshold-config',
    name: 'DeviceThresholdConfig',
    component: () => import('./views/DeviceThresholdConfig.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/gateway',
    name: 'GatewayMonitor',
    component: () => import('./views/GatewayMonitor.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system',
    name: 'System',
    component: () => import('./views/system/UserManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/user',
    name: 'UserManagement',
    component: () => import('./views/system/UserManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/role',
    name: 'RoleManagement',
    component: () => import('./views/system/RoleManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/menu',
    name: 'MenuManagement',
    component: () => import('./views/system/MenuManagement.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 检查是否登录
    const token = localStorage.getItem('token')
    if (!token) {
      next({ path: '/login' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
