# -*- coding: utf-8 -*-
"""
UDP发送调试工具

用于检查UDP发送状态并手动触发发送测试
"""

import sys
import os

# 模拟运行环境
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

print("=" * 70)
print("UDP发送器独立测试")
print("=" * 70)
print()

# 1. 测试UDP发送器模块
print("1. 测试导入UDP发送器模块...")
try:
    from 风场设置.main_control.udp_fan_sender import FanUDPSender, AsyncFanUDPSender
    print("  [OK] UDP发送器模块导入成功")
except Exception as e:
    print(f"  [FAIL] 无法导入UDP发送器: {e}")
    sys.exit(1)
print()

# 2. 创建测试数据
print("2. 创建测试数据...")
import numpy as np

# 创建40x40的测试网格（100个模块，每个4x4风扇）
test_grid = np.random.uniform(0, 100, (40, 40))
print(f"  [OK] 测试网格大小: {test_grid.shape}")
print(f"  [OK] 数据范围: {test_grid.min():.1f}% - {test_grid.max():.1f}%")
print()

# 3. 测试UDP发送器初始化
print("3. 测试UDP发送器初始化...")
try:
    # 使用AsyncFanUDPSender以支持队列发送
    sender = AsyncFanUDPSender(enable_logging=True)
    sender.start()  # 启动后台线程
    print("  [OK] UDP发送器初始化成功")
    print("  [OK] 后台发送线程已启动")
except Exception as e:
    print(f"  [FAIL] UDP发送器初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 4. 测试发送数据（会尝试发送，但可能没有实际的接收端）
print("4. 测试UDP发送...")
print("  [INFO] 注意: 如果没有实际的硬件接收端，发送会失败（这是正常的）")
print()

success_count = 0
fail_count = 0
callback_count = 0

def test_callback(success_cnt: int, fail_cnt: int, elapsed_time: float):
    """测试回调函数 - 批量回调"""
    global success_count, fail_count, callback_count
    success_count = success_cnt
    fail_count = fail_cnt
    callback_count += 1
    print(f"  [批量回调] 成功:{success_cnt} 失败:{fail_cnt} 耗时:{elapsed_time*1000:.1f}ms")

try:
    # 尝试发送网格数据
    sender.queue_send_grid(test_grid, test_callback)
    print("  [INFO] 已将100个控制板的数据加入发送队列")
    print("  [INFO] 等待发送完成...")
    import time
    time.sleep(2)  # 等待发送完成
    print(f"  [INFO] 发送结果: 成功 {success_count}, 失败 {fail_count}")
except Exception as e:
    print(f"  [FAIL] 发送失败: {e}")
    import traceback
    traceback.print_exc()
print()

# 5. 检查统计信息
print("5. 发送统计信息:")
stats = sender.get_statistics()
print(f"  总发送次数: {stats.get('total_sends', 0)}")
print(f"  成功次数: {stats.get('success_count', 0)}")
print(f"  失败次数: {stats.get('failure_count', 0)}")
print()

# 6. 关闭发送器
print("6. 关闭UDP发送器...")
sender.stop()
sender.close()
print("  [OK] UDP发送器已关闭")
print()

print("=" * 70)
print("测试完成")
print("=" * 70)
print()
print("使用说明:")
print("  1. 确保在主程序中启用了UDP发送（菜单栏 -> UDP控制 -> 启用UDP发送）")
print("  2. 确保网络连接正常（电驱板IP: 192.168.1.101-200, 端口: 5001）")
print("  3. 点击播放按钮后，查看信息输出窗口的UDP发送日志")
print("  4. 如果仍然没有发送，请检查:")
print("     - UDP控制菜单中'启用UDP发送'是否勾选")
print("     - '数据变化时自动发送'是否勾选")
print("     - 网络连接是否正常")
print()
