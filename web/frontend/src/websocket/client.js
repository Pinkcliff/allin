import { useDeviceStore } from '@/store/device'

class WebSocketClient {
  constructor() {
    this.ws = null
    this.reconnectTimer = null
    this.heartbeatTimer = null
    this.subscribedChannels = new Set()
    this.messageHandlers = {}
    this.deviceStore = null
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    this.ws = new WebSocket(wsUrl)
    this.deviceStore = useDeviceStore()

    this.ws.onopen = () => {
      console.log('WebSocket连接成功')
      this.deviceStore.setWebSocketConnected(true)

      // 清除重连定时器
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }

      // 重新订阅频道
      if (this.subscribedChannels.size > 0) {
        this.subscribe(Array.from(this.subscribedChannels))
      }

      // 启动心跳
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (e) {
        console.error('解析消息失败:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket连接关闭')
      this.deviceStore.setWebSocketConnected(false)

      // 停止心跳
      this.stopHeartbeat()

      // 自动重连
      this.reconnectTimer = setTimeout(() => {
        console.log('尝试重新连接...')
        this.connect()
      }, 3000)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  subscribe(channels) {
    channels.forEach(channel => {
      this.subscribedChannels.add(channel)
    })

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channels: channels
      }))
    }
  }

  unsubscribe(channels) {
    channels.forEach(channel => {
      this.subscribedChannels.delete(channel)
    })

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        channels: channels
      }))
    }
  }

  on(channel, handler) {
    if (!this.messageHandlers[channel]) {
      this.messageHandlers[channel] = []
    }
    this.messageHandlers[channel].push(handler)
  }

  off(channel, handler) {
    if (this.messageHandlers[channel]) {
      this.messageHandlers[channel] = this.messageHandlers[channel].filter(h => h !== handler)
    }
  }

  handleMessage(message) {
    const { type, data } = message

    // 更新store
    if (type === 'device_status') {
      this.deviceStore.setDeviceStatus(data)
    } else if (type === 'environment') {
      this.deviceStore.setEnvironment(data)
    } else if (type === 'power') {
      this.deviceStore.setPower(data)
    }

    // 调用注册的处理器
    if (this.messageHandlers[type]) {
      this.messageHandlers[type].forEach(handler => handler(data))
    }
  }

  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

// 创建全局实例
export const wsClient = new WebSocketClient()
