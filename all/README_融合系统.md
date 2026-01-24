# 融合系统使用说明

## 系统概述

本融合系统整合了两个主要项目：
1. **仪表盘系统** (from `frist`) - 全局监控仪表盘
2. **传感器数据采集系统** (from `setest`) - 传感器数据采集、查看和同步

## 目录结构

```
F:/A-User/cliff/allin/all/
├── main.py                          # 融合系统主入口
├── config.py                        # 统一配置文件
├── 核心模块/
│   ├── 数据采集/
│   │   ├── __init__.py
│   │   └── data_generator.py        # 传感器数据生成器
│   ├── 数据存储/
│   │   ├── __init__.py
│   │   └── redis_database.py        # Redis数据库操作
│   └── 数据同步/
│       ├── __init__.py
│       └── sync_to_mongo.py         # MongoDB数据同步
├── 仪表盘/
│   ├── main.py                      # 仪表盘独立入口
│   ├── ui_main_window.py            # 主窗口
│   ├── ui_sensor_collection.py      # 传感器数据采集和查看标签页
│   ├── ui_sensor_dock.py            # 传感器数据dock
│   └── ... (其他仪表盘模块)
└── test_imports.py                  # 模块导入测试脚本
```

## 依赖安装

运行融合系统需要安装以下依赖：

```bash
pip install PySide6 redis pymongo
```

或者使用 requirements.txt（如果有的话）。

## 使用方式

### 1. 启动融合系统启动器

```bash
cd F:/A-User/cliff/allin/all
python main.py
```

启动后，你将看到一个融合系统启动器窗口，提供三个选项：

- **全局监控仪表盘** - 启动纯仪表盘系统（不包含传感器数据采集）
- **融合系统（仪表盘+传感器）** - 启动包含所有功能的融合系统（推荐）
- **传感器数据采集** - 启动专注于传感器数据采集的系统

### 2. 直接启动仪表盘（原始方式）

```bash
cd F:/A-User/cliff/allin/all/仪表盘
python main.py
```

### 3. 使用传感器数据采集和查看功能

在仪表盘中，点击工具栏的"传感器数据"按钮即可打开传感器数据面板，包含两个标签页：

- **数据采集** - 配置和启动传感器数据采集任务
- **数据查看** - 查看历史采集记录和同步到MongoDB

## 功能说明

### 传感器数据采集

1. **数据采集标签页**：
   - 输入采集名称
   - 设置采集时长（秒）
   - 点击"开始采集"按钮启动数据采集
   - 实时查看采集进度和样本数据
   - 支持暂停/停止采集

2. **数据查看标签页**：
   - 查看所有历史采集记录
   - 查看采集数据的详细信息
   - 删除不需要的采集记录
   - 将Redis数据同步到MongoDB

### 传感器配置

系统模拟了以下传感器数据：
- 风扇PWM：1600个（范围：0-1000）
- 温度传感器：100个（范围：-20~80℃）
- 风速传感器：100个（范围：0~30m/s）
- 温湿度传感器：4个
- 大气压力传感器：1个
- 采样率：10次/秒

## 数据存储

- **Redis** - 用于实时数据采集和临时存储
- **MongoDB** - 用于持久化存储和历史数据查询

## 测试模块导入

运行以下命令测试所有模块是否正确导入：

```bash
cd F:/A-User/cliff/allin/all
python test_imports.py
```

## 注意事项

1. 确保 Redis 服务已启动（默认端口 6379）
2. 如需使用 MongoDB 同步功能，确保 MongoDB 服务已启动（默认端口 27017）
3. 所有导入路径已适配统一的项目结构
4. 使用统一的 `config.py` 配置文件

## 开发说明

### 添加新功能

1. 核心功能模块放在 `核心模块/` 目录下
2. UI组件放在 `仪表盘/` 目录下
3. 遵循现有的导入规范和代码风格

### 模块导入示例

```python
# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入核心模块
from 核心模块.数据采集 import SensorDataGenerator
from 核心模块.数据存储 import RedisDatabase
from 核心模块.数据同步 import MongoSync
```

## 故障排除

### 问题：导入错误 "No module named 'PySide6'"

**解决方案**：安装 PySide6
```bash
pip install PySide6
```

### 问题：导入错误 "No module named 'pymongo'"

**解决方案**：安装 pymongo
```bash
pip install pymongo
```

### 问题：Redis 连接失败

**解决方案**：确保 Redis 服务已启动
```bash
# Windows
redis-server

# Linux/Mac
sudo service redis-server start
```

### 问题：MongoDB 连接失败

**解决方案**：确保 MongoDB 服务已启动
```bash
# Windows
net start MongoDB

# Linux/Mac
sudo service mongod start
```

## 版本信息

- 融合系统版本：v1.0
- 基于项目：frist (仪表盘) + setest (传感器数据采集)
- Python版本要求：Python 3.8+
- GUI框架：PySide6
