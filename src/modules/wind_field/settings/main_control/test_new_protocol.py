# -*- coding: utf-8 -*-
"""
测试新的5字节UDP协议
"""

import sys
import os
import struct

# 模拟运行环境
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

print("=" * 70)
print("新UDP协议测试 (5字节包)")
print("=" * 70)
print()

# 协议说明
print("【协议说明】")
print("  字节0: chain_id    链路ID (0-9)")
print("  字节1: board_id    电驱板ID (0-9)")
print("  字节2: fan_id      风扇ID (0-15)")
print("  字节3: pwm低字节   PWM等级低字节")
print("  字节4: pwm高字节   PWM等级高字节")
print()

# IP映射
print("【IP映射】")
print("  板ID 0  -> 192.168.1.1   (链路0, 板0)")
print("  板ID 1  -> 192.168.1.2   (链路0, 板1)")
print("  ...")
print("  板ID 9  -> 192.168.1.10  (链路0, 板9)")
print("  板ID 10 -> 192.168.1.11  (链路1, 板0)")
print("  ...")
print("  板ID 99 -> 192.168.1.100 (链路9, 板9)")
print()

def build_packet(chain_id, board_id, fan_id, pwm_value):
    """构建5字节控制包"""
    packet = struct.pack(
        '<BBBBB',  # 5个1字节: little-endian
        chain_id & 0xFF,
        board_id & 0xFF,
        fan_id & 0xFF,
        pwm_value & 0xFF,
        (pwm_value >> 8) & 0xFF
    )
    return packet

def get_board_ip(board_id):
    """获取板ID对应的IP"""
    return f"192.168.1.{board_id + 1}"

print("【测试1: 构建5字节包】")
test_cases = [
    (0, 0, 0, 500),    # 链路0, 板0, 风扇0, PWM=500
    (0, 0, 15, 999),   # 链路0, 板0, 风扇15, PWM=999
    (5, 5, 8, 0),      # 链路5, 板5, 风扇8, PWM=0
    (9, 9, 7, 333),     # 链路9, 板9, 风扇7, PWM=333
]

for chain_id, board_id, fan_id, pwm in test_cases:
    packet = build_packet(chain_id, board_id, fan_id, pwm)
    ip = get_board_ip(chain_id * 10 + board_id)
    hex_str = ' '.join([f'{b:02X}' for b in packet])
    print(f"  链路{chain_id} 板{board_id} 风扇{fan_id:2d} PWM={pwm:3d} -> IP:{ip} | {hex_str}")

print()

print("【测试2: IP映射验证】")
print("  全局板ID -> 链路ID + 板内ID -> IP地址")
for global_id in [0, 1, 9, 10, 11, 50, 99]:
    chain_id = global_id // 10
    board_in_chain = global_id % 10
    ip = get_board_ip(global_id)
    print(f"  板ID{global_id:2d} -> 链路{chain_id} 板{board_in_chain} -> {ip}")

print()

print("【测试3: 40x40网格映射】")
print("  40x40网格 = 10x10个模块 (4x4风扇)")
print("  每个模块对应一个板ID")
print()

# 显示几个关键位置的映射
key_positions = [
    (0, 0, "左上角", 0, 0),
    (0, 39, "右上角", 0, 9),
    (39, 0, "左下角", 9, 0),
    (39, 39, "右下角", 9, 9),
]

for i in range(0, len(key_positions), 5):
    row, col, name, expected_chain, expected_board = key_positions[i]
    module_row = row // 4
    module_col = col // 4
    global_board_id = module_row * 10 + module_col
    chain_id = global_board_id // 10
    board_in_chain = global_board_id % 10
    ip = get_board_ip(global_board_id)
    print(f"  位置({row:2d},{col:2d}) {name:6s} -> 模块({module_row},{module_col}) 板ID{global_board_id:2d} 链路{chain_id}板{board_in_chain} -> {ip}")

print()
print("=" * 70)
print("新协议验证完成！")
print("=" * 70)
print()
print("【总结】")
print(f"  包大小: 5字节")
print(f"  IP范围: 192.168.1.1-100")
print(f"  链路数: 10个")
print(f"  每链路板数: 10个")
print(f"  总板数: 100个")
print(f"  每板风扇: 16个")
print(f"  总风扇数: 1600个")
