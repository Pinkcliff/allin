<template>
  <div class="fan-page fade-in">
    <!-- 顶部控制栏 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="5">
        <div class="card stat-card">
          <div class="stat-row">
            <span class="stat-label">总风扇</span>
            <span class="stat-value">{{ fanStatus?.total_fans || 1600 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">运行中</span>
            <span class="stat-value running">{{ fanStatus?.active_fans || 0 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">在线率</span>
            <span class="stat-value">{{ fanStatus?.total_fans ? '100' : '--' }}%</span>
          </div>
        </div>
      </el-col>

      <el-col :span="13">
        <div class="card actions-card">
          <div class="card-body" style="padding: 10px 16px;">
            <el-space :size="10">
              <el-button type="primary" @click="setAllPower(true)" :loading="loading">
                <el-icon><VideoPlay /></el-icon> 全部开启
              </el-button>
              <el-button type="danger" plain @click="setAllPower(false)" :loading="loading">
                <el-icon><VideoPause /></el-icon> 全部关闭
              </el-button>
              <el-button @click="refreshStatus">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </el-space>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="card">
          <div class="card-header">模板</div>
          <div class="card-body" style="padding-top: 0;">
            <el-select v-model="selectedTemplate" placeholder="选择模板" @change="applyTemplate" style="width: 100%" size="default">
              <el-option label="均匀分布" value="uniform" />
              <el-option label="中心聚焦" value="center" />
              <el-option label="梯度分布" value="gradient" />
              <el-option label="随机分布" value="random" />
            </el-select>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 风扇阵列 + 3D视图 -->
    <el-row :gutter="16">
      <el-col :span="14">
        <div class="card fan-array-card">
          <div class="card-header">
            <span>风扇阵列 40 x 40</span>
            <div class="header-actions">
              <el-button size="small" text @click="toggleAreaMode">
                {{ areaMode ? '退出区域模式' : '区域选择' }}
              </el-button>
              <el-button size="small" text @click="clearSelection" v-if="selectedCells.size > 0">
                清除 ({{ selectedCells.size }})
              </el-button>
            </div>
          </div>
          <div class="card-body fan-grid-wrap">
            <div class="fan-grid" :class="{ 'area-mode': areaMode }">
              <div v-for="(row, y) in fanArray" :key="y" class="fan-row">
                <div
                  v-for="(cell, x) in row" :key="`${x}-${y}`"
                  class="fan-cell"
                  :class="{ active: cell > 0, selected: isCellSelected(x, y) }"
                  :style="getCellStyle(cell)"
                  @click="handleCellClick(x, y)"
                  @mouseenter="handleCellEnter(x, y)"
                />
              </div>
            </div>
          </div>

          <!-- 区域控制 -->
          <div v-if="areaMode || selectedCells.size > 0" class="area-panel">
            <div class="area-panel-title">
              区域控制
              <span v-if="selectedCells.size > 0">（已选择 {{ selectedCells.size }} 个风扇）</span>
            </div>
            <div class="area-panel-body">
              <el-form :inline="true">
                <el-form-item label="转速">
                  <el-slider v-model="areaRpm" :min="0" :max="15000" :step="100"
                    style="width: 260px" />
                  <el-input-number v-model="areaRpm" :min="0" :max="15000" :step="100"
                    style="width: 110px; margin-left: 10px" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="applyAreaControl" :loading="loading">应用</el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="10">
        <div class="card fan-3d-card">
          <div class="card-header">
            <span>3D 风场视图</span>
            <div class="header-actions">
              <el-button size="small" text @click="reset3DView">重置视角</el-button>
            </div>
          </div>
          <div class="card-body" style="padding: 8px;">
            <div ref="chart3dRef" class="chart-3d-container"></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 单风扇设置 -->
    <el-dialog v-model="singleFanDialogVisible" title="单风扇设置" width="400px">
      <el-form :model="singleFanForm" label-width="80px">
        <el-form-item label="位置">
          <el-input :value="`(${singleFanForm.x}, ${singleFanForm.y})`" disabled />
        </el-form-item>
        <el-form-item label="转速">
          <el-slider v-model="singleFanForm.rpm" :min="0" :max="15000" :step="100" />
          <el-input-number v-model="singleFanForm.rpm" :min="0" :max="15000" :step="100"
            style="width: 110px; margin-top: 8px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="singleFanDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="applySingleFan" :loading="loading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fanApi } from '@/api/data'
import { wsClient } from '@/websocket/client'
import * as echarts from 'echarts'
import 'echarts-gl'

const fanStatus = ref(null)
const fanArray = ref([])
const loading = ref(false)
const selectedTemplate = ref('')
const areaMode = ref(false)
const selectedCells = ref(new Set())
const areaStart = ref(null)
const areaRpm = ref(5000)
const singleFanDialogVisible = ref(false)
const singleFanForm = ref({ x: 0, y: 0, rpm: 5000 })

// 3D 图表相关
const chart3dRef = ref(null)
let chart3d = null
let updateTimer3d = null
let pendingUpdate3d = false

const handleFanUpdate = (data) => {
  if (data.fan_array) fanArray.value = data.fan_array
  if (data.active_fans !== undefined) {
    if (!fanStatus.value) fanStatus.value = {}
    fanStatus.value.active_fans = data.active_fans
    fanStatus.value.total_fans = data.total_fans || 1600
  }
  // 标记需要更新3D视图
  pendingUpdate3d = true
}

const initFanArray = () => {
  fanArray.value = Array.from({ length: 40 }, () => Array(40).fill(0))
}

const isCellSelected = (x, y) => selectedCells.value.has(`${x},${y}`)

const handleCellClick = (x, y) => {
  if (areaMode.value) {
    if (!areaStart.value) {
      areaStart.value = { x, y }
    } else {
      const s = areaStart.value
      const minX = Math.min(s.x, x), maxX = Math.max(s.x, x)
      const minY = Math.min(s.y, y), maxY = Math.max(s.y, y)
      for (let py = minY; py <= maxY; py++)
        for (let px = minX; px <= maxX; px++)
          selectedCells.value.add(`${px},${py}`)
      areaStart.value = null
    }
  } else {
    singleFanForm.value = { x, y, rpm: 5000 }
    singleFanDialogVisible.value = true
  }
}
const handleCellEnter = () => {}
const toggleAreaMode = () => { areaMode.value = !areaMode.value; areaStart.value = null; if (!areaMode.value) selectedCells.value.clear() }
const clearSelection = () => { selectedCells.value.clear(); areaStart.value = null }

const setAllPower = async (on) => {
  loading.value = true
  try { await fanApi.setPower(on); ElMessage.success(on ? '已开启' : '已关闭'); await refreshStatus() }
  catch { ElMessage.error('操作失败') }
  finally { loading.value = false }
}

const refreshStatus = async () => {
  try { const r = await fanApi.getStatus(); fanStatus.value = r; fanArray.value = r.fan_array; pendingUpdate3d = true }
  catch { ElMessage.error('获取状态失败') }
}

const applyAreaControl = async () => {
  if (!selectedCells.value.size) { ElMessage.warning('请先选择'); return }
  loading.value = true
  try {
    let minX = 40, maxX = 0, minY = 40, maxY = 0
    selectedCells.value.forEach(k => { const [x, y] = k.split(',').map(Number); minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y) })
    await fanApi.setArea({ start_x: minX, start_y: minY, end_x: maxX, end_y: maxY, rpm: areaRpm.value })
    ElMessage.success(`已设置 ${selectedCells.value.size} 个风扇`)
    selectedCells.value.clear()
    await refreshStatus()
  } catch { ElMessage.error('设置失败') }
  finally { loading.value = false }
}

const applySingleFan = async () => {
  loading.value = true
  try { await fanApi.setSingle(singleFanForm.value); ElMessage.success('设置成功'); singleFanDialogVisible.value = false; await refreshStatus() }
  catch { ElMessage.error('设置失败') }
  finally { loading.value = false }
}

const getCellStyle = (cell) => {
  if (cell <= 0) return {}
  const p = Math.min(100, Math.max(0, cell / 10)) / 100
  const c1 = { r: 173, g: 216, b: 230 }, c2 = { r: 0, g: 255, b: 0 }, c3 = { r: 255, g: 255, b: 0 }, c4 = { r: 255, g: 0, b: 0 }
  const lerp = (a, b, t) => ({ r: Math.round(a.r + (b.r - a.r) * t), g: Math.round(a.g + (b.g - a.g) * t), b: Math.round(a.b + (b.b - a.b) * t) })
  const color = p < 0.33 ? lerp(c1, c2, p / 0.33) : p < 0.66 ? lerp(c2, c3, (p - 0.33) / 0.33) : lerp(c3, c4, (p - 0.66) / 0.34)
  return { backgroundColor: `rgb(${color.r},${color.g},${color.b})` }
}

const applyTemplate = async () => {
  loading.value = true
  try {
    const gens = {
      uniform: () => Array.from({ length: 40 }, () => Array(40).fill(8000)),
      center: () => Array.from({ length: 40 }, (_, y) => Array.from({ length: 40 }, (_, x) => Math.max(2000, 15000 - Math.sqrt((x - 20) ** 2 + (y - 20) ** 2) * 500))),
      gradient: () => Array.from({ length: 40 }, (_, y) => Array.from({ length: 40 }, (_, x) => 3000 + (x / 39) * 12000)),
      random: () => Array.from({ length: 40 }, () => Array.from({ length: 40 }, () => Math.floor(Math.random() * 15000)))
    }
    const data = gens[selectedTemplate.value]()
    for (let y = 0; y < 40; y += 5)
      for (let x = 0; x < 40; x += 5)
        await fanApi.setArea({ start_x: x, start_y: y, end_x: Math.min(x + 4, 39), end_y: Math.min(y + 4, 39), rpm: data[y][x] })
    ElMessage.success('模板已应用')
    await refreshStatus()
  } catch { ElMessage.error('应用模板失败') }
  finally { loading.value = false }
}

// ==================== 3D视图相关 ====================

const init3DChart = () => {
  if (!chart3dRef.value) return
  chart3d = echarts.init(chart3dRef.value)

  const option = {
    tooltip: {
      formatter: (params) => {
        const d = params.data
        return `位置: (${d[0]}, ${d[1]})<br/>转速: ${d[2].toFixed(1)}%`
      }
    },
    visualMap: {
      show: true,
      min: 0,
      max: 100,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090',
                '#fdae61', '#f46d43', '#d73027', '#a50026']
      },
      text: ['高', '低'],
      textStyle: { color: '#aaa' },
      right: 10,
      top: 'center',
      itemHeight: 120
    },
    xAxis3D: {
      type: 'value',
      name: 'X',
      min: 0,
      max: 39,
      nameTextStyle: { color: '#aaa' }
    },
    yAxis3D: {
      type: 'value',
      name: 'Y',
      min: 0,
      max: 39,
      nameTextStyle: { color: '#aaa' }
    },
    zAxis3D: {
      type: 'value',
      name: '转速%',
      min: 0,
      max: 100,
      nameTextStyle: { color: '#aaa' }
    },
    grid3D: {
      viewControl: {
        projection: 'perspective',
        autoRotate: false,
        distance: 180,
        alpha: 25,
        beta: 40
      },
      light: {
        main: {
          intensity: 1.2,
          shadow: true
        },
        ambient: {
          intensity: 0.3
        }
      },
      postEffect: {
        enable: true,
        bloom: { enable: false },
        SSAO: { enable: true, radius: 2, intensity: 1 }
      },
      boxWidth: 100,
      boxHeight: 50,
      boxDepth: 100
    },
    series: [{
      type: 'surface',
      wireframe: { show: false },
      shading: 'realistic',
      realisticMaterial: {
        roughness: 0.6,
        metalness: 0
      },
      itemStyle: {
        opacity: 0.9
      },
      data: []
    }]
  }

  chart3d.setOption(option)

  // 响应窗口大小变化
  window.addEventListener('resize', handleResize3d)
}

const update3DChart = () => {
  if (!chart3d || !fanArray.value || fanArray.value.length === 0) return

  // 构建表面数据 - echarts-gl surface 需要的数据格式
  const data = []
  for (let y = 0; y < 40; y++) {
    for (let x = 0; x < 40; x++) {
      const val = fanArray.value[y]?.[x] || 0
      // 将 PWM (0-1000) 转换为百分比 (0-100)
      const percent = Math.min(100, Math.max(0, val / 10))
      data.push([x, y, percent])
    }
  }

  chart3d.setOption({
    series: [{
      data: data
    }]
  })
}

const reset3DView = () => {
  if (!chart3d) return
  chart3d.setOption({
    grid3D: {
      viewControl: {
        distance: 180,
        alpha: 25,
        beta: 40
      }
    }
  })
}

const handleResize3d = () => {
  if (chart3d) chart3d.resize()
}

// 节流更新3D视图（每200ms最多更新一次）
const start3DUpdateLoop = () => {
  updateTimer3d = setInterval(() => {
    if (pendingUpdate3d) {
      pendingUpdate3d = false
      update3DChart()
    }
  }, 200)
}

onMounted(async () => {
  initFanArray()
  await refreshStatus()

  await nextTick()
  init3DChart()
  update3DChart()
  start3DUpdateLoop()

  wsClient.on('fan_update', handleFanUpdate)
})

onUnmounted(() => {
  wsClient.off('fan_update', handleFanUpdate)
  window.removeEventListener('resize', handleResize3d)
  if (updateTimer3d) clearInterval(updateTimer3d)
  if (chart3d) { chart3d.dispose(); chart3d = null }
})
</script>

<style scoped>
.fan-page { height: 100%; overflow-y: auto; }

/* 状态卡片 */
.stat-card .card-body { padding: 4px 0; }
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
}
.stat-row + .stat-row { border-top: 1px solid var(--border); }
.stat-label { font-size: 13px; color: var(--text-secondary); }
.stat-value { font-size: 15px; font-weight: 600; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.stat-value.running { color: var(--success); }

/* 风扇阵列 */
.fan-array-card { min-height: 0; }
.fan-grid-wrap {
  padding: 16px;
  background: var(--bg-base);
  border-radius: var(--radius-md);
  overflow: auto;
}

.fan-grid {
  display: inline-block;
  user-select: none;
  background: var(--bg-base);
}
.fan-grid.area-mode { cursor: crosshair; }

.fan-row { display: flex; }

.fan-cell {
  width: 11px;
  height: 11px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s, transform 0.1s;
}
.fan-cell:hover {
  border-color: rgba(255, 255, 255, 0.2);
  transform: scale(1.3);
  z-index: 2;
  position: relative;
}
.fan-cell.selected {
  border-color: var(--accent) !important;
  box-shadow: 0 0 4px var(--accent-glow);
}

/* 3D视图卡片 */
.fan-3d-card {
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.fan-3d-card .card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.chart-3d-container {
  width: 100%;
  height: 460px;
  min-height: 300px;
}

/* 区域控制面板 */
.area-panel {
  margin-top: 16px;
  padding: 16px 20px;
  background: rgba(14, 165, 233, 0.04);
  border: 1px solid rgba(14, 165, 233, 0.15);
  border-radius: var(--radius-md);
}
.area-panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-light);
  margin-bottom: 12px;
}
.area-panel-body { display: flex; align-items: center; }

.header-actions { display: flex; gap: 6px; }
</style>
