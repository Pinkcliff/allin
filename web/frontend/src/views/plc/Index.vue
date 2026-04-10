<template>
  <div class="plc-monitor-page">
    <!-- PLC状态 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="8">
        <div class="card">
          <div class="card-header">PLC状态</div>
          <div class="card-body">
            <div class="status-row">
              <span class="label">连接状态：</span>
              <el-tag :type="plcStatus?.connected ? 'success' : 'danger'">
                {{ plcStatus?.connected ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            <div class="status-row">
              <span class="label">IP地址：</span>
              <span class="value">{{ plcStatus?.ip_address || '--' }}</span>
            </div>
            <div class="status-row">
              <span class="label">最后更新：</span>
              <span class="value">{{ formatTime(plcStatus?.last_update) }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="16">
        <div class="card">
          <div class="card-header">操作</div>
          <div class="card-body">
            <el-space>
              <el-button @click="refreshAll" :loading="loading">
                <el-icon><Refresh /></el-icon>
                刷新全部
              </el-button>
              <el-switch v-model="autoRefresh" active-text="自动刷新" />
            </el-space>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="mb-16">
      <el-tab-pane label="编码器监控" name="encoder">
        <div class="card">
          <div class="card-header">编码器数据</div>
          <div class="card-body">
            <el-table :data="encoderData" size="small" stripe>
              <el-table-column prop="encoder_id" label="编码器ID" width="100" />
              <el-table-column label="位置 (度)" width="150">
                <template #default="{ row }">
                  <span :class="{ 'highlight': Math.abs(row.position) > 180 }">
                    {{ row.position?.toFixed(2) || '--' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="速度 (度/秒)" width="150">
                <template #default="{ row }">
                  <span :class="getVelocityClass(row.velocity)">
                    {{ row.velocity?.toFixed(2) || '--' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="timestamp" label="更新时间" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="点表监控" name="point">
        <div class="card">
          <div class="card-header">点表数据</div>
          <div class="card-body">
            <el-table :data="pointData" size="small" stripe>
              <el-table-column prop="point_name" label="点表名称" width="150" />
              <el-table-column label="数值" width="120">
                <template #default="{ row }">
                  <span class="value">{{ row.value?.toFixed(2) || '--' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="unit" label="单位" width="80" />
              <el-table-column prop="timestamp" label="更新时间" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史曲线" name="history">
        <div class="card">
          <div class="card-header">
            <span>编码器历史曲线</span>
            <el-select v-model="selectedEncoder" size="small" style="width: 150px" @change="loadHistory">
              <el-option v-for="i in 8" :key="i" :label="`编码器 ${i}`" :value="i" />
            </el-select>
          </div>
          <div class="card-body">
            <div ref="chartRef" style="width: 100%; height: 300px"></div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { plcApi } from '@/api/data'

// 数据
const plcStatus = ref(null)
const encoderData = ref([])
const pointData = ref([])
const loading = ref(false)
const autoRefresh = ref(true)
const activeTab = ref('encoder')
const selectedEncoder = ref(1)

// 图表
const chartRef = ref(null)
let chart = null
let refreshTimer = null

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '--'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 获取速度样式类
const getVelocityClass = (velocity) => {
  if (Math.abs(velocity) > 100) return 'warning'
  if (Math.abs(velocity) > 50) return 'caution'
  return 'normal'
}

// 刷新PLC状态
const refreshStatus = async () => {
  try {
    const res = await plcApi.getStatus()
    plcStatus.value = res
  } catch (error) {
    ElMessage.error('获取PLC状态失败')
  }
}

// 刷新编码器数据
const refreshEncoder = async () => {
  try {
    const res = await plcApi.getEncoderData()
    encoderData.value = res.encoders || []
  } catch (error) {
    ElMessage.error('获取编码器数据失败')
  }
}

// 刷新点表数据
const refreshPoint = async () => {
  try {
    const res = await plcApi.getPointData()
    pointData.value = res.points || []
  } catch (error) {
    ElMessage.error('获取点表数据失败')
  }
}

// 刷新全部
const refreshAll = async () => {
  loading.value = true
  try {
    await Promise.all([
      refreshStatus(),
      refreshEncoder(),
      refreshPoint()
    ])
    if (activeTab.value === 'history') {
      loadHistory()
    }
  } finally {
    loading.value = false
  }
}

// 加载历史数据
const loadHistory = async () => {
  try {
    const res = await plcApi.getHistory(selectedEncoder.value, { limit: 100 })
    initChart(res.data || [])
  } catch (error) {
    ElMessage.error('获取历史数据失败')
  }
}

// 初始化图表
const initChart = (data) => {
  if (!chartRef.value) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const times = data.map(d => {
    const date = new Date(d.timestamp)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
  })
  const positions = data.map(d => d.position)
  const velocities = data.map(d => d.velocity)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['位置', '速度'],
      textStyle: {
        color: '#e1e1e6'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: {
        lineStyle: {
          color: '#3a3c43'
        }
      },
      axisLabel: {
        color: '#8a8f98',
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '位置(度)',
        axisLine: {
          lineStyle: {
            color: '#3a3c43'
          }
        },
        axisLabel: {
          color: '#8a8f98'
        },
        splitLine: {
          lineStyle: {
            color: '#3a3c43'
          }
        }
      },
      {
        type: 'value',
        name: '速度(度/秒)',
        axisLine: {
          lineStyle: {
            color: '#3a3c43'
          }
        },
        axisLabel: {
          color: '#8a8f98'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '位置',
        type: 'line',
        smooth: true,
        data: positions,
        itemStyle: {
          color: '#00d1ff'
        }
      },
      {
        name: '速度',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: velocities,
        itemStyle: {
          color: '#00ff7f'
        }
      }
    ]
  }

  chart.setOption(option)
}

// 窗口大小改变时重新渲染图表
const handleResize = () => {
  chart?.resize()
}

onMounted(async () => {
  await refreshAll()

  // 自动刷新
  if (autoRefresh.value) {
    refreshTimer = setInterval(refreshAll, 2000)
  }

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.plc-monitor-page {
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

/* 表格样式 */
.el-table {
  background: transparent;
}

.el-table :deep(.el-table__body tr) {
  background: transparent;
}

.el-table :deep(.el-table__body tr:hover > td) {
  background: rgba(0, 209, 255, 0.1) !important;
}

.el-table :deep(td) {
  border-color: #3a3c43;
}

.el-table :deep(.el-table__header th) {
  background: #2a2c33;
  border-color: #3a3c43;
  color: #e1e1e6;
}

.value {
  color: #00d1ff;
  font-weight: bold;
}

.highlight {
  color: #ff3b30;
  font-weight: bold;
}

.warning {
  color: #ff3b30;
}

.caution {
  color: #ffc800;
}

.normal {
  color: #00ff7f;
}
</style>
