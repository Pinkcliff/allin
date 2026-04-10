# PLC监控模块集成总结

## 概述
成功将西门子S7 PLC监控模块从`see/ximen`目录集成到`all`融合系统中。

## 集成内容

### 1. 核心模块
- **S7通信模块** (`all/PLC监控/s7_comm/`)
  - `s7_connector.py`: S7协议通信核心类
  - `__init__.py`: 模块导出配置

### 2. 监控界面
- **编码器监控** (`all/PLC监控/encoder_monitor.py`)
  - 实时数据采集和显示
  - 500点数据缓冲
  - 变化检测和报警
  - 数据导出功能

- **点位表监控** (`all/PLC监控/point_table_monitor.py`)
  - CSV/Excel点位表导入
  - 按DB块批量读取优化
  - 实时数据刷新

### 3. UI集成
- 在`all/仪表盘/ui_docks.py`中添加`create_plc_monitor_dock()`函数
- 支持选项卡式显示编码器和点位表监控

### 4. 配置文件
- 在`all/config.py`中添加`PLC_CONFIG`配置块
- 创建默认点位表文件`all/data/点位表.csv`

### 5. 依赖管理
- 在`all/requirements.txt`中添加`python-snap7==1.3`

## 修复的问题

### 1. 模块导入问题
- **问题**: `No module named 's7_connector'`
- **解决**: 更新为`from s7_comm import S7PLCConnector`并添加`__init__.py`导出

### 2. 缺失导入
- **问题**: `name 'QFont' is not defined`
- **解决**: 在`ui_docks.py`中添加QFont导入

### 3. Python环境问题
- **问题**: Qt平台插件初始化失败
- **解决**: 确保使用my_env环境(Python 3.11.13)而非系统Python 3.7.0

### 4. 图片路径问题
- **问题**: `QPixmap::scaled: Pixmap is a null pixmap`
- **解决**: 修正所有图片路径，添加`资源/`前缀：
  - `ui_main_window.py`: `"背景.png"` → `"资源/背景.png"`
  - `ui_docks.py`: `"风场.png"` → `"资源/风场.png"`
  - `ui_docks.py`: `"动捕.png"` → `"资源/动捕.png"`

### 5. 缺失模块
- **问题**: `No module named 'debug'`
- **解决**: 创建`all/仪表盘/debug.py`模块

### 6. 缺失依赖
- **问题**: `No module named 'openpyxl'`
- **解决**: 安装openpyxl 3.1.5（用于Excel点位表读取）

### 7. QFont导入缺失
- **问题**: `name 'QFont' is not defined`
- **解决**: 在`PLC监控/point_table_monitor.py`中添加QFont导入

## 测试验证

创建了完整的测试脚本`all/test_plc_full.py`，验证：
- ✓ S7PLCConnector及相关类型导入成功
- ✓ EncoderMonitorWidget导入成功
- ✓ PointTableMonitorWidget导入成功
- ✓ create_plc_monitor_dock导入成功
- ✓ PLC配置加载成功
- ✓ 数据结构测试通过

## 配置说明

### PLC配置 (config.py)
```python
PLC_CONFIG = {
    'ip_address': '192.168.0.1',
    'rack': 0,
    'slot': 1,
    'timeout': 10,
    'encoder': {
        'db_number': 5,
        'offset': 124,
        'data_type': 'REAL',
        'min_value': -1000.0,
        'max_value': 1000.0
    },
    'point_table': {
        'file': '点位表.xlsx',
        'refresh_interval': 1000,
        'batch_by_db': True
    }
}
```

## 启动方式

### 方法1: 使用启动脚本
```batch
all/启动系统.bat
```

### 方法2: 命令行启动
```bash
D:\ProgramData\Anaconda3\envs\my_env\python.exe F:\A-User\cliff\allin\all\main.py
```

## 下一步工作
1. 根据实际PLC设备调整IP地址和点位表
2. 测试与真实PLC的连接通信
3. 根据需要调整监控界面布局和功能
