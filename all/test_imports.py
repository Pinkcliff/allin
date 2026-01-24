# -*- coding: utf-8 -*-
"""
测试脚本 - 验证所有模块导入是否正常
"""
import sys
import os

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

print("=" * 60)
print("测试模块导入")
print("=" * 60)

success_count = 0
total_tests = 7

# 测试 1: 导入 config
print("\n1. 测试导入 config...")
try:
    import config
    print("   [OK] config 导入成功")
    print(f"   - Redis配置: {config.REDIS_CONFIG}")
    print(f"   - 采样率: {config.SAMPLE_RATE}")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] config 导入失败: {e}")

# 测试 2: 导入数据采集模块
print("\n2. 测试导入核心模块.数据采集...")
try:
    from 核心模块.数据采集 import SensorDataGenerator
    print("   [OK] SensorDataGenerator 导入成功")

    # 测试生成数据
    generator = SensorDataGenerator()
    sample = generator.generate_sample()
    print(f"   - 生成测试数据成功:")
    print(f"     * 风扇数量: {len(sample['fans'])}")
    print(f"     * 温度传感器数量: {len(sample['temp_sensors'])}")
    print(f"     * 风速传感器数量: {len(sample['wind_speed_sensors'])}")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 数据采集模块导入失败: {e}")

# 测试 3: 导入数据存储模块
print("\n3. 测试导入核心模块.数据存储...")
try:
    from 核心模块.数据存储 import RedisDatabase
    print("   [OK] RedisDatabase 导入成功")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 数据存储模块导入失败: {e}")

# 测试 4: 导入数据同步模块
print("\n4. 测试导入核心模块.数据同步...")
try:
    from 核心模块.数据同步 import MongoSync
    print("   [OK] MongoSync 导入成功")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 数据同步模块导入失败: {e}")

# 测试 5: 导入仪表盘模块
print("\n5. 测试导入仪表盘模块...")
try:
    # 添加仪表盘目录到路径
    dashboard_dir = os.path.join(ROOT_DIR, '仪表盘')
    if dashboard_dir not in sys.path:
        sys.path.insert(0, dashboard_dir)

    from ui_sensor_collection import SensorDataCollectionTab, SensorDataViewTab
    print("   [OK] SensorDataCollectionTab 导入成功")
    print("   [OK] SensorDataViewTab 导入成功")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 仪表盘模块导入失败: {e}")

# 测试 6: 导入传感器数据dock
print("\n6. 测试导入传感器数据dock...")
try:
    from ui_sensor_dock import create_sensor_data_dock
    print("   [OK] create_sensor_data_dock 导入成功")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 传感器数据dock导入失败: {e}")

# 测试 7: 导入主窗口
print("\n7. 测试导入主窗口...")
try:
    from ui_main_window import GlobalDashboardWindow
    print("   [OK] GlobalDashboardWindow 导入成功")
    success_count += 1
except Exception as e:
    print(f"   [FAIL] 主窗口导入失败: {e}")

print("\n" + "=" * 60)
print(f"测试完成！通过: {success_count}/{total_tests}")
print("=" * 60)
