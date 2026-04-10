<template>
  <div class="dashboard">
    <!-- 第一行：系统状态和通讯状态 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <div class="card">
          <div class="card-header">系统状态</div>
          <div class="card-body">
            <div class="status-row">
              <span class="label">设备状态：</span>
              <el-tag :type="deviceStatus?.device_on ? 'success' : 'danger'">
                {{ deviceStatus?.device_on ? '运行中' : '已停止' }}
              </el-tag>
            </div>
            <div class="status-row">
              <span class="label">健康状态：</span>
              <el-tag type="success">{{ deviceStatus?.health || '正常' }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="18">
        <div class="card">
          <div class="card-header">通讯状态</div>
          <div class="card-body">
            <el-table :data="commData" size="small" :show-header="false">
              <el-table-column prop="name" label="名称" width="120" />
              <el-table-column prop="protocol" label="协议" width="100" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <span
                    class="status-indicator"
                    :class="row.status === 'online' ? 'online' : 'offline'"
                  ></span>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" width="80" />
              <el-table-column prop="speed" label="速率" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二行：环境数据和电力监控 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <div class="card">
          <div class="card-header">环境数据</div>
          <div class="card-body">
            <el-row :gutter="16">
              <el-col :span="6">
                <div class="data-item">
                  <div class="data-label">温度</div>
                  <div class="data-value">{{ environment?.temperature || '--' }}<span class="data-unit">°C</span></div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="data-item">
                  <div class="data-label">湿度</div>
                  <div class="data-value">{{ environment?.humidity || '--' }}<span class="data-unit">%</span></div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="data-item">
                  <div class="data-label">气压</div>
                  <div class="data-value">{{ environment?.pressure || '--' }}<span class="data-unit">Pa</span></div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="data-item">
                  <div class="data-label">密度</div>
                  <div class="data-value">{{ environment?.density || '--' }}<span class="data-unit">kg/m³</span></div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="card">
          <div class="card-header">电力监控</div>
          <div class="card-body">
            <el-row :gutter="16">
              <el-col :span="8">
                <div class="data-item">
                  <div class="data-label">电流</div>
                  <div class="data-value">{{ power?.current || '--' }}<span class="data-unit">A</span></div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="data-item">
                  <div class="data-label">电压</div>
                  <div class="data-value">{{ power?.voltage || '--' }}<span class="data-unit">V</span></div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="data-item">
                  <div class="data-label">功率</div>
                  <div class="data-value">{{ power?.power || '--' }}<span class="data-unit">kW</span></div>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：实时曲线 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">实时数据曲线</div>
          <div class="card-body">
            <div ref="chartRef" style="width: 100%; height: 250px"></div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { systemApi } from '@/api/data'
import { useDeviceStore } from '@/store/device'

const deviceStore = useDeviceStore()
const chartRef = ref(null)
let chart = null

// 计算属性
const deviceStatus = computed(() => deviceStore.deviceStatus)
const environment = computed(() => deviceStore.environment)
const power = computed(() => deviceStore.power)

// 通讯数据（静态，实际应从API获取）
const commData = ref([
  { name: '主控制器', protocol: 'TCP/IP', status: 'online', count: 128, speed: '100 Mbps' },
  { name: '电驱', protocol: 'EtherCAT', status: 'online', count: 64, speed: '100 Mbps' },
  { name: '风速传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '温度传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '湿度传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '动捕', protocol: 'API', status: 'online', count: 12, speed: '1 Gbps' },
])

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['电流', '电压', '功率'],
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
      boundaryGap: false,
      data: Array.from({ length: 60 }, (_, i) => i + 's'),
      axisLine: {
        lineStyle: {
          color: '#3a3c43'
        }
      },
      axisLabel: {
        color: '#8a8f98'
      }
    },
    yAxis: {
      type: 'value',
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
    series: [
      {
        name: '电流',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 60 }, () => Math.random() * 50 + 100),
        itemStyle: {
          color: '#00d1ff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 209, 255, 0.3)' },
              { offset: 1, color: 'rgba(0, 209, 255, 0)' }
            ]
          }
        }
      },
      {
        name: '电压',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 60 }, () => Math.random() * 10 + 375),
        itemStyle: {
          color: '#00ff7f'
        }
      },
      {
        name: '功率',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 60 }, () => Math.random() * 15 + 40),
        itemStyle: {
          color: '#ffc800'
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
  // 获取初始数据
  try {
    const [statusRes, commRes, envRes, powerRes] = await Promise.all([
      systemApi.getStatus(),
      systemApi.getCommunications(),
      systemApi.getEnvironment(),
      systemApi.getPower()
    ])

    deviceStore.setDeviceStatus(statusRes)
    commData.value = commRes
    deviceStore.setEnvironment(envRes)
    deviceStore.setPower(powerRes)
  } catch (error) {
    console.error('获取数据失败:', error)
  }

  // 初始化图表
  await nextTick()
  initChart()

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
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

.status-row:last-child {
  margin-bottom: 0;
}

.status-row .label {
  color: #8a8f98;
  margin-right: 8px;
}

.data-item {
  text-align: center;
  padding: 8px 0;
}

.data-label {
  font-size: 12px;
  color: #8a8f98;
  margin-bottom: 8px;
}

.data-value {
  font-size: 24px;
  font-weight: bold;
  color: #00d1ff;
}

.data-unit {
  font-size: 14px;
  color: #8a8f98;
  margin-left: 4px;
}
</style>
