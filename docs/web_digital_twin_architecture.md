# Web端数字孪生系统架构设计

## 一、需求总结

| 需求项 | 说明 |
|--------|------|
| 3D展示 | 不需要，保持与现有桌面应用一致的2D界面 |
| 实时性 | 先实现基础版本，后续优化 |
| 控制功能 | 风扇阵列、俯仰/造雨/喷雾、PLC参数设置 |
| 用户规模 | 几人，局域网访问 |
| 权限管理 | 操作员/观察员/管理员三级权限 |
| 数据存储 | Redis(实时) + MongoDB(历史)，与现有系统共用 |
| 部署环境 | Windows服务器 |
| 兼容性 | 保留原有桌面客户端 |

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web前端 (Browser)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ 监控大屏    │ │ 控制面板    │ │ 数据查看    │ │ 系统设置  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              WebSocket          REST API
                    │                   │
┌─────────────────────────────────────────────────────────────────┐
│                      Python后端 (FastAPI)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ WebSocket   │ │ REST API    │ │ 权限管理    │ │ 业务逻辑  │ │
│  │ Server      │ │ Handler     │ │ (JWT)       │ │ Layer     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌────────▼────────┐    ┌───────▼──────┐
│    Redis     │    │    MongoDB      │    │  硬件设备     │
│  (实时数据)   │    │   (历史数据)     │    │  (PLC/动捕)  │
└──────────────┘    └─────────────────┘    └──────────────┘
```

### 2.2 技术栈选型

#### 后端
| 组件 | 技术 | 说明 |
|------|------|------|
| Web框架 | FastAPI | 高性能异步框架，自带WebSocket支持 |
| 数据库客户端 | redis-py, pymongo | Redis和MongoDB客户端 |
| PLC通信 | python-snap7 | 西门子S7通信 |
| 异步任务 | asyncio | 异步IO处理 |

#### 前端
| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue.js 3 | 渐进式框架，易于上手 |
| UI组件库 | Element Plus | 企业级UI组件库 |
| 图表库 | ECharts | 丰富的图表类型 |
| WebSocket | 原生WebSocket API | 实时数据推送 |
| 状态管理 | Pinia | Vue官方状态管理 |

---

## 三、目录结构设计

```
allin/
├── src/                          # 现有桌面应用代码（保留）
│   ├── dashboard/
│   └── modules/
│
├── web/                          # 新增Web应用代码
│   ├── backend/                  # 后端代码
│   │   ├── main.py              # FastAPI应用入口
│   │   ├── config.py            # 配置文件
│   │   ├── requirements.txt     # 后端依赖
│   │   │
│   │   ├── api/                 # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 认证相关API
│   │   │   ├── system.py        # 系统状态API
│   │   │   ├── device.py        # 设备控制API
│   │   │   ├── fan.py           # 风扇控制API
│   │   │   ├── env.py           # 环境控制API
│   │   │   ├── plc.py           # PLC监控API
│   │   │   ├── motion.py        # 动捕数据API
│   │   │   └── sensor.py        # 传感器数据API
│   │   │
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py  # 认证服务
│   │   │   ├── device_service.py # 设备服务
│   │   │   ├── fan_service.py   # 风扇服务
│   │   │   ├── plc_service.py   # PLC服务
│   │   │   ├── motion_service.py # 动捕服务
│   │   │   └── sensor_service.py # 传感器服务
│   │   │
│   │   ├── models/              # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # 用户模型
│   │   │   └── device.py        # 设备模型
│   │   │
│   │   ├── websocket/           # WebSocket处理
│   │   │   ├── __init__.py
│   │   │   ├── manager.py       # 连接管理器
│   │   │   └── handlers.py      # 消息处理器
│   │   │
│   │   └── utils/               # 工具函数
│   │       ├── __init__.py
│   │       ├── security.py      # 加密相关
│   │       └── logger.py        # 日志工具
│   │
│   └── frontend/                # 前端代码
│       ├── package.json         # 前端依赖配置
│       ├── vite.config.js       # Vite配置
│       │
│       ├── src/
│       │   ├── main.js          # 应用入口
│       │   ├── App.vue          # 根组件
│       │   │
│       │   ├── router/          # 路由配置
│       │   │   └── index.js
│       │   │
│       │   ├── store/           # Pinia状态管理
│       │   │   ├── index.js
│       │   │   ├── user.js      # 用户状态
│       │   │   └── device.js    # 设备状态
│       │   │
│       │   ├── api/             # API调用封装
│       │   │   ├── index.js
│       │   │   ├── auth.js
│       │   │   ├── device.js
│       │   │   └── data.js
│       │   │
│       │   ├── views/           # 页面组件
│       │   │   ├── Login.vue    # 登录页
│       │   │   ├── Dashboard.vue # 监控大屏
│       │   │   ├── FanControl.vue # 风扇控制
│       │   │   ├── EnvControl.vue # 环境控制
│       │   │   ├── PLCMonitor.vue # PLC监控
│       │   │   ├── MotionView.vue # 动捕查看
│       │   │   ├── SensorData.vue # 传感器数据
│       │   │   └── Settings.vue  # 系统设置
│       │   │
│       │   ├── components/      # 公共组件
│       │   │   ├── common/
│       │   │   │   ├── Header.vue
│       │   │   │   └── Sidebar.vue
│       │   │   ├── charts/
│       │   │   │   ├── RealTimeChart.vue
│       │   │   │   └── StatusChart.vue
│       │   │   └── widgets/
│       │   │       ├── CommIndicator.vue
│       │   │       ├── EnvironmentCard.vue
│       │   │       └── DeviceStatus.vue
│       │   │
│       │   ├── websocket/       # WebSocket客户端
│       │   │   └── client.js
│       │   │
│       │   └── assets/          # 静态资源
│       │       ├── styles/
│       │       └── images/
│       │
│       └── dist/                # 构建输出
│
├── data/                        # 数据目录
├── docs/                        # 文档
├── startup.bat                  # 桌面应用启动
├── startup_web.bat              # Web应用启动（新增）
└── README.md
```

---

## 四、核心功能设计

### 4.1 用户权限管理

| 角色 | 权限 |
|------|------|
| 观察员 | 只读访问所有监控数据 |
| 操作员 | 可查看数据 + 控制设备 |
| 管理员 | 全部权限 + 用户管理 |

### 4.2 实时数据推送

使用WebSocket推送以下数据：

| 数据类型 | 推送频率 | 说明 |
|----------|----------|------|
| 设备状态 | 1秒 | 设备开关、健康状态 |
| 通讯状态 | 1秒 | 各协议通讯指示 |
| 环境数据 | 1秒 | 温度、湿度、气压 |
| 电力数据 | 1秒 | 电流、电压、功率 |
| PLC数据 | 按配置 | 编码器、点表数据 |
| 动捕数据 | 高频 | 实时位置数据 |
| 传感器数据 | 按配置 | 传感器采集数据 |

### 4.3 页面功能规划

```
登录页
└── 监控大屏（Dashboard）
    ├── 系统概览卡片（设备状态、通讯状态）
    ├── 环境监控卡片（温湿度、气压）
    ├── 电力监控曲线（电流、电压、功率）
    └── 实时日志显示
