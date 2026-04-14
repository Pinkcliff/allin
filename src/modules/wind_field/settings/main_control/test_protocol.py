# -*- coding: utf-8 -*-
"""
自动化协议验证测试脚本
对比 fan_control.py 和 udp_fan_sender.py 的输出是否完全一致
"""
import sys
import os
import struct
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

# ============================================================
# 1. 直接用 struct 构建（参照 fan_control.py 的方式）
# ============================================================

def fan_control_build_frame(frame_counter, pwm_percent, board_ids_with_fans):
    """
    完全复刻 fan_control.py 的 _build_frame 方法
    board_ids_with_fans: {board_id: [16个bool], ...}
    """
    PWM_FULL = 1000

    header = struct.pack('B', 0xAA)
    frame_num = struct.pack('<I', frame_counter)
    frame_type = struct.pack('B', 0x01)
    link_id = struct.pack('B', 0x00)
    board_id_byte = struct.pack('B', 0x00)
    data_len = struct.pack('>H', 640)

    data = bytearray(640)
    pwm_value = int(pwm_percent * PWM_FULL / 100)

    for board_id, fan_states in board_ids_with_fans.items():
        board_offset = board_id * 64
        for fan_id in range(16):
            val = pwm_value if fan_states[fan_id] else 0
            offset = board_offset + fan_id * 4
            struct.pack_into('<H', data, offset, val)
            struct.pack_into('<H', data, offset + 2, val)

    tail = struct.pack('B', 0xCC)
    return header + frame_num + frame_type + link_id + board_id_byte + data_len + bytes(data) + tail


# ============================================================
# 2. 使用 udp_fan_sender.py 的 _build_chain_packet
# ============================================================

def udp_sender_build_packet(frame_counter, boards_pwm_data):
    """
    调用 FanUDPSender._build_chain_packet
    """
    from modules.wind_field.settings.main_control.udp_fan_sender import FanUDPSender

    # 创建发送器（禁用socket绑定和日志）
    sender = FanUDPSender.__new__(FanUDPSender)
    sender.board_ip_start = '192.168.1.100'
    sender.udp_port = 6005
    sender.local_bind_ip = '192.168.1.101'
    sender.enable_logging = False
    sender.logger = None
    sender.frame_counter = frame_counter
    sender.stats = {'total_packets': 0, 'success_packets': 0, 'failed_packets': 0, 'last_send_time': None}
    sender.data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(sender.data_dir, exist_ok=True)
    sender.fan_pwm_states = {}
    sender.pwm_lock = __import__('threading').Lock()
    sender.fan_id_mapping = {i: i for i in range(16)}
    sender.physical_to_logical_fan = {i: i for i in range(16)}
    sender.csv_lock = __import__('threading').Lock()
    sender.playback_mode = False
    sender.verify_log_file = os.path.join(sender.data_dir, 'verify_test.log')

    packet = sender._build_chain_packet(boards_pwm_data)
    return packet, sender.frame_counter


# ============================================================
# 3. 测试用例
# ============================================================

results = []
log_lines = []

def log(msg):
    log_lines.append(msg)
    print(msg)

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" - {detail}"
    results.append((name, status, detail))
    log(msg)
    return condition


log("=" * 80)
log("电驱板通信协议自动化验证测试")
log("=" * 80)
log("")

# ------- 测试1: 空包（所有风扇关闭）-------
log("\n--- 测试1: 空包（全零数据）---")
fc_pkt = fan_control_build_frame(0, 100, {0: [False]*16})
our_pkt, _ = udp_sender_build_packet(0, {0: [0]*16})

check("包长度", len(our_pkt) == 651, f"实际={len(our_pkt)}")
check("帧头", our_pkt[0] == 0xAA, f"实际=0x{our_pkt[0]:02X}")
check("帧尾", our_pkt[650] == 0xCC, f"实际=0x{our_pkt[650]:02X}")
check("帧类型", our_pkt[5] == 0x01, f"实际=0x{our_pkt[5]:02X}")
check("链路ID", our_pkt[6] == 0x00, f"实际={our_pkt[6]}")
check("电驱板ID=0x00", our_pkt[7] == 0x00, f"实际={our_pkt[7]}")

