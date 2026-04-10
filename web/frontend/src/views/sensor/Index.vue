<template>
  <div class="sensor-data-page">
    <!-- 数据采集控制 -->
    <div class="card mb-16">
      <div class="card-header">数据采集控制</div>
      <div class="card-body">
        <el-form :inline="true" @submit.prevent="startCollection">
          <el-form-item label="采集名称">
            <el-input v-model="collectionForm.name" placeholder="请输入采集名称" style="width: 200px" />
          </el-form-item>
          <el-form-item label="时长(秒)">
            <el-input-number v-model="collectionForm.duration" :min="1" :max="3600" style="width: 120px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="startCollection" :loading="loading.collecting" :disabled="isCollecting">
              <el-icon><VideoPlay /></el-icon>
              开始采集
            </el-button>
            <el-button type="danger" @click="stopCollection" :loading="loading.collecting" :disabled="!isCollecting">
              <el-icon><VideoPause /></el-icon>
              停止采集
            </el-button>
          </el-form-item>
        </el-form>
        <div v-if="isCollecting" class="collecting-status">
          <el-progress :percentage="collectingProgress" :status="collectingProgress >= 100 ? 'success' : undefined" />
          <span class="time-info">剩余时间: {{ remainingTime }}秒</span>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab">
      <el-tab-pane label="采集列表" name="collections">
        <div class="card">
          <div class="card-header">
            <span>采集记录</span>
            <el-button size="small" @click="refreshCollections" :loading="loading.refresh">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          <div class="card-body">
            <el-table :data="collections" size="small" stripe>
              <el-table-column prop="collection_id" label="采集ID" width="150" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="created_at" label="创建时间" width="180" />
              <el-table-column prop="sample_count" label="样本数" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                    {{ row.status === 'completed' ? '完成' : '采集中' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="viewCollection(row)">查看</el-button>
                  <el-button size="small" type="danger" @click="deleteCollection(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据查看" name="view">
        <div class="card">
          <div class="card-header">
            <span>采集数据详情</span>
            <div v-if="currentCollection">
              <span class="collection-info">{{ currentCollection.name }} ({{ currentCollection.collection_id }})</span>
            </div>
          </div>
          <div class="card-body">
            <el-empty v-if="!currentCollection" description="请先选择一个采集记录" />
            <div v-else>
              <el-table :data="collectionData" size="small" stripe max-height="400">
                <el-table-column prop="timestamp" label="时间戳" width="180" />
                <el-table-column label="风扇数据" width="200">
                  <template #default="{ row }">
                    <span v-if="row.fans">均值: {{ (row.fans.reduce((a, b) => a + b, 0) / row.fans.length).toFixed(1) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="温度数据" width="200">
                  <template #default="{ row }">
                    <span v-if="row.temp_sensors">均值: {{ (row.temp_sensors.reduce((a, b) => a + b, 0) / row.temp_sensors.length).toFixed(1) }}°C</span>
                  </template>
                </el-table-column>
                <el-table-column label="湿度数据" width="200">
                  <template #default="{ row }">
                    <span v-if="row.humidity_sensors">均值: {{ (row.humidity_sensors.reduce((a, b) => a + b, 0) / row.humidity_sensors.length).toFixed(1) }}%</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="MongoDB同步" name="mongo">
        <div class="card">
          <div class="card-header">数据同步</div>
          <div class="card-body">
            <el-space direction="vertical" style="width: 100%">
              <div class="sync-info">
                <p>将Redis中的采集数据同步到MongoDB进行持久化存储。</p>
              </div>
              <el-button type="primary" @click="syncToMongoDB" :loading="loading.sync">
                <el-icon><Refresh /></el-icon>
                同步到MongoDB
              </el-button>
              <div v-if="syncResult" class="sync-result">
                <el-descriptions :column="3" border>
                  <el-descriptions-item label="采集数">{{ syncResult.collections }}</el-descriptions-item>
                  <el-descriptions-item label="样本数">{{ syncResult.samples }}</el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag type="success">成功</el-tag>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-space>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 数据查看对话框 -->
    <el-dialog v-model="viewDialogVisible" title="采集数据" width="80%">
      <el-table :data="viewData" size="small" stripe max-height="500">
        <el-table-column prop="timestamp" label="时间戳" width="180" />
        <el-table-column label="数据" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { sensorApi } from '@/api/data'

// 数据
const collections = ref([])
const currentCollection = ref(null)
const collectionData = ref([])
const viewData = ref([])
const viewDialogVisible = ref(false)
const syncResult = ref(null)
const loading = ref({
  collecting: false,
  refresh: false,
  sync: false
})

// 采集表单
const collectionForm = ref({
  name: '',
  duration: 60
})

// 采集状态
const isCollecting = ref(false)
const collectingProgress = ref(0)
const remainingTime = ref(0)
const activeTab = ref('collections')
let collectingTimer = null

// 获取采集列表
const refreshCollections = async () => {
  loading.value.refresh = true
  try {
    const res = await sensorApi.getCollections()
    collections.value = res.collections || []
  } catch (error) {
    ElMessage.error('获取采集列表失败')
  } finally {
    loading.value.refresh = false
  }
}

// 开始采集
const startCollection = async () => {
  if (!collectionForm.value.name) {
    ElMessage.warning('请输入采集名称')
    return
  }

  loading.value.collecting = true
  try {
    const res = await sensorApi.startCollection(collectionForm.value)
    ElMessage.success(`采集已开始: ${res.collection_id}`)
    isCollecting.value = true
    remainingTime.value = collectionForm.value.duration
    collectingProgress.value = 0

    // 启动倒计时
    collectingTimer = setInterval(() => {
      remainingTime.value--
      collectingProgress.value = ((collectionForm.value.duration - remainingTime.value) / collectionForm.value.duration) * 100

      if (remainingTime.value <= 0) {
        clearInterval(collectingTimer)
        collectingTimer = null
        isCollecting.value = false
        collectingProgress.value = 100
        ElMessage.success('采集完成')
        refreshCollections()
      }
    }, 1000)
  } catch (error) {
    ElMessage.error('开始采集失败')
  } finally {
    loading.value.collecting = false
  }
}

// 停止采集
const stopCollection = async () => {
  loading.value.collecting = true
  try {
    await sensorApi.stopCollection()
    ElMessage.success('采集已停止')
    isCollecting.value = false
    if (collectingTimer) {
      clearInterval(collectingTimer)
      collectingTimer = null
    }
    refreshCollections()
  } catch (error) {
    ElMessage.error('停止采集失败')
  } finally {
    loading.value.collecting = false
  }
}

// 查看采集
const viewCollection = async (row) => {
  currentCollection.value = row
  activeTab.value = 'view'

  loading.value.refresh = true
  try {
    const res = await sensorApi.getData(row.collection_id, { start: 0, end: 100 })
    collectionData.value = res.data || []
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value.refresh = false
  }
}

// 删除采集
const deleteCollection = async (row) => {
  await ElMessageBox.confirm(`确定要删除采集 ${row.collection_id} 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })

  try {
    await sensorApi.deleteCollection(row.collection_id)
    ElMessage.success('删除成功')
    refreshCollections()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 同步到MongoDB
const syncToMongoDB = async () => {
  loading.value.sync = true
  syncResult.value = null
  try {
    const res = await sensorApi.syncToMongoDB()
    syncResult.value = res
    ElMessage.success('同步成功')
  } catch (error) {
    ElMessage.error('同步失败')
  } finally {
    loading.value.sync = false
  }
}

onMounted(() => {
  refreshCollections()
})
</script>

<style scoped>
.sensor-data-page {
  height: 100%;
  overflow-y: auto;
}

.mb-16 {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-body {
  padding: 16px;
}

.collecting-status {
  margin-top: 16px;
}

.time-info {
  display: block;
  margin-top: 8px;
  color: #8a8f98;
  font-size: 12px;
}

.collection-info {
  margin-right: 16px;
  color: #8a8f98;
  font-size: 14px;
}

.sync-info {
  padding: 16px;
  background: rgba(0, 209, 255, 0.1);
  border: 1px solid rgba(0, 209, 255, 0.3);
  border-radius: 4px;
}

.sync-info p {
  margin: 0;
  color: #e1e1e6;
}

.sync-result {
  margin-top: 16px;
}
</style>
