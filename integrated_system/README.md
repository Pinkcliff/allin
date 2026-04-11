# 整合系统 v2.0

## 概述

整合系统将桌面客户端（PySide6）和Web数字孪生系统集成到一个统一平台中。

## 系统架构

```
整合系统主程序
├── 桌面客户端 (PySide6)
│   ├── 全局监控仪表盘
│   ├── 风扇控制
│   ├── 环境控制
│   ├── PLC监控
│   ├── 动捕查看
│   └── 传感器数据
│
└── Web数字孪生 (Vue3 + FastAPI)
    ├── 前端界面 (http://localhost:5174)
    └── 后端API (http://localhost:8000)
```

## 数据同步

桌面客户端和Web端通过以下方式实现实时同步：

1. **同步API**: 桌面客户端通过HTTP POST发送数据到后端同步接口
2. **WebSocket推送**: 后端接收到同步数据后，通过WebSocket推送到所有Web客户端
3. **实时更新**: Web端接收WebSocket消息后立即更新界面

## 使用方法

### 1. 安装依赖

```bash
# 后端依赖
cd web/backend
pip install -r requirements.txt

# 前端依赖
cd web/frontend
npm install
```

### 2. 启动整合系统

```bash
cd F:/A-User/cliff/allin
python integrated_system/main.py
```

### 3. 操作界面

启动后会看到整合平台主界面，包含三个选项：

- **桌面客户端**: 启动PySide6原生界面
- **Web数字孪生**: 在浏览器中打开Web界面
- **同时启动**: 同时启动桌面客户端和浏览器

## 功能特性

### 桌面客户端
- 原生PySide6界面
- 完整的仪表盘功能
- 所有控制模块
- 本地数据存储

### Web数字孪生
- 基于浏览器的访问
- 响应式设计
- 支持多终端访问
- 实时数据更新

### 数据同步
- 风扇状态同步
- 环境数据同步
- PLC状态同步
- 传感器数据同步
- 动捕数据同步

## 技术栈

### 后端
- FastAPI (Web框架)
- WebSocket (实时通信)
- Pydantic (数据验证)
- python-jose (JWT认证)

### 前端
- Vue 3
- Element Plus (UI组件)
- ECharts (图表)
- Pinia (状态管理)
- Vue Router (路由)

### 桌面
- PySide6 (Qt绑定)
- Python 3.7+

## 默认账户

- 管理员: admin / admin123
- 操作员: operator / operator123
- 访客: viewer / viewer123

## 端口配置

- 后端API: 8000
- 前端界面: 5173/5174 (自动选择可用端口)
- WebSocket: ws://localhost:8000/ws
