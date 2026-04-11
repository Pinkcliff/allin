<template>
  <div class="dashboard fade-in">
    <!-- 系统状态 + 通讯 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <div class="card status-card">
          <div class="card-header">系统状态</div>
          <div class="card-body">
            <div class="status-row">
              <span class="status-label">设备</span>
              <el-tag :type="deviceStatus?.device_on ? 'success' : 'danger'" size="small" effect="dark">
                {{ deviceStatus?.device_on ? '运行中' : '已停止' }}
              </el-tag>
            </div>
            <div class="status-row">
              <span class="status-label">健康</span>
              <el-tag type="success" size="small" effect="dark">{{ deviceStatus?.health || '正常' }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="18">
        <div class="card">
          <div class="card-header">通讯状态</div>
          <div class="card-body" style="padding: 0;">
            <el-table :data="commData" size="small">
              <el-table-column prop="name" label="设备" width="120">
                <template #default="{ row }">
                  <div style="display:flex;align-items:center;gap:8px">
                    <span class="status-dot" :class="row.status === 'online' ? 'online' : 'offline'"></span>
                    {{ row.name }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="protocol" label="协议" width="100" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'online' ? 'success' : 'danger'" size="small" effect="dark">
                    {{ row.status === 'online' ? '在线' : '离线' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="节点" width="80" />
              <el-table-column prop="speed" label="速率" />
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 环境 + 电力 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <div class="card env-card">
          <div class="card-header">环境数据</div>
          <div class="card-body">
            <div class="metrics-grid">
              <div class="metric-item">
                <div class="metric-icon temp">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value">{{ environment?.temperature || '--' }}<span class="data-unit">°C</span></div>
                  <div class="metric-label">温度</div>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-icon humid">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value">{{ environment?.humidity || '--' }}<span class="data-unit">%</span></div>
                  <div class="metric-label">湿度</div>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-icon press">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value">{{ environment?.pressure || '--' }}<span class="data-unit">Pa</span></div>
                  <div class="metric-label">气压</div>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-icon density">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value">{{ environment?.density || '--' }}<span class="data-unit">kg/m³</span></div>
                  <div class="metric-label">密度</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card power-card">
          <div class="card-header">电力监控</div>
          <div class="card-body">
            <div class="metrics-grid">
              <div class="metric-item">
                <div class="metric-icon current">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value accent">{{ power?.current || '--' }}<span class="data-unit">A</span></div>
                  <div class="metric-label">电流</div>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-icon volt">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value accent">{{ power?.voltage || '--' }}<span class="data-unit">V</span></div>
                  <div class="metric-label">电压</div>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-icon watt">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                </div>
                <div class="metric-info">
                  <div class="metric-value accent">{{ power?.power || '--' }}<span class="data-unit">kW</span></div>
                  <div class="metric-label">功率</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 实时曲线 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">实时数据曲线</div>
          <div class="card-body">
            <div ref="chartRef" style="width: 100%; height: 280px"></div>
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

const deviceStatus = computed(() => deviceStore.deviceStatus)
const environment = computed(() => deviceStore.environment)
const power = computed(() => deviceStore.power)

const commData = ref([
  { name: '主控制器', protocol: 'TCP/IP', status: 'online', count: 128, speed: '100 Mbps' },
  { name: '电驱', protocol: 'EtherCAT', status: 'online', count: 64, speed: '100 Mbps' },
  { name: '风速传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '温度传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '湿度传感', protocol: 'EtherCAT', status: 'online', count: 16, speed: '100 Mbps' },
  { name: '动捕', protocol: 'API', status: 'online', count: 12, speed: '1 Gbps' },
])

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const timeData = Array.from({ length: 60 }, (_, i) => i + 's')

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,25,38,0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#f0f2f5', fontSize: 12 }
    },
    legend: {
      data: ['电流', '电压', '功率'],
      textStyle: { color: '#8b95a8', fontSize: 12 },
      right: 20,
      top: 0,
      icon: 'roundRect',
      itemWidth: 12,
      itemHeight: 3
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 36, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timeData,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#4b5567', fontSize: 10 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#4b5567', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
    },
    series: [
      {
        name: '电流', type: 'line', smooth: true, showSymbol: false,
        data: Array.from({ length: 60 }, () => +(Math.random() * 50 + 100).toFixed(1)),
        lineStyle: { color: '#0ea5e9', width: 2 },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14,165,233,0.25)' },
              { offset: 1, color: 'rgba(14,165,233,0)' }
            ]
          }
        }
      },
      {
        name: '电压', type: 'line', smooth: true, showSymbol: false,
        data: Array.from({ length: 60 }, () => +(Math.random() * 10 + 375).toFixed(1)),
        lineStyle: { color: '#22c55e', width: 2 }
      },
      {
        name: '功率', type: 'line', smooth: true, showSymbol: false,
        data: Array.from({ length: 60 }, () => +(Math.random() * 15 + 40).toFixed(1)),
        lineStyle: { color: '#eab308', width: 2 }
      }
    ]
  })
}

const handleResize = () => chart?.resize()

onMounted(async () => {
  try {
    const [statusRes, commRes, envRes, powerRes] = await Promise.all([
      systemApi.getStatus(), systemApi.getCommunications(),
      systemApi.getEnvironment(), systemApi.getPower()
    ])
    deviceStore.setDeviceStatus(statusRes)
    commData.value = commRes
    deviceStore.setEnvironment(envRes)
    deviceStore.setPower(powerRes)
  } catch (e) { console.error('获取数据失败:', e) }

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

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}
.status-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 数据指标网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}
.metric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  transition: border-color 0.2s;
}
.metric-item:hover {
  border-color: var(--border-light);
}

.metric-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.metric-icon svg { width: 20px; height: 20px; }
.metric-icon.temp   { background: rgba(239,68,68,0.12); color: #ef4444; }
.metric-icon.humid  { background: rgba(14,165,233,0.12); color: #0ea5e9; }
.metric-icon.press  { background: rgba(139,92,246,0.12); color: #8b5cf6; }
.metric-icon.density{ background: rgba(34,197,94,0.12); color: #22c55e; }
.metric-icon.current{ background: rgba(14,165,233,0.12); color: #0ea5e9; }
.metric-icon.volt   { background: rgba(234,179,8,0.12); color: #eab308; }
.metric-icon.watt   { background: rgba(139,92,246,0.12); color: #8b5cf6; }

.metric-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}
.metric-value.accent {
  color: var(--accent-light);
}
.metric-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 3px;
}
.data-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted);
  margin-left: 2px;
}
</style>
