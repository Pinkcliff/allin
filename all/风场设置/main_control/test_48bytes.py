# -*- coding: utf-8 -*-
"""
显示板ID 9 (192.168.1.10) 新协议的48字节数据包
"""
import struct

# 板ID 9 的参数（仅用于显示，不包含在数据包中）
chain_id = 0
board_id = 9

# 假设从界面提取的4x4模块数据
module_data = [
    [10, 20, 30, 40],   # 第0行
    [50, 60, 70, 80],   # 第1行
    [90, 15, 25, 35],   # 第2行
    [45, 55, 65, 75]    # 第3行
]

print("=" * 80)
print(f"板ID {chain_id*10 + board_id} (192.168.1.{chain_id*10 + board_id + 1}) 的48字节数据包（新协议）")
print("=" * 80)
print()
print("4x4模块数据 (百分比):")
for row in module_data:
    print(f"  {row}")
print()

# 构建48字节数据包
packet_bytes = b''

print("构建过程（新协议：3字节/风扇）:")
print("-" * 80)
for fan_id in range(16):
    row = fan_id // 4
    col = fan_id % 4
    percent = module_data[row][col]
    pwm_value = int((percent / 100.0) * 999)

    # 构建3字节包
    packet = struct.pack(
        '<B',            # 风扇ID
        fan_id & 0xFF
    ) + struct.pack(
        '<H',            # PWM值
        pwm_value & 0xFFFF
    )

    packet_bytes += packet

    print(f"风扇{fan_id:2d} (row={row}, col={col}): {percent:3d}% -> PWM={pwm_value:3d} | 数据: {' '.join(f'{b:02X}' for b in packet)}")

print()
print("=" * 80)
print(f"完整的48字节数据包（新协议）:")
print("=" * 80)
print(f"总长度: {len(packet_bytes)} 字节")
print()
print("十六进制显示 (每行24字节):")
for i in range(0, len(packet_bytes), 24):
    chunk = packet_bytes[i:i+24]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  [{i:04d}] {hex_str}")

print()
print("=" * 80)
print("每组3字节解析 (共16组，每组3字节):")
print("=" * 80)
for i in range(16):
    start = i * 3
    end = start + 3
    chunk = packet_bytes[start:end]
    fan = chunk[0]
    pwm_low = chunk[1]
    pwm_high = chunk[2]
    pwm = pwm_low | (pwm_high << 8)

    print(f"  [{i:2d}] fan={fan:02X} pwm={pwm:3d} (0x{pwm:04X}) | {' '.join(f'{b:02X}' for b in chunk)}")

print()
print("=" * 80)
print("协议对比:")
print("=" * 80)
print("旧协议（5字节）: chain_id(1) + board_id(1) + fan_id(1) + pwm_low(1) + pwm_high(1)")
print("新协议（3字节）: fan_id(1) + pwm_low(1) + pwm_high(1)")
print()
print("优势:")
print("1. 更小的数据包（80字节 -> 48字节）")
print("2. IP地址已经标识了是哪个板，不需要重复发送chain_id和board_id")
