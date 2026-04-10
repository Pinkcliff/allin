# -*- coding: utf-8 -*-
"""
显示板ID 9 (192.168.1.10) 实际发送的80字节数据
"""
import struct

# 板ID 9 的参数
chain_id = 0  # 链路ID
board_id = 9  # 链内板ID

# 假设从界面提取的4x4模块数据（使用不同的值来测试）
# 模拟 grid_data[0:4, 36:40] 的数据
module_data = [
    [10, 20, 30, 40],   # 第0行
    [50, 60, 70, 80],   # 第1行
    [90, 15, 25, 35],   # 第2行
    [45, 55, 65, 75]    # 第3行
]

print("=" * 80)
print(f"板ID {chain_id*10 + board_id} (192.168.1.{chain_id*10 + board_id + 1}) 的80字节数据包")
print("=" * 80)
print()
print("4x4模块数据 (百分比):")
for row in module_data:
    print(f"  {row}")
print()

# 构建80字节数据包
packet_bytes = b''

print("构建过程:")
print("-" * 80)
for fan_id in range(16):
    row = fan_id // 4
    col = fan_id % 4
    percent = module_data[row][col]
    pwm_value = int((percent / 100.0) * 999)

    # 构建5字节包
    packet = struct.pack(
        '<BBBBB',
        chain_id & 0xFF,
        board_id & 0xFF,
        fan_id & 0xFF,
        pwm_value & 0xFF,
        (pwm_value >> 8) & 0xFF
    )

    packet_bytes += packet

    print(f"风扇{fan_id:2d} (row={row}, col={col}): {percent:3d}% -> PWM={pwm_value:3d} | 数据: {' '.join(f'{b:02X}' for b in packet)}")

print()
print("=" * 80)
print(f"完整的80字节数据包:")
print("=" * 80)
print(f"总长度: {len(packet_bytes)} 字节")
print()
print("十六进制显示 (每行20字节):")
for i in range(0, len(packet_bytes), 20):
    chunk = packet_bytes[i:i+20]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  [{i:04d}] {hex_str}")

print()
print("=" * 80)
print("每组5字节解析 (共16组，每组5字节):")
print("=" * 80)
for i in range(16):
    start = i * 5
    end = start + 5
    chunk = packet_bytes[start:end]
    chain = chunk[0]
    board = chunk[1]
    fan = chunk[2]
    pwm_low = chunk[3]
    pwm_high = chunk[4]
    pwm = pwm_low | (pwm_high << 8)

    print(f"  [{i:2d}] chain={chain:02X} board={board:02X} fan={fan:02X} pwm={pwm:3d} (0x{pwm:04X}) | {' '.join(f'{b:02X}' for b in chunk)}")
