# -*- coding: utf-8 -*-
"""
测试主系统导入
"""
import sys
import os

# 模拟main.py的路径设置
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

dashboard_dir = os.path.join(ROOT_DIR, '仪表盘')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

print('ROOT_DIR:', ROOT_DIR)
print('dashboard_dir:', dashboard_dir)
print()

print('=== Testing Main System Imports ===')

try:
    from ui_main_window import GlobalDashboardWindow
    print('[OK] GlobalDashboardWindow')
except Exception as e:
    print(f'[FAIL] GlobalDashboardWindow: {e}')
    import traceback
    traceback.print_exc()

try:
    from ui_docks import create_plc_monitor_dock
    print('[OK] create_plc_monitor_dock')
except Exception as e:
    print(f'[FAIL] create_plc_monitor_dock: {e}')
    import traceback
    traceback.print_exc()

try:
    from PLC监控.s7_comm import S7PLCConnector
    print('[OK] S7PLCConnector')
except Exception as e:
    print(f'[FAIL] S7PLCConnector: {e}')

try:
    from PLC监控.encoder_monitor import EncoderMonitorWidget
    print('[OK] EncoderMonitorWidget')
except Exception as e:
    print(f'[FAIL] EncoderMonitorWidget: {e}')

try:
    from PLC监控.point_table_monitor import PointTableMonitorWidget
    print('[OK] PointTableMonitorWidget')
except Exception as e:
    print(f'[FAIL] PointTableMonitorWidget: {e}')

print()
print('=== Test Complete ===')
