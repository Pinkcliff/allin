# PLC监控模块使用说明

## 模块概述

PLC监控模块是从 `see/ximen` 项目整合而来的西门子S7 PLC通信模块，提供以下功能：

1. **编码器实时监控** - 实时读取和显示编码器位置数据
2. **点位表批量监控** - 从Excel点位表批量读取PLC数据

## 目录结构

```
all/PLC监控/
├── __init__.py                 # 模块初始化
├── config.py                   # 配置文件
├── s7_comm/                    # S7通信核心模块
│   ├── __init__.py
│   └── s7_connector.py        # S7连接器类
├── encoder_monitor.py          # 编码器监控GUI
└── point_table_monitor.py      # 点位表监控GUI
```

## 功能说明

### 1. 编码器监控

**功能**：
- 实时读取PLC DB块中的编码器位置数据（REAL类型）
- 显示当前位置（大字体LCD显示）
- 实时曲线图显示位置变化
- 统计信息（最大值、最小值、变化次数、运行时间）
- 变化阈值设置和检测

**配置**：
- PLC IP: 192.168.0.1（可在config.py中修改）
- DB块号: 5
- 偏移地址: 124
- 数据类型: REAL（4字节浮点数）

### 2. 点位表监控

**功能**：
- 从Excel文件加载点位表
- 按DB块分组批量读取数据（提高效率）
- 支持REAL、BOOL、INT、DINT数据类型
- 实时更新显示
- 统计信息（总点数、读取成功/失败数）

**点位表格式**：
Excel文件（点位表.xlsx）格式：
```
| 点位名称 | 地址        | 数据类型 |
|----------|-------------|----------|
| 温度1    | DB5.0.0     | REAL     |
| 压力1    | DB5.4.0     | REAL     |
| 电机状态 | DB5.12.0    | BOOL     |
```

## 使用方法

### 1. 启动系统

```bash
cd F:/A-User/cliff/allin/all
python main.py
```

### 2. 打开PLC监控面板

在仪表盘工具栏中点击 "PLC监控" 按钮，即可打开PLC监控面板。

### 3. 编码器监控操作

1. 设置PLC IP地址（如果与默认不同）
2. 点击 "开始监控" 按钮
3. 系统将自动连接PLC并开始读取编码器位置
4. 查看实时位置数据和变化曲线
5. 可调整 "变化阈值" 来检测位置变化

### 4. 点位表监控操作

1. 确保点位表文件存在于 `all/data/点位表.xlsx`
2. 点击 "连接PLC" 按钮
3. 连接成功后，点击 "开始监控" 或 "单次刷新"
4. 系统将批量读取所有点位数据并显示在表格中

## 配置说明

### PLC配置

在 `all/config.py` 中修改：

```python
PLC_CONFIG = {
    'ip_address': '192.168.0.1',  # PLC IP地址
    'rack': 0,                      # 机架号
    'slot': 1,                       # 槽位号
    'timeout': 10,                   # 连接超时(秒)
    'encoder': {
        'db_number': 5,               # 编码器DB块号
        'offset': 124,                # 编码器偏移地址
        'data_type': 'REAL',          # 数据类型
        'min_value': -1000.0,         # 最小值
        'max_value': 1000.0           # 最大值
    },
    'point_table': {
        'file': '点位表.xlsx',         # 点位表文件名
        'refresh_interval': 1000,      # 刷新间隔(ms)
        'batch_by_db': True           # 按DB块分组读取
    }
}
```

## 依赖安装

```bash
pip install python-snap7==1.3
pip install pandas openpyxl
```

或使用：
```bash
pip install -r requirements.txt
```

## 注意事项

### PLC侧配置

1. **启用PUT/GET通信**
   - 打开TIA Portal项目
   - 进入「设备组态」→「以太网接口」→「属性」
   - 勾选「允许来自远程对象的PUT/GET通信访问」

2. **DB块设置**
   - 创建**非优化DB块**（重要！）
   - 记录DB块编号和起始地址

3. **网络配置**
   - PLC IP: 192.168.0.1（或根据实际修改）
   - 确保与上位机在同一网段

### 常见问题

**问题1**: 连接PLC失败
- 检查PLC是否启用了PUT/GET通信
- 确认IP地址正确
- 检查网络连接

**问题2**: 读取数据全为0
- 确认DB块为非优化块
- 检查偏移地址是否正确

**问题3**: 导入错误
```bash
# 如果提示缺少snap7模块
pip install python-snap7==1.3

# 如果提示缺少pandas
pip install pandas openpyxl
```

## 技术细节

### S7协议通信

- 使用 `python-snap7` 库
- 支持TCP/IP通信
- 支持多种数据类型：REAL, BOOL, INT, DINT, WORD, DWORD, BYTE

### 数据读取优化

- **批量读取**: 按DB块分组，一次读取整个块，减少通信次数
- **数据解析**: 使用snap7的util函数快速解析数据

### 界面集成

- 使用PySide6与系统其他模块保持一致
- 采用暗色主题
- 支持dock浮动和停靠

## 版本信息

- 版本: 1.0.0
- 来源: see/ximen 项目
- 整合日期: 2026-04-10
