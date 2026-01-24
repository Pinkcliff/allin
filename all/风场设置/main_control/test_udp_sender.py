# -*- coding: utf-8 -*-
"""
UDP风扇发送器测试脚本
"""

import sys
import os
import numpy as np

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from udp_fan_sender import FanUDPSender, AsyncFanUDPSender, PROTOCOL_CONFIG


def test_protocol_config():
    """测试协议配置"""
    print("=" * 60)
    print("协议配置测试")
    print("=" * 60)
    print(f"Magic (FC): {PROTOCOL_CONFIG['magic_fc']}")
    print(f"Magic (FR): {PROTOCOL_CONFIG['magic_fr']}")
    print(f"控制器IP: {PROTOCOL_CONFIG['controller_ip']}")
    print(f"电驱板IP起始: {PROTOCOL_CONFIG['board_ip_start']}")
    print(f"电驱板IP结束: {PROTOCOL_CONFIG['board_ip_end']}")
    print(f"UDP端口: {PROTOCOL_CONFIG['udp_port']}")
    print(f"每板风扇数: {PROTOCOL_CONFIG['fans_per_board']}")
    print(f"PWM最大值: {PROTOCOL_CONFIG['pwm_max']}")
    print(f"数据包大小: {PROTOCOL_CONFIG['control_packet_size']}字节")
    print()


def test_board_ip_mapping():
    """测试电驱板ID到IP的映射"""
    print("=" * 60)
    print("电驱板ID到IP映射测试")
    print("=" * 60)

    sender = FanUDPSender(enable_logging=False)

    # 测试几个关键点
    test_ids = [0, 1, 10, 50, 99]
    for board_id in test_ids:
        ip = sender._get_board_ip(board_id)
        print(f"电驱板ID #{board_id:2d} -> IP: {ip}")

    sender.close()
    print()


def test_control_packet():
    """测试控制数据包构建"""
    print("=" * 60)
    print("控制数据包构建测试")
    print("=" * 60)

    sender = FanUDPSender(enable_logging=False)

    # 测试数据包
    board_id = 0
    fan_pwm_values = [500, 600, 700, 800] * 4  # 16个风扇

    packet = sender._build_control_packet(board_id, fan_pwm_values)

    print(f"电驱板ID: {board_id}")
    print(f"风扇PWM值: {fan_pwm_values[:4]}...")
    print(f"数据包大小: {len(packet)}字节")
    print(f"预期大小: {PROTOCOL_CONFIG['control_packet_size']}字节")
    print(f"数据包前16字节 (头部): {packet[:16].hex()}")
    print(f"数据包后4字节 (CRC32): {packet[-4:].hex()}")

    sender.close()
    print()


def test_grid_to_board_mapping():
    """测试40x40网格到电驱板的映射"""
    print("=" * 60)
    print("40x40网格到电驱板映射测试")
    print("=" * 60)

    sender = FanUDPSender(enable_logging=False)

    # 创建测试网格数据
    test_grid = np.zeros((40, 40), dtype=float)

    # 设置一些测试值
    # 电驱板0 (左下角): 50%
    test_grid[0:4, 0:4] = 50.0
    # 电驱板1: 75%
    test_grid[0:4, 4:8] = 75.0
    # 电驱板10 (第二排第一个): 100%
    test_grid[4:8, 0:4] = 100.0
    # 电驱板99 (右上角): 25%
    test_grid[36:40, 36:40] = 25.0

    print("测试网格数据:")
    print(f"  电驱板0 (0,0): 50%")
    print(f"  电驱板1 (0,1): 75%")
    print(f"  电驱板10 (1,0): 100%")
    print(f"  电驱板99 (9,9): 25%")
    print()

    # 映射检查
    print("模块到电驱板ID映射:")
    for module_row in range(10):
        for module_col in range(10):
            board_id = module_row * 10 + module_col
            if board_id in [0, 1, 10, 99]:
                row_start = module_row * 4
                row_end = row_start + 4
                col_start = module_col * 4
                col_end = col_start + 4
                module_data = test_grid[row_start:row_end, col_start:col_end]
                avg_value = module_data[0, 0]
                print(f"  模块({module_row},{module_col}) -> 电驱板#{board_id:2d} -> 平均值: {avg_value:.1f}%")

    sender.close()
    print()


def test_send_simulation():
    """模拟发送测试（不实际发送）"""
    print("=" * 60)
    print("模拟发送测试")
    print("=" * 60)

    # 使用测试模式（不实际发送数据）
    sender = FanUDPSender(enable_logging=False)

    # 创建测试网格
    test_grid = np.zeros((40, 40), dtype=float)

    # 设置渐变值
    for i in range(40):
        for j in range(40):
            test_grid[i, j] = (i + j) / 78.0 * 100  # 0-100%

    print("创建了40x40的渐变测试网格")
    print(f"最小值: {test_grid.min():.2f}%")
    print(f"最大值: {test_grid.max():.2f}%")
    print(f"平均值: {test_grid.mean():.2f}%")
    print()

    # 计算将要发送的数据包数量
    print(f"将发送到 {10*10} 个电驱板")
    print(f"每个电驱板包含 16 个风扇")
    print(f"总共 {10*10*16} 个风扇")
    print()

    sender.close()


def test_custom_mapping():
    """测试自定义映射函数"""
    print("=" * 60)
    print("自定义映射测试")
    print("=" * 60)

    sender = FanUDPSender(enable_logging=False)

    # 根据用户描述的映射：下角是1号机，横排从左到右
    # 假设"下角"是底部（第0行模块），从左到右编号
    # 那么映射应该是：board_id = module_row * 10 + module_col

    # 测试边界情况
    test_cases = [
        ((0, 0), 0, "左下角"),
        ((0, 9), 9, "右下角"),
        ((9, 0), 90, "左上角"),
        ((9, 9), 99, "右上角"),
    ]

    for (mr, mc), expected_id, desc in test_cases:
        board_id = mr * 10 + mc
        match = "OK" if board_id == expected_id else "FAIL"
        print(f"{match} 模块({mr},{mc}) [{desc:8s}] -> 电驱板#{board_id:2d} (预期: {expected_id})")

    sender.close()
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("UDP风扇发送器测试套件")
    print("=" * 60)
    print()

    test_protocol_config()
    test_board_ip_mapping()
    test_control_packet()
    test_grid_to_board_mapping()
    test_send_simulation()
    test_custom_mapping()

    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
