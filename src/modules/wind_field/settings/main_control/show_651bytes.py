# -*- coding: utf-8 -*-
"""
显示电驱板通信协议的651字节数据包（参照 fan_control.py）

协议帧格式:
  [0]       AA           帧头(固定)
  [1-4]     帧号         4字节小端序递增
  [5]       01           帧类型(设置参数)
  [6]       00           链路ID(固定0x00)
  [7]       00           电驱板ID(固定0x00)
  [8-9]     02 80        数据长度(640字节, 大端序)
  [10-649]  数据区       10板×64字节, 板N偏移=N×64
  [650]     CC           帧尾(固定)

数据区: 每板64字节 = 16风扇 × 4字节(2个小端序16位PWM值)
  风扇N偏移 = 板偏移 + N × 4
"""
import struct

# 参数
PWM_FULL = 1000  # 100% = 1000

# 模拟板0和板6的数据（百分比）
board_data = {
    0: [10, 20, 30, 40, 50, 60, 70, 80, 90, 15, 25, 35, 45, 55, 65, 75],
    6: [100] * 16,  # 板6全部100%
}

frame_counter = 3

# 构建帧
header = struct.pack('B', 0xAA)
frame_num = struct.pack('<I', frame_counter)
frame_type = struct.pack('B', 0x01)
link_id = struct.pack('B', 0x00)
board_id_byte = struct.pack('B', 0x00)
data_len = struct.pack('>H', 640)

data = bytearray(640)

for board_id, percentages in board_data.items():
    board_offset = board_id * 64
    print(f"板{board_id} (偏移={board_offset}):")
    for fan_id in range(16):
        percent = percentages[fan_id]
        pwm_value = int(percent * PWM_FULL / 100)
        offset = board_offset + fan_id * 4
        struct.pack_into('<H', data, offset, pwm_value)
        struct.pack_into('<H', data, offset + 2, pwm_value)
        print(f"  风扇{fan_id:2d}: {percent:3d}% -> PWM={pwm_value:4d} | "
              f"字节[{offset}]=0x{data[offset]:02X} [{offset+1}]=0x{data[offset+1]:02X} "
              f"[{offset+2}]=0x{data[offset+2]:02X} [{offset+3}]=0x{data[offset+3]:02X}")
    print()

tail = struct.pack('B', 0xCC)
packet = header + frame_num + frame_type + link_id + board_id_byte + data_len + bytes(data) + tail

print("=" * 80)
print(f"651字节数据包 (帧号={frame_counter}):")
print("=" * 80)
hex_str = ''.join(f'{b:02X}' for b in packet)
print(f"总长度: {len(packet)} 字节")
print(f"十六进制:\n  {hex_str}")
print()

# 验证头部
print("头部解析:")
print(f"  帧头: 0x{packet[0]:02X}")
fn = struct.unpack_from('<I', packet, 1)[0]
print(f"  帧号: {fn} (小端序)")
print(f"  帧类型: 0x{packet[5]:02X}")
print(f"  链路ID: {packet[6]}")
print(f"  电驱板ID: {packet[7]} (固定0x00)")
dl = struct.unpack_from('>H', packet, 8)[0]
print(f"  数据长度: {dl}")
print(f"  帧尾: 0x{packet[650]:02X}")
print()

# 验证PWM数据
print("PWM数据验证 (小端序):")
for board_id in [0, 6]:
    board_offset = board_id * 64
    print(f"  板{board_id}:")
    for fan_id in [0, 6, 15]:
        offset = board_offset + fan_id * 4
        pwm_val = struct.unpack_from('<H', packet, 10 + offset)[0]
        percent = pwm_val * 100 // PWM_FULL
        print(f"    风扇{fan_id:2d}: PWM={pwm_val:4d} ({percent:3d}%)")
