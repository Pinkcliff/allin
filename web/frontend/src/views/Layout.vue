<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-name">WindField</span>
          <span class="brand-sub">Digital Twin</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section-title">监控中心</div>
        <router-link to="/dashboard" class="nav-item">
          <div class="nav-icon"><Monitor /></div>
          <span>监控大屏</span>
        </router-link>
        <router-link to="/fan" class="nav-item">
          <div class="nav-icon"><View /></div>
          <span>风扇控制</span>
        </router-link>

        <div class="nav-section-title">设备控制</div>
        <router-link to="/env" class="nav-item">
          <div class="nav-icon"><Sunny /></div>
          <span>环境控制</span>
        </router-link>
        <router-link to="/plc" class="nav-item">
          <div class="nav-icon"><Link /></div>
          <span>PLC监控</span>
        </router-link>

        <div class="nav-section-title">数据采集</div>
        <router-link to="/motion" class="nav-item">
          <div class="nav-icon"><VideoCamera /></div>
          <span>动捕查看</span>
        </router-link>
        <router-link to="/sensor" class="nav-item">
          <div class="nav-icon"><TrendCharts /></div>
          <span>传感器数据</span>
        </router-link>

        <div class="nav-section-title">系统</div>
        <router-link to="/settings" class="nav-item">
          <div class="nav-icon"><Setting /></div>
          <span>系统设置</span>
        </router-link>
      </nav>

      <!-- 底部连接状态 -->
      <div class="sidebar-footer">
        <div class="connection-status">
          <span class="status-dot" :class="wsConnected ? 'online' : 'offline'"></span>
          <span class="status-text">{{ wsConnected ? '实时连接' : '连接断开' }}</span>
        </div>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="main">
      <!-- 顶栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ currentPageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <!-- 明暗切换 -->
          <button class="theme-switch" @click="toggleTheme" :title="isDark ? '切换亮色模式' : '切换暗色模式'">
            <svg v-if="isDark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>

          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-chip">
              <div class="user-avatar">{{ userName?.charAt(0)?.toUpperCase() }}</div>
              <div class="user-detail">
                <span class="user-name">{{ userName }}</span>
                <span class="user-role-chip">{{ roleText }}</span>
              </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容 -->
      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Monitor, View, Link, Sunny,
  VideoCamera, TrendCharts, Setting, SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { useDeviceStore } from '@/store/device'
import { useThemeStore } from '@/store/theme'
import { wsClient } from '@/websocket/client'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const deviceStore = useDeviceStore()
const themeStore = useThemeStore()

const isDark = computed(() => themeStore.isDark)
const toggleTheme = () => themeStore.toggleTheme()
const wsConnected = computed(() => deviceStore.websocketConnected)
const userName = computed(() => userStore.userName)
const userRole = computed(() => userStore.userRole)

const roleText = computed(() => {
  return { admin: '管理员', operator: '操作员', viewer: '观察员' }[userRole.value] || ''
})

const currentPageTitle = computed(() => {
  return {
    Dashboard: '监控大屏',
    FanControl: '风扇控制',
    EnvControl: '环境控制',
    PLCMonitor: 'PLC监控',
    MotionView: '动捕查看',
    SensorData: '传感器数据',
    Settings: '系统设置'
  }[route.name] || ''
})

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      wsClient.disconnect()
      router.push('/login')
      ElMessage.success('已退出登录')
    })
  }
}

onMounted(() => {
  themeStore.applyTheme()
  wsClient.connect()
  wsClient.subscribe(['device_status', 'environment', 'power', 'fan_update', 'sensor', 'motion'])
})

onUnmounted(() => {
  wsClient.disconnect()
})
</script>

<style scoped>
.layout {
  width: 100%;
  height: 100vh;
  display: flex;
  background: var(--bg-base);
  overflow: hidden;
}

/* ====== 侧边栏 ====== */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, var(--accent-glow), transparent 30%, transparent 70%, var(--accent-glow));
  opacity: 0.5;
}

/* Logo区域 */
.sidebar-brand {
  padding: 20px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border);
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}
.brand-icon svg {
  width: 20px;
  height: 20px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.brand-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}
.brand-sub {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  overflow-y: auto;
}

.nav-section-title {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  padding: 16px 12px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin: 2px 0;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  position: relative;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.router-link-active {
  background: var(--bg-active);
  color: var(--accent-light);
}
.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  background: var(--accent);
  border-radius: 0 3px 3px 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  opacity: 0.7;
}
.nav-item.router-link-active .nav-icon {
  opacity: 1;
}

/* 底部状态 */
.sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid var(--border);
}
.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-text {
  font-size: 11px;
  color: var(--text-muted);
}

/* ====== 主区域 ====== */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 20% 0%, rgba(14, 165, 233, 0.04) 0%, transparent 50%),
    var(--bg-base);
}

/* 顶栏 */
.topbar {
  height: 56px;
  min-height: 56px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
}

.page-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.2px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 明暗切换按钮 */
.theme-switch {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.theme-switch svg { width: 18px; height: 18px; }
.theme-switch:hover {
  border-color: var(--accent);
  color: var(--accent-light);
  box-shadow: var(--shadow-glow);
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 14px 5px 5px;
  border-radius: 40px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
}
.user-chip:hover {
  border-color: var(--border-light);
  background: rgba(30, 37, 56, 0.8);
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 600;
}

.user-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.user-role-chip {
  font-size: 10px;
  color: var(--accent-light);
  background: rgba(14, 165, 233, 0.12);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

/* 内容区 */
.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

/* 页面切换动画 */
.page-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
