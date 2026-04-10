<template>
  <div class="fan-control-page">
    <!-- 顶部控制栏 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="6">
        <div class="card">
          <div class="card-header">风扇状态</div>
          <div class="card-body">
            <div class="status-row">
              <span class="label">总数：</span>
              <span class="value">{{ fanStatus?.total_fans || 1600 }}</span>
            </div>
            <div class="status-row">
              <span class="label">在线：</span>
              <span class="value success">{{ fanStatus?.online_fans || 1600 }}</span>
            </div>
            <div class="status-row">
              <span class="label">运行中：</span>
              <span class="value active">{{ fanStatus?.active_fans || 0 }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="card">
          <div class="card-header">快捷操作</div>
          <div class="card-body">
            <el-space>
              <el-button type="success" @click="setAllPower(true)" :loading="loading">
                <el-icon><VideoPlay /></el-icon>
                全部开启
              </el-button>
              <el-button type="danger" @click="setAllPower(false)" :loading="loading">
                <el-icon><VideoPause /></el-icon>
                全部关闭
              </el-button>
              <el-button @click="refreshStatus">
                <el-icon><Refresh /></el-icon>
                刷新状态
              </el-button>
            </el-space>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="card">
          <div class="card-header">模板</div>
          <div class="card-body">
            <el-select v-model="selectedTemplate" placeholder="选择模板" @change="applyTemplate" style="width: 100%">
              <el-option label="均匀分布" value="uniform" />
              <el-option label="中心聚焦" value="center" />
              <el-option label="梯度分布" value="gradient" />
              <el-option label="随机分布" value="random" />
            </el-select>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 风扇阵列视图 -->
    <div class="card">
      <div class="card-header">
        <span>风扇阵列 (40×40)</span>
        <div class="header-actions">
          <el-button size="small" @click="toggleAreaMode">
            {{ areaMode ? '退出区域模式' : '区域选择' }}
          </el-button>
          <el-button size="small" @click="clearSelection" v-if="selectedCells.size > 0">
            清除选择 ({{ selectedCells.size }})
          </el-button>
        </div>
      </div>
      <div class="card-body">
        <!-- 风扇网格 -->
        <div class="fan-grid-container">
          <div class="fan-grid" :class="{ 'area-mode': areaMode }">
            <div
              v-for="(row, y) in fanArray"
              :key="y"
              class="fan-row"
            >
              <div
                v-for="(cell, x) in row"
                :key="`${x}-${y}`"
                class="fan-cell"
                :class="{
                  'active': cell === 1,
                  'selected': isCellSelected(x, y),
                  'in-area': isCellInArea(x, y)
                }"
                @click="handleCellClick(x, y)"
                @mouseenter="handleCellEnter(x, y)"
                :title="`(${x}, ${y})${cell ? ' - 运行中' : ' - 已停止'}`"
              ></div>
            </div>
          </div>
        </div>

        <!-- 区域控制面板 -->
        <div v-if="areaMode || selectedCells.size > 0" class="area-control-panel">
          <div class="panel-title">
            区域控制
            <span v-if="selectedCells.size > 0">（已选择 {{ selectedCells.size }} 个风扇）</span>
          </div>
          <div class="panel-content">
            <el-form :inline="true">
              <el-form-item label="转速">
                <el-slider
                  v-model="areaRpm"
                  :min="0"
                  :max="15000"
                  :step="100"
                  :marks="{ 0: '0', 5000: '5K', 10000: '10K', 15000: '15K' }"
                  style="width: 300px"
                />
                <el-input-number
                  v-model="areaRpm"
                  :min="0"
                  :max="15000"
                  :step="100"
                  style="width: 120px; margin-left: 10px"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="applyAreaControl" :loading="loading">
                  应用
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>

    <!-- 单风扇设置对话框 -->
    <el-dialog v-model="singleFanDialogVisible" title="单风扇设置" width="400px">
      <el-form :model="singleFanForm" label-width="80px">
        <el-form-item label="位置">
          <el-input :value="`(${singleFanForm.x}, ${singleFanForm.y})`" disabled />
        </el-form-item>
        <el-form-item label="转速">
          <el-slider
            v-model="singleFanForm.rpm"
            :min="0"
            :max="15000"
            :step="100"
            :marks="{ 0: '0', 5000: '5K', 10000: '10K', 15000: '15K' }"
          />
          <el-input-number
            v-model="singleFanForm.rpm"
            :min="0"
            :max="15000"
            :step="100"
            style="width: 120px; margin-top: 10px"
          />
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fanApi } from '@/api/data'

