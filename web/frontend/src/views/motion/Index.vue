<template>
  <div class="motion-view-page">
    <!-- 动捕系统状态 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <div class="card">
          <div class="card-header">系统状态</div>
          <div class="card-body">
            <div class="status-row">
              <span class="label">连接状态：</span>
              <el-tag :type="motionStatus?.connected ? 'success' : 'danger'">
                {{ motionStatus?.connected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            <div class="status-row">
              <span class="label">IP地址：</span>
              <span class="value">{{ motionStatus?.ip_address || '--' }}</span>
            </div>
            <div class="status-row">
              <span class="label">帧率：</span>
              <span class="value">{{ motionStatus?.current_fps || 0 }} FPS</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="card">
          <div class="card-header">相机状态</div>
          <div class="card-body">
            <div class="camera-grid">
              <div
                v-for="camera in cameras"
                :key="camera.camera_id"
                class="camera-item"
                :class="camera.status"
              >
                <span class="camera-id">{{ camera.camera_id.toString().padStart(2, '0') }}</span>
                <span class="camera-status">
                  <i class="status-dot"></i>
                  {{ camera.status === 'green' ? '在线' : '离线' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="card">
          <div class="card-header">录制控制</div>
          <div class="card-body">
            <el-space direction="vertical" style="width: 100%">
              <div class="recording-status">
                <span class="label">录制状态：</span>
                <el-tag :type="motionStatus?.recording ? 'success' : 'info'">
                  {{ motionStatus?.recording ? '录制中' : '未录制' }}
                </el-tag>
              </div>
              <el-button
                v-if="!motionStatus?.recording"
                type="primary"
                @click="startRecording"
                :loading="loading.recording"
                style="width: 100%"
              >
                <el-icon><VideoPlay /></el-icon>
                开始录制
              </el-button>
              <el-button
                v-else
                type="danger"
                @click="stopRecording"
                :loading="loading.recording"
                style="width: 100%"
              >
                <el-icon><VideoPause /></el-icon>
                停止录制
              </el-button>
            </el-space>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 实时数据 -->
    <div class="card mb-16">
      <div class="card-header">实时动捕数据</div>
      <div class="card-body">
        <el-empty description="暂无数据" v-if="!motionData || motionData.length === 0" />
        <div v-else class="motion-data-container">
          <div class="data-summary">
            <span class="data-item">帧ID: {{ motionData.frame_id || '--' }}</span>
            <span class="data-item">标记点: {{ motionStatus?.total_markers || 0 }}</span>
            <span class="data-item">时间戳: {{ motionData.timestamp || '--' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史数据 -->
    <div class="card">
      <div class="card-header">历史记录</div>
      <div class="card-body">
        <el-empty description="暂无历史记录" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { motionApi } from '@/api/data'

// 数据
const motionStatus = ref(null)
const cameras = ref([])
const motionData = ref(null)
const loading = ref({
  recording: false
})

let refreshTimer = null

// 刷新状态
const refreshStatus = async () => {
  try {
    const [statusRes, camerasRes] = await Promise.all([
      motionApi.getStatus(),
      motionApi.getCameras()
    ])
    motionStatus.value = statusRes
    cameras.value = camerasRes
  } catch (error) {
    ElMessage.error('获取状态失败')
  }
}

// 获取实时数据
const refreshData = async () => {
  try {
    const res = await motionApi.getData({ limit: 1 })
    if (res.frames && res.frames.length > 0) {
      motionData.value = res.frames[0]
    }
  } catch (error) {
    // 静默失败，不显示错误
  }
}

// 开始录制
const startRecording = async () => {
  loading.value.recording = true
  try {
    await motionApi.startRecording()
    ElMessage.success('录制已开始')
    await refreshStatus()
  } catch (error) {
    ElMessage.error('开始录制失败')
  } finally {
    loading.value.recording = false
  }
}

// 停止录制
const stopRecording = async () => {
  loading.value.recording = true
  try {
    const res = await motionApi.stopRecording()
    ElMessage.success(`录制已停止：${res.file_path || ''}`)
    await refreshStatus()
  } catch (error) {
    ElMessage.error('停止录制失败')
  } finally {
    loading.value.recording = false
  }
}

onMounted(async () => {
  await refreshStatus()
  await refreshData()

  // 定时刷新
  refreshTimer = setInterval(async () => {
    await refreshStatus()
    await refreshData()
  }, 1000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.motion-view-page {
  height: 100%;
  overflow-y: auto;
}

.mb-16 {
  margin-bottom: 16px;
}

.card-body {
  padding: 16px;
}

.status-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.status-row .label {
  color: #8a8f98;
  margin-right: 8px;
}

.status-row .value {
  color: #e1e1e6;
}

/* 相机网格 */
.camera-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}

.camera-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: #1a1c23;
  border: 1px solid #3a3c43;
  border-radius: 4px;
}

.camera-item .camera-id {
  font-size: 16px;
  font-weight: bold;
  color: #e1e1e6;
  margin-bottom: 4px;
}

.camera-item .camera-status {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.camera-item.green {
  border-color: #00ff7f;
}

.camera-item.green .camera-id {
  color: #00ff7f;
}

.camera-item.red {
  border-color: #ff3b30;
}

.camera-item.red .camera-id {
  color: #ff3b30;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.camera-item.green .status-dot {
  background: #00ff7f;
  box-shadow: 0 0 4px #00ff7f;
}

.camera-item.red .status-dot {
  background: #ff3b30;
}

/* 录制状态 */
.recording-status {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.recording-status .label {
  color: #8a8f98;
  margin-right: 8px;
}

/* 动捕数据 */
.motion-data-container {
  padding: 16px;
  background: #1a1c23;
  border-radius: 4px;
}

.data-summary {
  display: flex;
  gap: 24px;
}

.data-item {
  color: #e1e1e6;
  font-size: 14px;
}
</style>