# 与fan_control.py逐字节对比
match = fc_pkt == our_pkt
check("与fan_control.py完全一致", match)
if not match:
    for i in range(651):
        if fc_pkt[i] != our_pkt[i]:
            log(f"    首个差异在字节[{i}]: fan_control=0x{fc_pkt[i]:02X}, ours=0x{our_pkt[i]:02X}")
            break

# ------- 测试2: 单板全开100% -------
log("\n--- 测试2: 板0全部风扇100% ---")
fc_pkt = fan_control_build_frame(0, 100, {0: [True]*16})
our_pkt, _ = udp_sender_build_packet(0, {0: [1000]*16})

match = fc_pkt == our_pkt
check("与fan_control.py完全一致", match)
if not match:
    for i in range(min(651, len(fc_pkt), len(our_pkt))):
        if fc_pkt[i] != our_pkt[i]:
            log(f"    首个差异在字节[{i}]: fan_control=0x{fc_pkt[i]:02X}, ours=0x{our_pkt[i]:02X}")
            break

# 检查PWM数据
val = struct.unpack_from('<H', our_pkt, 10)[0]
check("风扇0 PWM值=1000", val == 1000, f"实际={val}")
log(f"    风扇0原始字节: {our_pkt[10]:02X} {our_pkt[11]:02X} {our_pkt[12]:02X} {our_pkt[13]:02X}")

# ------- 测试3: 单板50% -------
log("\n--- 测试3: 板0全部风扇50% ---")
fc_pkt = fan_control_build_frame(0, 50, {0: [True]*16})
our_pkt, _ = udp_sender_build_packet(0, {0: [500]*16})

match = fc_pkt == our_pkt
check("与fan_control.py完全一致", match)
if not match:
    for i in range(min(651, len(fc_pkt), len(our_pkt))):
        if fc_pkt[i] != our_pkt[i]:
            log(f"    首个差异在字节[{i}]: fan_control=0x{fc_pkt[i]:02X}, ours=0x{our_pkt[i]:02X}")
            break

# ------- 测试4: 多板不同PWM -------
log("\n--- 测试4: 板0=1000, 板6=500, 板9=200 ---")
boards_data = {
    0: [1000]*16,
    6: [500]*16,
    9: [200]*16,
}
our_pkt, _ = udp_sender_build_packet(0, boards_data)

# 验证板0
val0 = struct.unpack_from('<H', our_pkt, 10)[0]
check("板0风扇0 PWM=1000", val0 == 1000, f"实际={val0}")

# 验证板6
board6_offset = 10 + 6 * 64
val6 = struct.unpack_from('<H', our_pkt, board6_offset)[0]
check("板6风扇0 PWM=500", val6 == 500, f"实际={val6}, 偏移={board6_offset}")

# 验证板9
board9_offset = 10 + 9 * 64
val9 = struct.unpack_from('<H', our_pkt, board9_offset)[0]
check("板9风扇0 PWM=200", val9 == 200, f"实际={val9}, 偏移={board9_offset}")

# 验证空板（板1-5, 7-8）为0
board1_offset = 10 + 1 * 64
val_empty = struct.unpack_from('<H', our_pkt, board1_offset)[0]
check("空板(板1)PWM=0", val_empty == 0, f"实际={val_empty}")

# ------- 测试5: 帧号递增 -------
log("\n--- 测试5: 帧号小端序递增 ---")
pkt1, fc1 = udp_sender_build_packet(0, {0: [0]*16})
pkt2, fc2 = udp_sender_build_packet(fc1, {0: [0]*16})
pkt3, fc3 = udp_sender_build_packet(fc2, {0: [0]*16})

fn1 = struct.unpack_from('<I', pkt1, 1)[0]
fn2 = struct.unpack_from('<I', pkt2, 1)[0]
fn3 = struct.unpack_from('<I', pkt3, 1)[0]

check("帧号从0开始", fn1 == 0, f"实际={fn1}")
check("帧号递增到1", fn2 == 1, f"实际={fn2}")
check("帧号递增到2", fn3 == 2, f"实际={fn3}")

# 验证小端序字节序
log(f"    帧号0字节: {pkt1[1]:02X} {pkt1[2]:02X} {pkt1[3]:02X} {pkt1[4]:02X} (小端序期望: 00 00 00 00)")
log(f"    帧号1字节: {pkt2[1]:02X} {pkt2[2]:02X} {pkt2[3]:02X} {pkt2[4]:02X} (小端序期望: 01 00 00 00)")