// 数据
const fanStatus = ref(null)
const fanArray = ref([])  // 40x40 array
const loading = ref(false)
const selectedTemplate = ref('')

// 区域选择
const areaMode = ref(false)
const selectedCells = ref(new Set())
const areaStart = ref(null)
const areaRpm = ref(5000)

// 单风扇设置
const singleFanDialogVisible = ref(false)
const singleFanForm = ref({
  x: 0,
  y: 0,
  rpm: 5000
})

// 初始化风扇阵列
const initFanArray = () => {
  const arr = []
  for (let y = 0; y < 40; y++) {
    const row = []
    for (let x = 0; x < 40; x++) {
      row.push(0)
    }
    arr.push(row)
  }
  fanArray.value = arr
}

// 判断单元格是否被选中
const isCellSelected = (x, y) => {
  return selectedCells.value.has(`${x},${y}`)
}

// 判断单元格是否在当前选择区域内
const isCellInArea = (x, y) => {
  if (!areaStart.value) return false
  const start = areaStart.value
  const end = { x, y }
  const minX = Math.min(start.x, end.x)
  const maxX = Math.max(start.x, end.x)
  const minY = Math.min(start.y, end.y)
  const maxY = Math.max(start.y, end.y)
  return x >= minX && x <= maxX && y >= minY && y <= maxY
}

// 处理单元格点击
const handleCellClick = (x, y) => {
  if (areaMode.value) {
    if (!areaStart.value) {
      areaStart.value = { x, y }
    } else {
      // 完成区域选择
      const start = areaStart.value
      const minX = Math.min(start.x, x)
      const maxX = Math.max(start.x, x)
      const minY = Math.min(start.y, y)
      const maxY = Math.max(start.y, y)

      for (let py = minY; py <= maxY; py++) {
        for (let px = minX; px <= maxX; px++) {
          selectedCells.value.add(`${px},${py}`)
        }
      }
      areaStart.value = null
    }
  } else {
    // 单风扇设置
    singleFanForm.value = { x, y, rpm: 5000 }
    singleFanDialogVisible.value = true
  }
}

// 处理鼠标进入（用于区域选择预览）
const handleCellEnter = (x, y) => {
  // 可以在这里添加预览效果
}

// 切换区域模式
const toggleAreaMode = () => {
  areaMode.value = !areaMode.value
  areaStart.value = null
  if (!areaMode.value) {
    selectedCells.value.clear()
  }
}

// 清除选择
const clearSelection = () => {
  selectedCells.value.clear()
  areaStart.value = null
}

