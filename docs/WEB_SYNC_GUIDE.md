# 桌面端与Web端数据同步指南

## 概述

本文档说明如何实现桌面端和Web端的实时数据同步。

## 同步机制

### 1. 架构说明

```
桌面端 (PySide6)
    ↓ 数据变化
Web同步客户端 (HTTP POST)
    ↓
Web后端 (FastAPI)
    ↓ WebSocket推送
Web前端 (Vue.js)
```

### 2. 同步流程

1. **桌面端数据变化** → 调用Web同步客户端
2. **Web同步客户端** → 发送HTTP POST到Web后端API
3. **Web后端** → 接收数据并通过WebSocket广播
4. **Web前端** → 订阅WebSocket频道，接收实时更新

### 3. 已实现的同步API

| API端点 | 功能 | 数据格式 |
|---------|------|----------|
| `/api/fan/sync` | 风扇状态同步 | `{"fans": [...], "timestamp": ...}` |
| `/api/env/sync` | 环境数据同步 | `{"temperature": ..., "humidity": ..., "pressure": ...}` |
| `/api/sensor/sync` | 传感器数据同步 | `{"sensors": [...], "timestamp": ...}` |
| `/api/plc/sync` | PLC状态同步 | `{"connected": ..., "status": {...}}` |
| `/api/device/sync` | 设备状态同步 | `{"devices": [...], "timestamp": ...}` |

### 4. 桌面端集成示例

```python
from modules.core.data_sync.web_sync_client import get_web_sync_client

# 获取同步客户端
sync_client = get_web_sync_client()

# 同步风扇状态
sync_client.sync_fan_status(fans_data)

# 同步环境数据
sync_client.sync_environment(temperature=25.0, humidity=60.0, pressure=101325.0)

# 同步传感器数据
sync_client.sensor_update(sensors_data)
```

### 5. Web前端订阅示例

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// 订阅频道
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['device_status', 'environment', 'power']
  }));
};

// 接收数据更新
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Channel:', message.type);
  console.log('Data:', message.data);

  // 根据频道类型更新UI
  switch(message.type) {
    case 'environment':
      updateEnvironmentDisplay(message.data);
      break;
    case 'device_status':
      updateDeviceStatus(message.data);
      break;
    // ...
  }
};
```

## 测试同步功能

### 测试步骤

1. **启动Web后端和前端**
   ```bash
   # 运行一键启动.bat
   ```

2. **打开Web浏览器**
   访问 http://localhost:5174

3. **打开桌面端**
   点击"集成系统"菜单启动桌面客户端

4. **测试数据同步**
   - 在桌面端修改风扇状态
   - 观察Web端是否同步更新

### 验证要点

- [ ] 桌面端数据变化时，Web后端日志显示同步请求
- [ ] Web前端接收到WebSocket推送消息
- [ ] Web前端UI实时更新显示同步的数据

## 故障排查

### 问题1: Web端数据不更新

**检查项:**
1. Web后端是否正常运行（http://localhost:8000）
2. 桌面端是否能连接到Web后端
3. WebSocket连接是否建立

**解决方案:**
```bash
# 检查后端状态
curl http://localhost:8000/health

# 检查WebSocket连接
# 在浏览器控制台查看ws连接状态
```

### 问题2: 同步延迟过高

**原因:**
- 网络延迟
- 同步队列阻塞

**解决方案:**
- 调整同步间隔
- 优化数据量大小

## 下一步优化

1. **增加数据缓存** - 减少重复同步
2. **批量同步** - 合并多个数据更新
3. **错误重试** - 处理网络失败情况
4. **数据压缩** - 减少传输数据量

## 总结

通过这个同步机制，桌面端和Web端可以实现实时数据同步，确保两个界面显示的数据一致。