# 大帧号测试
pkt_big, _ = udp_sender_build_packet(255, {0: [0]*16})
fn_big = struct.unpack_from('<I', pkt_big, 1)[0]
check("帧号255", fn_big == 255, f"实际={fn_big}")
log(f"    帧255字节: {pkt_big[1]:02X} {pkt_big[2]:02X} {pkt_big[3]:02X} {pkt_big[4]:02X} (期望: FF 00 00 00)")

pkt_256, _ = udp_sender_build_packet(256, {0: [0]*16})
fn_256 = struct.unpack_from('<I', pkt_256, 1)[0]
check("帧号256(跨字节)", fn_256 == 256, f"实际={fn_256}")
log(f"    帧256字节: {pkt_256[1]:02X} {pkt_256[2]:02X} {pkt_256[3]:02X} {pkt_256[4]:02X} (期望: 00 01 00 00)")

# ------- 测试6: 每个风扇占4字节（2个副本）-------
log("\n--- 测试6: 每风扇4字节双副本 ---")
pwm_test = 777
our_pkt, _ = udp_sender_build_packet(0, {0: [pwm_test] + [0]*15})

# 风扇0的字节偏移 = 10 + 0*64 + 0*4 = 10
b0 = struct.unpack_from('<H', our_pkt, 10)[0]
b0_copy = struct.unpack_from('<H', our_pkt, 12)[0]
check("风扇0第1个值=777", b0 == pwm_test, f"实际={b0}")
check("风扇0第2个值(副本)=777", b0_copy == pwm_test, f"实际={b0_copy}")
log(f"    风扇0四个字节: {our_pkt[10]:02X} {our_pkt[11]:02X} {our_pkt[12]:02X} {our_pkt[13]:02X}")
log(f"    777=0x{pwm_test:04X}, 小端序: {pwm_test&0xFF:02X} {(pwm_test>>8)&0xFF:02X}")

# 风扇1的字节偏移 = 10 + 0*64 + 1*4 = 14
b1 = struct.unpack_from('<H', our_pkt, 14)[0]
check("风扇1(未设置)PWM=0", b1 == 0, f"实际={b1}")

# ------- 测试7: PWM值范围钳位 -------
log("\n--- 测试7: PWM值钳位(0-1000) ---")
our_pkt, _ = udp_sender_build_packet(0, {0: [2000] + [-100] + [500] + [0]*13})
v_over = struct.unpack_from('<H', our_pkt, 10)[0]
v_under = struct.unpack_from('<H', our_pkt, 14)[0]
v_normal = struct.unpack_from('<H', our_pkt, 18)[0]
check("超限值2000->钳位到1000", v_over == 1000, f"实际={v_over}")
check("负值-100->钳位到0", v_under == 0, f"实际={v_under}")
check("正常值500保持不变", v_normal == 500, f"实际={v_normal}")

# ------- 测试8: 数据长度字段大端序 -------
log("\n--- 测试8: 数据长度字段 ---")
our_pkt, _ = udp_sender_build_packet(0, {0: [0]*16})
dlen_byte8 = our_pkt[8]
dlen_byte9 = our_pkt[9]
dlen_val = struct.unpack_from('>H', our_pkt, 8)[0]
check("数据长度=640", dlen_val == 640, f"实际={dlen_val}")
check("字节[8]=0x02", dlen_byte8 == 0x02, f"实际=0x{dlen_byte8:02X}")
check("字节[9]=0x80", dlen_byte9 == 0x80, f"实际=0x{dlen_byte9:02X}")

# ------- 测试9: 40x40网格数据到PWM转换 -------
log("\n--- 测试9: 网格百分比->PWM转换 ---")
grid = np.zeros((40, 40), dtype=float)
grid[0, 0] = 100.0   # 100%
grid[0, 1] = 50.0    # 50%
grid[0, 2] = 10.0    # 10%
grid[0, 3] = 0.0     # 0%

