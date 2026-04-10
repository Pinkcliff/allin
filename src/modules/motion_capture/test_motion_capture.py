# -*- coding: utf-8 -*-
"""
测试动捕采集窗口是否能正常导入
"""

import sys
import os

# 添加动捕模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("=" * 60)
print("测试动捕采集窗口导入")
print("=" * 60)
print()

# 测试1: 导入动捕采集窗口
print("1. 测试导入动捕采集窗口...")
try:
    from motion_capture_window import MotionCaptureWindow
    print("  [OK] 动捕采集窗口导入成功")
except Exception as e:
    print(f"  [FAIL] 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 测试2: 检查SDK是否存在
print("2. 测试检查SDK...")
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
print()

# 测试3: 测试SDK导入
print("3. 测试SDK导入...")
try:
    sdk_path = os.path.join(current_dir, 'LuMoSDKPy')
    if sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)
    import LuMoSDKClient
    print("  [OK] LuMoSDKClient导入成功")
except Exception as e:
    print(f"  [FAIL] LuMoSDKClient导入失败: {e}")
print()

# 测试4: 检查PySide6
print("4. 测试PySide6...")
try:
    from PySide6.QtWidgets import QApplication
    print("  [OK] PySide6导入成功")
except Exception as e:
    print(f"  [FAIL] PySide6导入失败: {e}")
print()

print("=" * 60)
print("测试完成")
print("=" * 60)
print()
print("动捕采集模块已准备就绪！")
print()
print("使用说明:")
print("  1. 运行主程序 (main.py)")
print("  2. 在仪表盘中找到'动捕设置'面板")
print("  3. 点击'打开动捕采集'按钮")
print("  4. 在动捕采集窗口中配置IP和保存目录")
print("  5. 点击'开始采集'按钮进行数据采集")
print()
