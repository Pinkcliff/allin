# -*- coding: utf-8 -*-
"""
测试PLC监控模块
"""
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """测试所有导入"""
    print("=" * 50)
    print("测试PLC监控模块导入")
    print("=" * 50)

    try:
        from PLC监控.s7_comm import S7PLCConnector
        print("[OK] S7PLCConnector 导入成功")
    except Exception as e:
        print(f"[FAIL] S7PLCConnector 导入失败: {e}")

    try:
        from PLC监控.encoder_monitor import EncoderMonitorWidget
        print("[OK] EncoderMonitorWidget 导入成功")
    except Exception as e:
        print(f"[FAIL] EncoderMonitorWidget 导入失败: {e}")

    try:
        from PLC监控.point_table_monitor import PointTableMonitorWidget
        print("[OK] PointTableMonitorWidget 导入成功")
    except Exception as e:
        print(f"[FAIL] PointTableMonitorWidget 导入失败: {e}")

    try:
        from 仪表盘.ui_docks import create_plc_monitor_dock
        print("[OK] create_plc_monitor_dock 导入成功")
    except Exception as e:
        print(f"[FAIL] create_plc_monitor_dock 导入失败: {e}")

    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    test_imports()