// 全部开关
const setAllPower = async (powerOn) => {
  loading.value = true
  try {
    await fanApi.setPower(powerOn)
    ElMessage.success(powerOn ? '所有风扇已开启' : '所有风扇已关闭')
    await refreshStatus()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

// 刷新状态
const refreshStatus = async () => {
  try {
    const res = await fanApi.getStatus()
    fanStatus.value = res
    fanArray.value = res.fan_array
  } catch (error) {
    ElMessage.error('获取状态失败')
  }
}

// 应用区域控制
const applyAreaControl = async () => {
  if (selectedCells.value.size === 0) {
    ElMessage.warning('请先选择风扇')
    return
  }

  loading.value = true
  try {
    // 找出选中区域的边界
    let minX = 40, maxX = 0, minY = 40, maxY = 0
    selectedCells.value.forEach(key => {
      const [x, y] = key.split(',').map(Number)
      minX = Math.min(minX, x)
      maxX = Math.max(maxX, x)
      minY = Math.min(minY, y)
      maxY = Math.max(maxY, y)
    })

    await fanApi.setArea({
      start_x: minX,
      start_y: minY,
      end_x: maxX,
      end_y: maxY,
      rpm: areaRpm.value
    })

    ElMessage.success(`已设置 ${selectedCells.value.size} 个风扇转速为 ${areaRpm.value}`)
    selectedCells.value.clear()
    await refreshStatus()
  } catch (error) {
    ElMessage.error('设置失败')
  } finally {
    loading.value = false
  }
}

// 应用单风扇设置
const applySingleFan = async () => {
  loading.value = true
  try {
    await fanApi.setSingle(singleFanForm.value)
    ElMessage.success(`风扇 (${singleFanForm.value.x}, ${singleFanForm.value.y}) 转速已设置为 ${singleFanForm.value.rpm}`)
    singleFanDialogVisible.value = false
    await refreshStatus()
  } catch (error) {
    ElMessage.error('设置失败')
  } finally {
    loading.value = false
  }
}

// 应用模板
const applyTemplate = async () => {
  loading.value = true
  try {
    // 生成模板数据
    let templateData
    switch (selectedTemplate.value) {
      case 'uniform':
        templateData = generateUniformTemplate()
        break
      case 'center':
        templateData = generateCenterTemplate()
        break
      case 'gradient':
        templateData = generateGradientTemplate()
        break
      case 'random':
        templateData = generateRandomTemplate()
        break
    }

    // 应用模板（分区域应用）
    for (let y = 0; y < 40; y += 5) {
      for (let x = 0; x < 40; x += 5) {
        await fanApi.setArea({
          start_x: x,
          start_y: y,
          end_x: Math.min(x + 4, 39),
          end_y: Math.min(y + 4, 39),
          rpm: templateData[y][x]
        })
      }
    }

    ElMessage.success('模板已应用')
    await refreshStatus()
  } catch (error) {
    ElMessage.error('应用模板失败')
  } finally {
    loading.value = false
  }
}

// 生成均匀分布模板
const generateUniformTemplate = () => {
  const arr = []
  for (let y = 0; y < 40; y++) {
    const row = []
    for (let x = 0; x < 40; x++) {
      row.push(8000)
    }
    arr.push(row)
  }
  return arr
}

// 生成中心聚焦模板
const generateCenterTemplate = () => {
  const arr = []
  const cx = 20, cy = 20
  for (let y = 0; y < 40; y++) {
    const row = []
    for (let x = 0; x < 40; x++) {
      const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
      const rpm = Math.max(2000, 15000 - dist * 500)
      row.push(rpm)
    }
    arr.push(row)
  }
  return arr
}

// 生成梯度分布模板
const generateGradientTemplate = () => {
  const arr = []
  for (let y = 0; y < 40; y++) {
    const row = []
    for (let x = 0; x < 40; x++) {
      const rpm = 3000 + (x / 39) * 12000
      row.push(rpm)
    }
    arr.push(row)
  }
  return arr
}

// 生成随机分布模板
const generateRandomTemplate = () => {
  const arr = []
  for (let y = 0; y < 40; y++) {
    const row = []
    for (let x = 0; x < 40; x++) {
      row.push(Math.floor(Math.random() * 15000))
    }
    arr.push(row)
  }
  return arr
}

onMounted(() => {
  initFanArray()
  refreshStatus()
})
</script>

<style scoped>
.fan-control-page {
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
  margin-bottom: 8px;
}

.status-row .label {
  color: #8a8f98;
  margin-right: 8px;
}

.status-row .value {
  font-size: 16px;
  font-weight: bold;
  color: #e1e1e6;
}

.status-row .value.success {
  color: #00ff7f;
}

.status-row .value.active {
  color: #00d1ff;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 风扇网格 */
.fan-grid-container {
  width: 100%;
  overflow: auto;
  padding: 16px;
  background: #1a1c23;
  border-radius: 4px;
}

.fan-grid {
  display: inline-block;
  background: #1a1c23;
  user-select: none;
}

.fan-grid.area-mode {
  cursor: crosshair;
}

.fan-row {
  display: flex;
}

.fan-cell {
  width: 12px;
  height: 12px;
  background: #3a3c43;
  border: 1px solid #2a2c33;
  cursor: pointer;
  transition: all 0.1s;
}

.fan-cell:hover {
  background: #4a4c53;
}

.fan-cell.active {
  background: #00d1ff;
}

.fan-cell.selected {
  background: #ffc800;
}

.fan-cell.in-area {
  background: rgba(0, 209, 255, 0.3);
}

/* 区域控制面板 */
.area-control-panel {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 209, 255, 0.1);
  border: 1px solid rgba(0, 209, 255, 0.3);
  border-radius: 4px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #00d1ff;
  margin-bottom: 12px;
}

.panel-content {
  display: flex;
  align-items: center;
}
</style>
