# 项目重构方案

## 目标
1. 将所有中文文件夹名改为英文
2. 整理项目结构，使其更清晰
3. 删除重复和无用的文件
4. 保留 see 和 sikao260410 文件夹

## 新项目结构

```
allin/
├── src/                          # 源代码主目录
│   ├── main.py                   # 主入口
│   ├── config.py                 # 配置文件
│   ├── requirements.txt          # 依赖
│   │
│   ├── dashboard/                # 仪表盘模块
│   │   ├── __init__.py
│   │   ├── ui_main_window.py
│   │   ├── ui_docks.py
│   │   ├── ui_custom_widgets.py
│   │   ├── ui_chart_widget.py
│   │   ├── ui_motion_capture.py
│   │   ├── ui_sensor_collection.py
│   │   ├── ui_sensor_dock.py
│   │   ├── core_theme_manager.py
│   │   ├── core_data_simulator.py
│   │   └── debug.py
│   │
│   ├── modules/                  # 功能模块
│   │   ├── __init__.py
│   │   │
│   │   ├── plc_monitoring/       # PLC监控 (PLC监控)
│   │   │   ├── __init__.py
│   │   │   ├── s7_comm/
│   │   │   ├── encoder_monitor.py
│   │   │   └── point_table_monitor.py
│   │   │
│   │   ├── motion_capture/       # 运动捕捉 (动捕)
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   │
│   │   ├── wind_field/           # 风场相关
│   │   │   ├── __init__.py
│   │   │   ├── editor/           # 风场编辑器 (风场编辑器)
│   │   │   ├── settings/         # 风场设置 (风场设置)
│   │   │   └── preprocessing/    # 前处理 (前处理)
│   │   │
│   │   ├── fan_control/          # 风扇控制 (风扇控制)
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   │
│   │   ├── hardware/             # 硬件控制 (硬件控制)
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   │
│   │   └── core/                 # 核心模块 (核心模块)
│   │       ├── __init__.py
│   │       ├── data_sync/        # 数据同步
│   │       ├── data_storage/     # 数据存储
│   │       └── data_generation/  # 数据生成
│   │
│   ├── assets/                   # 资源文件 (资源)
│   │   ├── images/               # 图片
│   │   ├── icons/                # 图标
│   │   └── themes/               # 主题
│   │
│   └── tests/                    # 测试文件
│       └── ...
│
├── data/                         # 数据文件
│   └── ...
│
├── docs/                         # 文档
│   └── ...
│
├── see/                          # 保留（外部模块）
├── sikao260410/                  # 保留（思考文档）
│
├── .gitignore
├── README.md
└── startup.bat                   # 启动脚本
```

## 文件夹重命名映射

| 原名称 | 新名称 |
|--------|--------|
| 仪表盘 | src/dashboard |
| PLC监控 | src/modules/plc_monitoring |
| 动捕 | src/modules/motion_capture |
| 风场编辑器 | src/modules/wind_field/editor |
| 风场设置 | src/modules/wind_field/settings |
| 前处理 | src/modules/wind_field/preprocessing |
| 风扇控制 | src/modules/fan_control |
| 硬件控制 | src/modules/hardware |
| 核心模块 | src/modules/core |
| 资源 | src/assets |
| 测试 | src/tests |
| docs | docs (移到根目录) |
| tests | 删除（与测试重复） |
| wind_field_editor | 删除（重复） |
| wind_field_editor_code | 删除（重复） |

## 执行步骤

1. 创建新的目录结构
2. 移动和重命名文件
3. 更新导入路径
4. 删除重复和无用文件
5. 测试系统运行
