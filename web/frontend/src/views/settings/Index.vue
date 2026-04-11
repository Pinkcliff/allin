<template>
  <div class="settings-page">
    <!-- 用户管理 -->
    <div class="card mb-16">
      <div class="card-header">
        <span><el-icon><User /></el-icon> 用户管理</span>
      </div>
      <div class="card-body">
        <el-table :data="users" size="small" stripe>
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="full_name" label="姓名" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleType(row.role)" size="small">
                {{ getRoleText(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="权限" width="300">
            <template #default="{ row }">
              <el-space>
                <el-tag v-if="row.role === 'admin' || row.role === 'operator'" size="small">设备控制</el-tag>
                <el-tag v-if="row.role === 'admin'" size="small">用户管理</el-tag>
                <el-tag size="small">数据查看</el-tag>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 通讯协议设置 -->
    <div class="card mb-16">
      <div class="card-header">
        <span><el-icon><Link /></el-icon> 通讯协议配置</span>
      </div>
      <div class="card-body">
        <el-table :data="protocols" size="small" stripe>
          <el-table-column prop="name" label="设备名称" width="150" />
          <el-table-column prop="protocol" label="协议" width="120" />
          <el-table-column prop="address" label="地址" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">
                {{ row.status === 'online' ? '在线' : '离线' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="editProtocol(row)">配置</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 系统参数 -->
    <div class="card mb-16">
      <div class="card-header">
        <span><el-icon><Setting /></el-icon> 系统参数</span>
      </div>
      <div class="card-body">
        <el-form :model="systemParams" label-width="150px" style="max-width: 600px">
          <el-form-item label="数据刷新频率">
            <el-input-number v-model="systemParams.refreshRate" :min="100" :max="10000" :step="100" />
            <span class="unit">毫秒</span>
          </el-form-item>
          <el-form-item label="历史数据保留">
            <el-input-number v-model="systemParams.dataRetention" :min="1" :max="365" />
            <span class="unit">天</span>
          </el-form-item>
          <el-form-item label="自动备份">
            <el-switch v-model="systemParams.autoBackup" />
          </el-form-item>
          <el-form-item label="调试模式">
            <el-switch v-model="systemParams.debugMode" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSystemParams">保存设置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 系统信息 -->
    <div class="card">
      <div class="card-header">
        <span><el-icon><InfoFilled /></el-icon> 系统信息</span>
      </div>
      <div class="card-body">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="系统名称">微小型无人机智能风场测试评估系统</el-descriptions-item>
          <el-descriptions-item label="版本号">v1.0.0</el-descriptions-item>
          <el-descriptions-item label="后端API">http://localhost:8000</el-descriptions-item>
          <el-descriptions-item label="前端">http://localhost:5173</el-descriptions-item>
          <el-descriptions-item label="Python版本">3.11+</el-descriptions-item>
          <el-descriptions-item label="Node版本">18+</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>

    <!-- 协议配置对话框 -->
    <el-dialog v-model="protocolDialogVisible" title="通讯协议配置" width="500px">
      <el-form :model="protocolForm" label-width="100px">
        <el-form-item label="设备名称">
          <el-input v-model="protocolForm.name" disabled />
        </el-form-item>
        <el-form-item label="协议类型">
          <el-select v-model="protocolForm.protocol" style="width: 100%">
            <el-option label="TCP/IP" value="TCP/IP" />
            <el-option label="EtherCAT" value="EtherCAT" />
            <el-option label="Modbus" value="Modbus" />
            <el-option label="API" value="API" />
          </el-select>
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="protocolForm.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="protocolDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProtocol">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Link, Setting, InfoFilled } from '@element-plus/icons-vue'

// 用户数据
const users = ref([
  { username: 'admin', full_name: '系统管理员', role: 'admin' },
  { username: 'operator', full_name: '操作员', role: 'operator' },
  { username: 'viewer', full_name: '观察员', role: 'viewer' }
])

// 通讯协议数据
const protocols = ref([
  { name: '主控制器', protocol: 'TCP/IP', address: '192.168.1.1:8000', status: 'online' },
  { name: '电驱', protocol: 'EtherCAT', address: '192.168.1.10', status: 'online' },
  { name: '风速传感', protocol: 'EtherCAT', address: '192.168.1.20', status: 'online' },
  { name: '温度传感', protocol: 'EtherCAT', address: '192.168.1.21', status: 'online' },
  { name: '湿度传感', protocol: 'EtherCAT', address: '192.168.1.22', status: 'online' },
  { name: '动捕', protocol: 'API', address: '192.168.1.50:8000', status: 'online' },
  { name: '俯仰伺服', protocol: 'Modbus', address: '192.168.1.30', status: 'offline' },
  { name: '造雨', protocol: 'Modbus', address: '192.168.1.31', status: 'offline' },
  { name: '喷雾', protocol: 'Modbus', address: '192.168.1.32', status: 'offline' }
])

// 系统参数
const systemParams = ref({
  refreshRate: 1000,
  dataRetention: 30,
  autoBackup: true,
  debugMode: false
})

// 协议配置
const protocolDialogVisible = ref(false)
const protocolForm = ref({
  name: '',
  protocol: '',
  address: ''
})

// 获取角色类型
const getRoleType = (role) => {
  const typeMap = {
    admin: 'danger',
    operator: 'warning',
    viewer: 'info'
  }
  return typeMap[role] || 'info'
}

// 获取角色文本
const getRoleText = (role) => {
  const textMap = {
    admin: '管理员',
    operator: '操作员',
    viewer: '观察员'
  }
  return textMap[role] || role
}

// 编辑协议
const editProtocol = (row) => {
  protocolForm.value = { ...row }
  protocolDialogVisible.value = true
}

// 保存协议
const saveProtocol = () => {
  const index = protocols.value.findIndex(p => p.name === protocolForm.value.name)
  if (index !== -1) {
    protocols.value[index] = { ...protocolForm.value }
  }
  protocolDialogVisible.value = false
  ElMessage.success('配置已保存')
}

// 保存系统参数
const saveSystemParams = () => {
  ElMessage.success('系统参数已保存')
}
</script>

<style scoped>
.settings-page {
  height: 100%;
  overflow-y: auto;
}

.mb-16 {
  margin-bottom: 16px;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-body {
  padding: 16px;
}

.unit {
  margin-left: 8px;
  color: #8a8f98;
}
</style>