└── 风扇控制
    ├── 风扇阵列视图（40×40）
    ├── 批量控制（全部开启/关闭）
    ├── 区域选择控制
    └── 单风扇设置
└── 环境控制
    ├── 俯仰伺服控制
    ├── 造雨系统控制
    └── 喷雾系统控制
└── PLC监控
    ├── 编码器监控
    ├── 点表监控
    └── 实时曲线
└── 动捕查看
    ├── 相机状态指示
    ├── 实时数据显示
    └── 历史数据回放
└── 传感器数据
    ├── 数据采集控制
    ├── 采集列表
    ├── 数据查看
    └── MongoDB查询
└── 系统设置
    ├── 通讯协议设置
    ├── 用户管理
    └── 系统参数配置
```

---

## 五、API接口设计

### 5.1 认证接口

```
POST   /api/auth/login       # 用户登录
POST   /api/auth/logout      # 用户登出
GET    /api/auth/profile     # 获取用户信息
PUT    /api/auth/profile     # 更新用户信息
```

### 5.2 设备控制接口

```
GET    /api/device/status          # 获取设备状态
POST   /api/device/power           # 设备开关
PUT    /api/device/config          # 设备配置
```

### 5.3 风扇控制接口

```
GET    /api/fan/status             # 风扇阵列状态
POST   /api/fan/power              # 全部开关
POST   /api/fan/area               # 区域控制
PUT    /api/fan/single             # 单风扇设置
GET    /api/fan/template           # 获取模板列表
POST   /api/fan/template           # 保存模板
```

### 5.4 环境控制接口

```
GET    /api/env/status             # 环境设备状态
POST   /api/env/pitch              # 俯仰控制
POST   /api/env/rain               # 造雨控制
POST   /api/env/spray              # 喷雾控制
```

### 5.5 PLC监控接口

```
GET    /api/plc/status             # PLC连接状态
GET    /api/plc/encoder            # 编码器数据
GET    /api/plc/point              # 点表数据
```

### 5.6 动捕接口

```
GET    /api/motion/status          # 动捕系统状态
GET    /api/motion/cameras         # 相机列表
GET    /api/motion/data            # 实时数据
```

### 5.7 传感器接口

```
GET    /api/sensor/collections     # 采集列表
POST   /api/sensor/start           # 开始采集
POST   /api/sensor/stop            # 停止采集
GET    /api/sensor/data            # 获取采集数据
```

---

## 六、WebSocket消息协议

### 6.1 客户端 → 服务器

```json
{
  "type": "subscribe",     // 订阅数据类型
  "channels": ["device", "env", "power", "plc", "motion"]
}
```

### 6.2 服务器 → 客户端

```json
{
  "type": "device_status",   // 消息类型
  "timestamp": 1234567890,
  "data": {
    "device_on": true,
    "health": "normal"
  }
}
```

---

## 七、开发计划

### 第一阶段：基础框架搭建
1. 创建Web目录结构
2. 搭建FastAPI后端框架
3. 搭建Vue3前端框架
4. 实现用户登录和权限管理

### 第二阶段：核心功能开发
1. 实现WebSocket实时数据推送
2. 实现监控大屏（设备状态、环境、电力）
3. 实现风扇控制功能
4. 实现环境控制功能

### 第三阶段：扩展功能开发
1. 实现PLC监控
2. 实现动捕查看
3. 实现传感器数据查看
4. 实现历史数据回放

### 第四阶段：优化和部署
1. 性能优化
2. 安全加固
3. 部署文档编写
4. 用户手册编写

---

## 八、启动脚本

### startup_web.bat

```batch
@echo off
echo Starting Web Digital Twin System...
echo.

