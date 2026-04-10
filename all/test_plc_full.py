# -*- coding: utf-8 -*-
"""
测试PLC监控模块完整功能
"""
import sys
import os

# 添加模块路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 添加仪表盘目录到路径
dashboard_dir = os.path.join(ROOT_DIR, '仪表盘')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

def test_all_imports():
    """测试所有导入"""
    print("=" * 60)
    print("测试PLC监控模块完整功能")
    print("=" * 60)

    # 测试1: S7通信模块
    try:
        from PLC监控.s7_comm import S7PLCConnector, DBItem, DataType
        print("[OK] S7PLCConnector及相关类型 导入成功")
    except Exception as e:
        print(f"[FAIL] S7通信模块 导入失败: {e}")
        return False

    # 测试2: 编码器监控模块
    try:
        from PLC监控.encoder_monitor import EncoderMonitorWidget
        print("[OK] EncoderMonitorWidget 导入成功")
    except Exception as e:
        print(f"[FAIL] 编码器监控模块 导入失败: {e}")
        return False

    # 测试3: 点位表监控模块
    try:
        from PLC监控.point_table_monitor import PointTableMonitorWidget
        print("[OK] PointTableMonitorWidget 导入成功")
    except Exception as e:
        print(f"[FAIL] 点位表监控模块 导入失败: {e}")
        return False

    # 测试4: UI集成
    try:
        from 仪表盘.ui_docks import create_plc_monitor_dock
        print("[OK] create_plc_monitor_dock 导入成功")
    except Exception as e:
        print(f"[FAIL] UI集成模块 导入失败: {e}")
        return False

    # 测试5: 配置文件
    try:
        from config import PLC_CONFIG
        print(f"[OK] PLC配置加载成功: {PLC_CONFIG['ip_address']}:{PLC_CONFIG['rack']}/{PLC_CONFIG['slot']}")
    except Exception as e:
        print(f"[FAIL] PLC配置 导入失败: {e}")
        return False

    print("=" * 60)
    print("所有模块测试通过！")
    print("=" * 60)
    return True

def test_data_structures():
    """测试数据结构"""
    print("\n" + "=" * 60)
    print("测试数据结构")
    print("=" * 60)

    try:
        from PLC监控.s7_comm import DBItem, DataType

        # 创建测试数据项
        test_item = DBItem(
            name="测试点位",
            data_type=DataType.REAL,
            start_offset=0
        )
        print(f"[OK] DBItem创建成功: {test_item}")

        # 测试枚举
        print(f"[OK] 数据类型枚举: REAL={DataType.REAL.value}, BOOL={DataType.BOOL.value}")

        return True
    except Exception as e:
        print(f"[FAIL] 数据结构测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_all_imports()
    if success:
        test_data_structures()
