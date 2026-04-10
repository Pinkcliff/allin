import request from './index'

export const systemApi = {
  // 获取系统状态
  getStatus() {
    return request.get('/system/status')
  },

  // 获取设备状态
  getDevices() {
    return request.get('/system/devices')
  },

  // 获取通讯状态
  getCommunications() {
    return request.get('/system/communications')
  },

  // 获取环境数据
  getEnvironment() {
    return request.get('/system/environment')
  },

  // 获取电力数据
  getPower() {
    return request.get('/system/power')
  },

  // 获取日志
  getLogs(limit = 100) {
    return request.get('/system/logs', { params: { limit } })
  }
}

export const deviceApi = {
  // 获取设备状态
  getStatus() {
    return request.get('/device/status')
  },

  // 控制设备电源
  setPower(device_on) {
    return request.post('/device/power', { device_on })
  }
}

export const fanApi = {
  // 获取风扇状态
  getStatus() {
    return request.get('/fan/status')
  },

  // 全部开关
  setPower(power_on) {
    return request.post('/fan/power', { power_on })
  },

  // 区域控制
  setArea(data) {
    return request.post('/fan/area', data)
  },

  // 单风扇设置
  setSingle(data) {
    return request.put('/fan/single', data)
  },

  // 获取模板
  getTemplates() {
    return request.get('/fan/templates')
  },

  // 保存模板
  saveTemplate(data) {
    return request.post('/fan/template', data)
  }
}

export const envApi = {
  // 获取环境设备状态
  getStatus() {
    return request.get('/env/status')
  },

  // 俯仰控制
  controlPitch(data) {
    return request.post('/env/pitch', data)
  },

  // 造雨控制
  controlRain(data) {
    return request.post('/env/rain', data)
  },

  // 停止造雨
  stopRain() {
    return request.post('/env/rain/stop')
  },

  // 喷雾控制
  controlSpray(data) {
    return request.post('/env/spray', data)
  },

  // 停止喷雾
  stopSpray() {
    return request.post('/env/spray/stop')
  }
}

export const plcApi = {
  // 获取PLC状态
  getStatus() {
    return request.get('/plc/status')
  },

  // 获取编码器数据
  getEncoderData(encoder_id) {
    return request.get('/plc/encoder', { params: { encoder_id } })
  },

  // 获取点表数据
  getPointData(point_name) {
    return request.get('/plc/point', { params: { point_name } })
  },

  // 获取历史数据
  getHistory(encoder_id, params) {
    return request.get(`/plc/history/encoder/${encoder_id}`, { params })
  }
}

export const motionApi = {
  // 获取动捕状态
  getStatus() {
    return request.get('/motion/status')
  },

  // 获取相机状态
  getCameras() {
    return request.get('/motion/cameras')
  },

  // 获取实时数据
  getData(params) {
    return request.get('/motion/data', { params })
  },

  // 开始录制
  startRecording() {
    return request.post('/motion/recording/start')
  },

  // 停止录制
  stopRecording() {
    return request.post('/motion/recording/stop')
  }
}

export const sensorApi = {
  // 获取采集列表
  getCollections() {
    return request.get('/sensor/collections')
  },

  // 开始采集
  startCollection(data) {
    return request.post('/sensor/start', data)
  },

  // 停止采集
  stopCollection() {
    return request.post('/sensor/stop')
  },

  // 获取采集数据
  getData(collection_id, params) {
    return request.get(`/sensor/data/${collection_id}`, { params })
  },

  // 获取采集元数据
  getMeta(collection_id) {
    return request.get(`/sensor/meta/${collection_id}`)
  },

  // 删除采集
  deleteCollection(collection_id) {
    return request.delete(`/sensor/data/${collection_id}`)
  },

  // 同步到MongoDB
  syncToMongoDB() {
    return request.get('/sensor/sync/mongodb')
  }
}
