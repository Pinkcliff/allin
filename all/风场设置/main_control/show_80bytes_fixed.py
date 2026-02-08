# -*- coding: utf-8 -*-
"""
显示板ID 9 (192.168.1.10) 正确的80字节数据包
前两个字节固定为 00 00（因为IP地址已经标识了板的位置）
"""
import struct

# 板ID 9（仅用于确定IP，不包含在数据包中）
chain_id = 0  # 固定为0x00
board_id = 9  # 固定为0x00

# 假设从界面提取的4x4模块数据
module_data = [
    [10, 20, 30, 40],   # 第0行
    [50, 60, 70, 80],   # 第1行
    [90, 15, 25, 35],   # 第2行
    [45, 55, 65, 75]    # 第3行
]

print("=" * 80)
print(f"板ID 9 (192.168.1.10) 的80字节数据包")
print("=" * 80)
print("协议说明：")
print("  - 前2字节固定为 00 00（IP地址已标识板位置）")
print("  - 后3字节：风扇ID + PWM低 + PWM高")
print()
print("4x4模块数据 (百分比):")
for row in module_data:
    print(f"  {row}")
print()

# 构建80字节数据包
packet_bytes = b''

print("构建过程（每个风扇5字节，前2字节固定00 00）:")
print("-" * 80)
for fan_id in range(16):
    row = fan_id // 4
    col = fan_id % 4
    percent = module_data[row][col]
    pwm_value = int((percent / 100.0) * 999)

    # 构建5字节包: 00 00 + 风扇ID + PWM低 + PWM高
    packet = struct.pack(
        '<BBBBB',
        0x00,                    # 链路ID（固定0）
        0x00,                    # 板ID（固定0）
        fan_id & 0xFF,           # 风扇ID
        pwm_value & 0xFF,        # PWM低字节
        (pwm_value >> 8) & 0xFF  # PWM高字节
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

print()
print("=" * 80)
print("关键变化：")
print("=" * 80)
print("✓ 前2字节固定为 00 00（不再发送实际的chain_id和board_id）")
print("✓ IP地址已经标识了是哪个板（192.168.1.10 = 板ID 9）")
print("✓ 每个风扇的5字节包：00 00 + fan_id + pwm_low + pwm_high")
