# -*- coding: utf-8 -*-
"""
展示UDP数据包格式
"""

import sys
import os
import struct
import time
import zlib

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

print("=" * 80)
print("UDP控制数据包格式展示")
print("=" * 80)
print()

# 协议配置
PROTOCOL_CONFIG = {
    'magic_fc': b'FC',
    'board_ip_start': '192.168.1.101',
    'udp_port': 5001,
    'pwm_max': 999,
}

# 构建一个测试数据包 - 发送到板ID #0
board_id = 0
sequence_number = 0
timestamp = int(time.time() * 1000) & 0xFFFFFFFF

# 16个风扇的PWM值 (测试用不同的值)
fan_pwm_values = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 999, 500, 500, 500, 500, 500]

print("【发送配置】")
print(f"  目标板ID: {board_id}")
print(f"  目标IP: 192.168.1.101")
print(f"  目标端口: {PROTOCOL_CONFIG['udp_port']}")
print(f"  序列号: {sequence_number}")
print(f"  时间戳: {timestamp}")
print(f"  风扇PWM值: {fan_pwm_values}")
print()

# 构建协议头 (16字节)
print("【协议头 (16字节)】")
header_parts = []
header_parts.append(struct.pack('<2s', PROTOCOL_CONFIG['magic_fc']))  # 2 bytes: magic "FC"
header_parts.append(struct.pack('<B', board_id))  # 1 byte: board_id
header_parts.append(struct.pack('<H', sequence_number))  # 2 bytes: sequence_number
header_parts.append(struct.pack('<I', timestamp))  # 4 bytes: timestamp
header_parts.append(struct.pack('<H', 0))  # 2 bytes: control_flags
header_parts.append(b'\x00' * 5)  # 5 bytes: reserved
header = b''.join(header_parts)

print("  字段解析:")
print(f"    magic (2字节): '{PROTOCOL_CONFIG['magic_fc'].decode('ascii')}'")
print(f"    hex: {header[0:2].hex().upper()}")
print()
print(f"    board_id (1字节): {board_id}")
print(f"    hex: {header[2:3].hex().upper()}")
print()
print(f"    sequence_number (2字节): {sequence_number}")
print(f"    hex: {header[3:5].hex().upper()}")
print()
print(f"    timestamp (4字节): {timestamp}")
print(f"    hex: {header[5:9].hex().upper()}")
print()
print(f"    control_flags (2字节): 0")
print(f"    hex: {header[9:11].hex().upper()}")
print()
print(f"    reserved (5字节): 0x00 * 5")
print(f"    hex: {header[11:16].hex().upper()}")
print()
print(f"  协议头完整hex: {header.hex().upper()}")
print()

# 构建控制数据 (80字节)
print("【控制数据 (80字节) - 16个风扇 × 5字节】")
control_data = b''
for i, (fan_id, pwm_value) in enumerate(zip(range(16), fan_pwm_values)):
    pwm_value = max(0, min(PROTOCOL_CONFIG['pwm_max'], pwm_value))
    fan_flags = 0x0001  # 启动标志
    fan_data = struct.pack('<BHH', fan_id, pwm_value, fan_flags)
    control_data += fan_data

    # 只显示前3个和最后1个风扇的详情
    if i < 3 or i == 15:
        print(f"  风扇 #{fan_id}:")
        print(f"    fan_id (1字节): {fan_id} -> hex: {fan_data[0:1].hex().upper()}")
        print(f"    pwm_level (2字节): {pwm_value} -> hex: {fan_data[1:3].hex().upper()}")
        print(f"    fan_flags (2字节): 0x{fan_flags:04X} -> hex: {fan_data[3:5].hex().upper()}")
        print(f"    小计hex: {fan_data.hex().upper()}")
        print()

print(f"  控制数据完整hex: {control_data.hex().upper()}")
print()

# CRC32校验 (4字节)
print("【CRC32校验 (4字节)】")
crc_data = header + control_data
crc32 = zlib.crc32(crc_data) & 0xFFFFFFFF
print(f"  校验范围: 协议头(16字节) + 控制数据(80字节) = 96字节")
print(f"  CRC32值: {crc32} (0x{crc32:08X})")
print(f"  hex: {struct.pack('<I', crc32).hex().upper()}")
print()

# 完整数据包
packet = header + control_data + struct.pack('<I', crc32)

print("=" * 80)
print("【完整UDP数据包 (100字节)】")
print("=" * 80)
print()

# 分行显示，每行16字节
print("Hex显示 (每行16字节):")
for i in range(0, len(packet), 16):
    chunk = packet[i:i+16]
    hex_str = ' '.join([f'{b:02X}' for b in chunk])
    ascii_str = ''.join([chr(b) if 32 <= b < 127 else '.' for b in chunk])
    print(f"  {i:04X}: {hex_str:<48} |{ascii_str}|")

print()
print(f"完整hex字符串 (100字节):")
print(f"  {packet.hex().upper()}")
print()

print("=" * 80)
print("【数据包结构总结】")
print("=" * 80)
print(f"  协议头:     16 字节 (00-15)")
print(f"  控制数据:   80 字节 (16-95) - 16个风扇 × 5字节")
print(f"  CRC32校验:   4 字节 (96-99)")
print(f"  总计:       100 字节")
print()
print(f"  发送到: 192.168.1.101:5001 (板ID #0)")
print("=" * 80)
