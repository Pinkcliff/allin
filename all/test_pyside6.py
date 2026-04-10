# -*- coding: utf-8 -*-
"""
简单测试脚本 - 验证PySide6是否能在my_env中正常工作
"""
import sys
print("Python版本:", sys.version)
print("Python路径:", sys.executable)

try:
    from PySide6.QtWidgets import QApplication, QLabel, QWidget
    print("✓ PySide6导入成功")

    app = QApplication(sys.argv)
    print("✓ QApplication创建成功")

    widget = QWidget()
    widget.setWindowTitle("测试窗口")
    widget.resize(300, 200)
    widget.show()
    print("✓ 测试窗口显示成功")

    print("\nPySide6在my_env中工作正常！")

except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
