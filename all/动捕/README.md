# 动捕数据采集模块

## 功能说明

该模块用于采集动捕系统的数据并保存为CSV文件。

## 依赖项

在使用该模块之前，需要安装以下Python包：

```bash
pip install protobuf
pip install pyzmq
pip install pyside6
```

或者使用requirements.txt：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 通过主程序使用

1. 运行主程序 `python main.py`
2. 在仪表盘中找到"动捕设置"面板
3. 点击"打开动捕采集"按钮
4. 在动捕采集窗口中配置：
   - 动捕系统IP地址（默认：192.168.3.24）
   - 保存目录
5. 点击"开始采集"按钮进行数据采集
6. 点击"停止采集"按钮结束采集

### 2. 独立运行动捕采集窗口

```python
from motion_capture_window import MotionCaptureWindow
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = MotionCaptureWindow()
window.show()
sys.exit(app.exec())
```

## 数据格式

采集的数据保存为CSV文件，包含以下内容：

- 帧ID
- 时间戳
- 相机同步时间
- 数据广播时间
- 标记点数据（ID、名称、X、Y、Z坐标）
- 刚体数据（位置、姿态、速度、加速度、欧拉角）
- 时码信息

## 文件结构

```
动捕/
├── __init__.py                    # 模块初始化文件
├── motion_capture_window.py       # 动捕采集窗口
├── LuMoSDKPy/                     # LuMo SDK
│   ├── LuMoSDKClient.py          # SDK客户端
│   ├── LusterFrameStruct_pb2.py  # Protobuf数据结构
│   ├── PythonSample.py           # SDK使用示例
│   └── Readme.txt                # SDK说明文档
├── test_sdk_only.py              # SDK测试脚本
└── README.md                     # 本文件
```

## API配置

- **默认IP**: 192.168.3.24
- **端口**: 6868 (ZMQ SUB端口)
- **协议**: ZMQ (ZeroMQ)

## 超时设置

- 默认超时：5秒无数据自动停止
- 可在MotionCaptureWorker类中修改`data_timeout`属性

## 注意事项

1. 确保动捕系统已启动并正常广播数据
2. 确保网络连接正常，可以访问动捕系统IP
3. 采集的数据会自动保存到指定的保存目录
4. 如果标记点数量变化，会自动创建新的CSV文件

## 故障排除

### 问题1: ModuleNotFoundError: No module named 'google'

**解决方案**: 安装protobuf
```bash
pip install protobuf
```

### 问题2: ModuleNotFoundError: No module named 'zmq'

**解决方案**: 安装pyzmq
```bash
pip install pyzmq
```

### 问题3: 无法连接到动捕系统

**检查事项**:
1. 动捕系统是否已启动
2. IP地址是否正确
3. 网络连接是否正常
4. 防火墙是否允许连接

### 问题4: 采集的数据为空

**检查事项**:
1. 动捕系统是否在广播数据
2. 标记点是否正确设置
3. 相机是否正常工作