# 提取板0(网格[0:4, 0:4])的PWM值
pwm_max = 1000
pwm_values = []
for fan_id in range(16):
    row = fan_id // 4
    col = fan_id % 4
    percent = grid[row, col]
    pwm_value = int((percent / 100.0) * pwm_max)
    pwm_values.append(pwm_value)

our_pkt, _ = udp_sender_build_packet(0, {0: pwm_values})
# 风扇0=100% -> 1000
v0 = struct.unpack_from('<H', our_pkt, 10)[0]
check("网格100%->PWM=1000", v0 == 1000, f"实际={v0}")
# 风扇1=50% -> 500
v1 = struct.unpack_from('<H', our_pkt, 14)[0]
check("网格50%->PWM=500", v1 == 500, f"实际={v1}")
# 风扇2=10% -> 100
v2 = struct.unpack_from('<H', our_pkt, 18)[0]
check("网格10%->PWM=100", v2 == 100, f"实际={v2}")
# 风扇3=0% -> 0
v3 = struct.unpack_from('<H', our_pkt, 22)[0]
check("网格0%->PWM=0", v3 == 0, f"实际={v3}")

# ------- 测试10: 完整包hex与fan_control.py逐字节对比 -------
log("\n--- 测试10: 完整包逐字节对比(fan_control.py vs udp_fan_sender.py) ---")

# 构建fan_control.py的参考包
fc_boards = {}
for bid in range(10):
    fc_boards[bid] = [True]*16
fc_pkt = fan_control_build_frame(5, 75, fc_boards)

# 构建udp_fan_sender.py的包
our_boards = {}
for bid in range(10):
    our_boards[bid] = [750]*16  # 75% * 1000 = 750
our_pkt, _ = udp_sender_build_packet(5, our_boards)

byte_diffs = []
for i in range(651):
    if fc_pkt[i] != our_pkt[i]:
        byte_diffs.append((i, fc_pkt[i], our_pkt[i]))

check("全10板75%包完全一致", len(byte_diffs) == 0, f"差异字节数={len(byte_diffs)}")
if byte_diffs:
    log(f"    前10个差异:")
    for idx, (pos, fc_val, our_val) in enumerate(byte_diffs[:10]):
        log(f"      字节[{pos}]: fan_control=0x{fc_val:02X}, ours=0x{our_val:02X}")

# ------- 测试11: 包结构完整性 -------
log("\n--- 测试11: 包结构字段位置验证 ---")
our_pkt, _ = udp_sender_build_packet(0, {0: [123]*16})

# 验证头部10字节
log(f"  头部10字节: {' '.join(f'{our_pkt[i]:02X}' for i in range(10))}")
check("[0] 帧头=0xAA", our_pkt[0] == 0xAA)
check("[1-4] 帧号小端序", our_pkt[1] == 0x00 and our_pkt[2] == 0x00 and our_pkt[3] == 0x00 and our_pkt[4] == 0x00)
check("[5] 帧类型=0x01", our_pkt[5] == 0x01)
check("[6] 链路ID=0x00", our_pkt[6] == 0x00)
check("[7] 电驱板ID=0x00", our_pkt[7] == 0x00)
check("[8-9] 数据长度=0x0280", our_pkt[8] == 0x02 and our_pkt[9] == 0x80)

# 验证尾部
log(f"  尾部字节: [... {our_pkt[649]:02X}] [{our_pkt[650]:02X}]")
check("[650] 帧尾=0xCC", our_pkt[650] == 0xCC)

# 验证数据区大小 (字节10到649)
check("数据区=640字节", len(our_pkt) - 10 - 1 == 640)

# ======= 总结 =======
log("\n" + "=" * 80)
log("测试总结")
log("=" * 80)
pass_count = sum(1 for _, s, _ in results if s == "PASS")
fail_count = sum(1 for _, s, _ in results if s == "FAIL")
log(f"  总测试项: {len(results)}")
log(f"  通过: {pass_count}")
log(f"  失败: {fail_count}")

if fail_count > 0:
    log(f"\n  失败项:")
    for name, status, detail in results:
        if status == "FAIL":
            log(f"    - {name}: {detail}")
else:
    log(f"\n  所有测试通过!")

# 写入日志文件
log_file = os.path.join(os.path.dirname(__file__), 'data', f'autotest_{os.path.basename(__file__).replace(".py","")}.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))
log(f"\n日志已写入: {log_file}")
