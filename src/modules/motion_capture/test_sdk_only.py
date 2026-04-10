# -*- coding: utf-8 -*-
"""
测试动捕SDK是否能正常导入（不依赖PySide6）
"""

import sys
import os

# 添加动捕模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("=" * 60)
print("测试动捕SDK导入")
print("=" * 60)
print()

# 测试1: 检查SDK是否存在
print("1. 检查SDK文件夹...")
sdk_path = os.path.join(current_dir, 'LuMoSDKPy')
if os.path.exists(sdk_path):
    print(f"  [OK] SDK文件夹存在: {sdk_path}")

    # 检查关键文件
    required_files = [
        'LuMoSDKClient.py',
        'LusterFrameStruct_pb2.py',
    ]
    for file in required_files:
        file_path = os.path.join(sdk_path, file)
        if os.path.exists(file_path):
            print(f"  [OK] {file} 存在")
        else:
            print(f"  [FAIL] {file} 不存在")
else:
    print(f"  [FAIL] SDK文件夹不存在: {sdk_path}")
    sys.exit(1)
print()

# 测试2: 测试SDK导入
print("2. 测试SDK导入...")
try:
    if sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)
    import LuMoSDKClient
    print("  [OK] LuMoSDKClient导入成功")

    # 检查关键函数
    functions = ['Init', 'Connnect', 'Close', 'ReceiveData']
    for func in functions:
        if hasattr(LuMoSDKClient, func):
            print(f"  [OK] 函数 {func} 存在")
        else:
            print(f"  [FAIL] 函数 {func} 不存在")
except Exception as e:
    print(f"  [FAIL] LuMoSDKClient导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 测试3: 检查protobuf
print("3. 测试protobuf结构...")
try:
    import LusterFrameStruct_pb2
    print("  [OK] LusterFrameStruct_pb2导入成功")

    # 检查关键结构
    if hasattr(LusterFrameStruct_pb2, 'Frame'):
        print("  [OK] Frame结构存在")
    else:
        print("  [WARN] Frame结构不存在")
except Exception as e:
    print(f"  [FAIL] LusterFrameStruct_pb2导入失败: {e}")
print()

# 测试4: 检查zmq
print("4. 测试zmq模块...")
try:
    import zmq
    print(f"  [OK] zmq模块存在 (版本: {zmq.zmq_version()})")
except Exception as e:
    print(f"  [FAIL] zmq模块不存在: {e}")
    print("  [INFO] 请安装zmq: pip install pyzmq")
print()

print("=" * 60)
print("SDK测试完成")
print("=" * 60)
print()
print("SDK模块状态:")
print("  - LuMoSDKClient: " + ("✓" if os.path.exists(os.path.join(sdk_path, 'LuMoSDKClient.py')) else "✗"))
print("  - LusterFrameStruct_pb2: " + ("✓" if os.path.exists(os.path.join(sdk_path, 'LusterFrameStruct_pb2.py')) else "✗"))
print("  - zmq: " + ("✓" if 'zmq' in sys.modules else "✗"))
print()