REM Activate my_env environment
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

REM Start backend server
start "Backend Server" cmd /k "cd /d F:\A-User\cliff\allin\web\backend && python main.py"

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend (optional, can also use npm run dev)
start "Frontend Server" cmd /k "cd /d F:\A-User\cliff\allin\web\frontend && npm run dev"

echo.
echo Web System Starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
pause
```

---

## 九、依赖清单

### 后端依赖 (requirements.txt)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
pymongo==4.6.0
python-snap7==1.3
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

### 前端依赖 (package.json)

```json
{
  "dependencies": {
    "vue": "^3.3.8",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.4.4",
    "echarts": "^5.4.3",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "vite": "^5.0.4"
  }
}
```

---

## 十、注意事项

1. **与现有系统的兼容性**
   - 复用现有的Redis和MongoDB数据结构
   - 复用现有的PLC通信、动捕等模块代码

2. **安全性**
   - 使用JWT进行认证
   - 敏感操作需要二次确认
   - 控制操作记录日志

3. **性能考虑**
   - WebSocket连接管理，避免连接泄漏
   - 高频数据（如动捕）考虑节流推送
   - 大量数据使用分页查询

4. **可维护性**
   - 模块化设计，便于扩展
   - 统一的错误处理和日志记录
   - API文档自动生成（FastAPI自带）
