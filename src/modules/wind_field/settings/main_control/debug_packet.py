# -*- coding: utf-8 -*-
"""
调试80字节数据包的内容
"""
import struct

def debug_bulk_packet(chain_id, board_id, pwm_values):
    """打印80字节数据包的详细内容"""
    print(f"\n{'='*80}")
    print(f"板ID {chain_id*10 + board_id} (192.168.1.{chain_id*10 + board_id + 1}) 的80字节数据包")
    print(f"链路ID: {chain_id}, 板内ID: {board_id}")
    print(f"{'='*80}")

    packet_parts = []
    for fan_id in range(16):
        pwm_value = pwm_values[fan_id]
        packet = struct.pack(
            '<BBBBB',
            chain_id & 0xFF,
            board_id & 0xFF,
            fan_id & 0xFF,
            pwm_value & 0xFF,
            (pwm_value >> 8) & 0xFF
        )
        packet_parts.append(packet)

        # 打印每个5字节包的详细内容
        print(f"\n风扇 {fan_id:2d} (5字节):")
        print(f"  链路ID: {chain_id}")
        print(f"  板ID  : {board_id}")
        print(f"  风扇ID: {fan_id}")
        print(f"  PWM值 : {pwm_value} (0x{pwm_value:04X})")
        print(f"  数据  : {' '.join(f'{b:02X}' for b in packet)}")

    full_packet = b''.join(packet_parts)
    print(f"\n完整的80字节数据包 (十六进制):")
    print(f"长度: {len(full_packet)} 字节")
    for i in range(0, len(full_packet), 20):
        hex_str = ' '.join(f'{b:02X}' for b in full_packet[i:i+20])
        print(f"  {i:04d}: {hex_str}")

# 测试板ID 9的数据
chain_id = 0  # 板ID 9 = 链路0, 板9
board_id = 9

# 使用不同的PWM值来测试
pwm_values = [359, 369, 379, 389, 759, 769, 779, 789, 1158, 1168, 1178, 1188, 1558, 1568, 1578, 1588]

debug_bulk_packet(chain_id, board_id, pwm_values)

print(f"\n\n{'='*80}")
print("关键观察点:")
print("="*80)
print("1. 每个5字节包的第3字节应该是风扇ID (0x00-0x0F)")
print("2. 每个5字节包的第4-5字节应该是PWM值")
print("3. 如果硬件端风扇布局不同，可能需要调整映射关系")
print()
print("可能的问题:")
print("- 硬件端风扇0可能不在左上角，而在其他位置")
print("- 硬件可能按列优先方式排列风扇，而不是行优先")
print("- 硬件的fan_id编号顺序可能与代码假设不同")
