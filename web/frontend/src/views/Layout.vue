<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>风场测试系统</h2>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/dashboard" class="nav-item">
          <el-icon><Monitor /></el-icon>
          <span>监控大屏</span>
        </router-link>
        <router-link to="/fan" class="nav-item">
          <el-icon><View /></el-icon>
          <span>风扇控制</span>
        </router-link>
        <router-link to="/env" class="nav-item">
          <el-icon><Cloud /></el-icon>
          <span>环境控制</span>
        </router-link>
        <router-link to="/plc" class="nav-item">
          <el-icon><Connection /></el-icon>
          <span>PLC监控</span>
        </router-link>
        <router-link to="/motion" class="nav-item">
          <el-icon><VideoCamera /></el-icon>
          <span>动捕查看</span>
        </router-link>
        <router-link to="/sensor" class="nav-item">
          <el-icon><DataLine /></el-icon>
          <span>传感器数据</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="header">
        <div class="header-left">
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>

        <div class="header-right">
          <!-- WebSocket状态 -->
          <div class="status-item">
            <span
              class="status-indicator"
              :class="{ online: wsConnected, offline: !wsConnected }"
            ></span>
            <span>{{ wsConnected ? '已连接' : '未连接' }}</span>
          </div>

          <!-- 用户信息 -->
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ userName }}</span>
              <span class="user-role">{{ roleText }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区 -->
      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useDeviceStore } from '@/store/device'
import { wsClient } from '@/websocket/client'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const deviceStore = useDeviceStore()

// 计算属性
const wsConnected = computed(() => deviceStore.websocketConnected)
const userName = computed(() => userStore.userName)
const userRole = computed(() => userStore.userRole)

const roleText = computed(() => {
  const roleMap = {
    admin: '管理员',
    operator: '操作员',
    viewer: '观察员'
  }
  return roleMap[userRole.value] || ''
})

const currentPageTitle = computed(() => {
  const titleMap = {
    Dashboard: '监控大屏',
    FanControl: '风扇控制',
    EnvControl: '环境控制',
    PLCMonitor: 'PLC监控',
    MotionView: '动捕查看',
    SensorData: '传感器数据',
    Settings: '系统设置'
  }
  return titleMap[route.name] || ''
})

// 方法
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

// 生命周期
onMounted(() => {
  // 连接WebSocket
  wsClient.connect()

  // 订阅频道
  wsClient.subscribe(['device_status', 'environment', 'power'])
})

onUnmounted(() => {
  // 断开WebSocket
  wsClient.disconnect()
})
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #1a1c23;
}

.sidebar {
  width: 200px;
  background: #2a2c33;
  border-right: 1px solid #3a3c43;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #3a3c43;
}

.sidebar-header h2 {
  font-size: 16px;
  color: #e1e1e6;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #8a8f98;
  text-decoration: none;
  transition: all 0.3s;
}

.nav-item:hover {
  background: rgba(0, 209, 255, 0.1);
  color: #e1e1e6;
}

.nav-item.router-link-active {
  background: rgba(0, 209, 255, 0.15);
  color: #00d1ff;
  border-right: 3px solid #00d1ff;
}

.nav-item .el-icon {
  margin-right: 10px;
  font-size: 18px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  background: #2a2c33;
  border-bottom: 1px solid #3a3c43;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #e1e1e6;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #8a8f98;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-role {
  font-size: 12px;
  color: #8a8f98;
  padding: 2px 8px;
  background: rgba(0, 209, 255, 0.1);
  border-radius: 4px;
}

.content-area {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
