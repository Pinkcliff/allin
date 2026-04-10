# -*- coding: utf-8 -*-
"""
测试PLC连接线程功能
验证UI不会在连接时卡住
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

dashboard_dir = os.path.join(ROOT_DIR, '仪表盘')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

def test_threading():
    """测试线程功能"""
    print("=" * 60)
    print("测试PLC连接线程功能")
    print("=" * 60)

    # 创建应用
    app = QApplication(sys.argv)

    # 导入模块
    from PLC监控.point_table_monitor import (
        PointTableMonitorWidget,
        PLCConnectionThread,
        PLCDataReadThread
    )

    print("[OK] 模块导入成功")

    # 创建窗口
    widget = PointTableMonitorWidget()
    widget.setWindowTitle("PLC连接测试 - 使用后台线程")
    widget.resize(800, 600)
    widget.show()

    print("[OK] 测试窗口已创建")
    print()
    print("说明:")
    print("  - 点击'连接PLC'按钮时，UI不会卡住")
    print("  - 连接按钮会显示'连接中...'状态")
    print("  - 连接完成后会自动更新UI状态")
    print("  - 数据读取也在后台线程中执行")
    print()
    print("注意: 需要真实的PLC设备才能完成连接")
    print("      如果没有PLC，连接会超时但不会卡住UI")
    print()
    print("关闭窗口以退出测试...")

    # 运行应用
    return app.exec()

if __name__ == "__main__":
    test_threading()
