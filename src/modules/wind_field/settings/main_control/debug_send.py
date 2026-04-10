# -*- coding: utf-8 -*-
"""
调试UDP发送，验证80字节包是否正确
"""
import socket
import struct
import time

# 模拟构建80字节包的数据
def build_80byte_packet():
    """构建80字节包（16个风扇 × 5字节）"""
    packet_parts = []

    # 使用不同的PWM值来测试
    pwm_values = [99, 199, 299, 399, 499, 599, 699, 799,
                  899, 149, 249, 349, 449, 549, 649, 749]

    for fan_id in range(16):
        pwm_value = pwm_values[fan_id]
        # 每个风扇5字节: 00 00 fan_id pwm_low pwm_high
        packet = struct.pack(
            '<BBBBB',
            0x00,                    # 链路ID（固定0）
            0x00,                    # 板ID（固定0）
            fan_id & 0xFF,           # 风扇ID
            pwm_value & 0xFF,        # PWM低字节
            (pwm_value >> 8) & 0xFF  # PWM高字节
        )
        packet_parts.append(packet)

    # 合并成80字节
    full_packet = b''.join(packet_parts)
    return full_packet

print("=" * 80)
print("验证80字节包构建")
print("=" * 80)

packet = build_80byte_packet()
print(f"\n构建的数据包长度: {len(packet)} 字节")
print(f"是否为80字节: {len(packet) == 80}")

print("\n十六进制显示:")
for i in range(0, len(packet), 20):
    chunk = packet[i:i+20]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f"  [{i:04d}] {hex_str}")

print("\n" + "=" * 80)
print("模拟发送UDP包")
print("=" * 80)

# 创建一个测试socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 测试发送到本地（用于抓包分析）
    target_ip = "127.0.0.1"
    target_port = 5001

    print(f"\n目标地址: {target_ip}:{target_port}")
    print(f"准备发送 {len(packet)} 字节数据...")

    # 发送数据
    sock.sendto(packet, (target_ip, target_port))
    print(f"发送成功！")

    # 验证是否一次性发送
    print(f"\n验证：数据包是 {len(packet)} 字节，应该是一次性发送的")
    print(f"如果你在抓包工具中看到16个5字节包，说明有问题")
    print(f"如果看到1个80字节包，说明正确")

    sock.close()

except Exception as e:
    print(f"发送失败: {e}")

print("\n" + "=" * 80)
print("可能的问题排查")
print("=" * 80)
print("1. 检查代码中是否调用了 send_grid_to_boards() 而不是 send_grid_to_boards_bulk()")
print("2. send_grid_to_boards() 会循环发送1600次（100板 × 16风扇）")
print("3. send_grid_to_boards_bulk() 会发送100次（每次80字节）")
print("\n请确认主窗口中调用的是哪个函数！")
