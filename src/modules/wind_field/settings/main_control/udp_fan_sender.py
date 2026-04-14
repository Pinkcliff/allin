# -*- coding: utf-8 -*-
"""
UDP风扇控制模块 - 651字节协议版本

电驱板通信协议帧格式（参照 fan_control.py）：
  [0]       AA           帧头(固定)
  [1-4]     帧号         4字节小端序递增，每发一包+1
  [5]       01           帧类型(设置参数)
  [6]       00           链路ID(固定0x00)
  [7]       00           电驱板ID(固定0x00)
  [8-9]     02 80        数据长度(640字节, 大端序)
  [10-649]  数据区       10块板 × 64字节, 板N偏移=N×64
  [650]     CC           帧尾(固定)

数据区布局(640字节):
  每块板64字节 = 16个风扇 × 2个参数(各2字节小端序)
  风扇N的数据偏移 = 板偏移 + N × 4
    [0-1] PWM值(小端序)
    [2-3] PWM值副本(小端序)

PWM范围: 0-1000, 100% = 1000
发送粒度: 每个链路(10块板)一包, 共10个链路 = 10包

IP映射: 每行10个板共享1个IP
  链路0 (板0-9)   -> 192.168.1.100
  链路1 (板10-19) -> 192.168.1.101
  ...
  链路9 (板90-99) -> 192.168.1.109
"""

import socket
import struct
import time
import threading
from typing import Optional, Dict, Tuple, List
import numpy as np
import logging
from datetime import datetime
import os
import csv
import threading as threading_module

# 协议配置
PROTOCOL_CONFIG = {
    'controller_ip': '192.168.1.101',   # 中控机以太网口IP
    'local_bind_ip': '192.168.1.101',   # 绑定本地网口IP
    'board_ip_start': '192.168.1.100',  # 第1行(链路0) -> 192.168.1.100
    'board_ip_end': '192.168.1.109',    # 第10行(链路9) -> 192.168.1.109
    'udp_port': 6005,
    'fans_per_board': 16,
    'boards_per_chain': 10,  # 每个链路10个板
    'chains_total': 10,       # 总共10个链路
    'pwm_max': 1000,          # 100% = 1000
    'packet_size': 651,       # 651字节完整包
    'bytes_per_board': 64,    # 每块板在数据区占64字节
}


def setup_udp_logger(log_dir: str = None) -> logging.Logger:
    """设置UDP发送日志记录器"""
    logger = logging.getLogger('FanUDP')
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'udp_send_{timestamp}.log')

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s).%(msecs)03d | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info('=' * 80)
    logger.info(f'UDP发送日志文件: {log_file}')
    logger.info('=' * 80)

    return logger


_udp_logger = None


def get_udp_logger() -> logging.Logger:
    """获取UDP日志记录器"""
    global _udp_logger
    if _udp_logger is None:
        _udp_logger = setup_udp_logger()
    return _udp_logger


class FanUDPSender:
    """UDP风扇数据发送器

    将40x40的风扇网格数据发送到100个电驱板
    每个电驱板对应4x4的风扇块，ID从0-99
    按链路发送: 每个链路(10块板)打包成一包651字节数据
    """

    def __init__(self, board_ip_start: str = None, udp_port: int = None,
                 local_bind_ip: str = None, enable_logging: bool = True):
        """
        初始化UDP发送器

        Args:
            board_ip_start: 电驱板起始IP，默认192.168.1.100
            udp_port: UDP端口，默认6005
            local_bind_ip: 绑定本地网口IP，默认192.168.1.101（以太网口）
            enable_logging: 是否启用日志
        """
        self.board_ip_start = board_ip_start or PROTOCOL_CONFIG['board_ip_start']
        self.udp_port = udp_port or PROTOCOL_CONFIG['udp_port']
        self.local_bind_ip = local_bind_ip or PROTOCOL_CONFIG['local_bind_ip']
        self.enable_logging = enable_logging

        # 日志配置（需要在socket绑定前初始化）
        if self.enable_logging:
            self.logger = get_udp_logger()
        else:
            self.logger = None

        # 创建UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
        self.sock.settimeout(0.1)

        # 绑定到指定网口
        try:
            self.sock.bind((self.local_bind_ip, 0))
            if self.enable_logging and self.logger:
                self.logger.info(f'已绑定到本地网口: {self.local_bind_ip}')
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f'绑定到网口 {self.local_bind_ip} 失败: {e}')

        # 帧计数器(4字节, 自增)
        self.frame_counter = 0

        # 统计信息
        self.stats = {
            'total_packets': 0,
            'success_packets': 0,
            'failed_packets': 0,
            'last_send_time': None,
        }

        # 数据记录目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)

        # 记录每个风扇的当前PWM值
        self.fan_pwm_states = {}
        self.pwm_lock = threading_module.Lock()

        # 风扇ID映射表：逻辑风扇ID -> 物理风扇ID
        self.fan_id_mapping = {
            0: 13, 1: 9, 2: 5, 3: 1,
            4: 14, 5: 10, 6: 6, 7: 2,
            8: 15, 9: 11, 10: 7, 11: 3,
            12: 16, 13: 12, 14: 8, 15: 4,
        }
        self.physical_to_logical_fan = {v: k for k, v in self.fan_id_mapping.items()}

        # CSV文件锁和写入器
        self.csv_lock = threading_module.Lock()
        self.csv_writer = None
        self.csv_file = None
        self._init_csv_file()

        # 播放模式标志
        self.playback_mode = False

        # 原始数据TXT文件
        self.raw_data_file = None
        self._init_raw_data_file()

        if self.enable_logging and self.logger:
            self.logger.info('=' * 60)
            self.logger.info('FanUDPSender 初始化完成 (协议: 651字节 AA...CC)')
            self.logger.info(f'PWM满值: {PROTOCOL_CONFIG["pwm_max"]} (100%=1000)')
            self.logger.info(f'发送粒度: 每链路1包(10板), 共10包')
            self.logger.info(f'IP范围: 192.168.1.100-109')
            self.logger.info('=' * 60)

    def _get_chain_ip(self, chain_id: int) -> str:
        """
        根据链路ID获取IP地址

        Args:
            chain_id: 链路ID (0-9)

        Returns:
            str: IP地址
        """
        ip_parts = self.board_ip_start.split('.')
        last_octet = int(ip_parts[3]) + chain_id
        return f"192.168.1.{last_octet}"

    def _get_board_ip(self, board_id: int) -> str:
        """根据全局板ID获取IP (兼容旧接口)"""
        return self._get_chain_ip(board_id // 10)

    def _init_csv_file(self):
        """初始化CSV文件，写入表头"""
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            csv_file = os.path.join(self.data_dir, f'fan_data_{date_str}.csv')

            if not os.path.exists(csv_file):
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        '时间', 'IP地址', '风扇ID',
                        '链路ID', '板ID', '原PWM值', '新PWM值', '变化值'
                    ])
            self.csv_file = csv_file
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"初始化CSV文件失败: {e}")

    def _init_raw_data_file(self):
        """初始化原始数据记录TXT文件"""
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            raw_data_file = os.path.join(self.data_dir, f'raw_data_{date_str}.txt')

            if not os.path.exists(raw_data_file):
                with open(raw_data_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"风机通讯原始数据记录 - {date_str}\n")
                    f.write("=" * 80 + "\n\n")

            self.raw_data_file = raw_data_file
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"初始化原始数据文件失败: {e}")

    def _build_chain_packet(self, boards_pwm_data: dict) -> bytes:
        """
        构建一个链路的651字节数据包（参照 fan_control.py _build_frame）

        帧结构:
          [0]     AA         帧头
          [1-4]   帧号       4字节小端序递增
          [5]     01         帧类型(设置参数)
          [6]     00         链路ID(固定)
          [7]     00         电驱板ID(固定0x00)
          [8-9]   02 80      数据长度(640, 大端序)
          [10-649] 数据区    10板×64字节, 板N偏移=N×64
          [650]   CC         帧尾

        每板64字节:
          风扇N占4字节: [PWM低, PWM高, PWM低(副本), PWM高(副本)]
          风扇N偏移 = 板偏移 + N × 4

        Args:
            boards_pwm_data: {board_id(0-9): [16个PWM值(0-1000)], ...}

        Returns:
            bytes: 651字节的数据包
        """
        # 帧头
        header = struct.pack('B', 0xAA)
        # 帧号(4字节小端序, 自增)
        frame_num = struct.pack('<I', self.frame_counter)
        self.frame_counter = (self.frame_counter + 1) & 0xFFFFFFFF
        # 帧类型
        frame_type = struct.pack('B', 0x01)
        # 链路ID
        link_id = struct.pack('B', 0x00)
        # 电驱板ID(固定0x00)
        board_id_byte = struct.pack('B', 0x00)
        # 数据长度(640字节, 大端序)
        data_len = struct.pack('>H', 640)

        # 数据区: 640字节, 全零初始化
        data = bytearray(640)

        # 填充每块板的风扇数据
        pwm_max = PROTOCOL_CONFIG['pwm_max']
        for board_id, pwm_values in boards_pwm_data.items():
            board_offset = board_id * PROTOCOL_CONFIG['bytes_per_board']
            for fan_id in range(min(16, len(pwm_values))):
                pwm = max(0, min(pwm_max, pwm_values[fan_id]))
                # 每个风扇占2个参数位置(4字节)
                offset = board_offset + fan_id * 4
                struct.pack_into('<H', data, offset, pwm)
                struct.pack_into('<H', data, offset + 2, pwm)

        # 帧尾
        tail = struct.pack('B', 0xCC)

        return header + frame_num + frame_type + link_id + board_id_byte + data_len + bytes(data) + tail

    def _log_raw_data(self, ip: str, port: int, packet: bytes, packet_type: str):
        """记录发送的原始数据包"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            date_str = datetime.now().strftime('%Y%m%d')
            expected_file = os.path.join(self.data_dir, f'raw_data_{date_str}.txt')
            if self.raw_data_file != expected_file:
                self._init_raw_data_file()
                expected_file = self.raw_data_file

            hex_str = ' '.join(f'{b:02X}' for b in packet)
            packet_length = len(packet)

            log_entry = f"""
{'=' * 60}
时间: {timestamp}
类型: {packet_type}
目标: {ip}:{port}
长度: {packet_length} 字节
数据包内容 (HEX):
{hex_str}

数据包详细解析:
"""

            if packet_type == '651byte' and packet_length == 651:
                log_entry += f"  帧头: 0x{packet[0]:02X}\n"
                # 帧号: 小端序4字节
                frame_num = struct.unpack_from('<I', packet, 1)[0]
                log_entry += f"  帧号: {frame_num}\n"
                log_entry += f"  帧类型: 0x{packet[5]:02X}\n"
                log_entry += f"  链路ID: {packet[6]}\n"
                log_entry += f"  电驱板ID: {packet[7]} (固定0x00)\n"
                data_len = struct.unpack_from('>H', packet, 8)[0]
                log_entry += f"  数据长度: {data_len}\n"
                log_entry += f"\n  各板PWM数据 (小端序, 每风扇4字节):\n"
                for board_id in range(10):
                    board_offset = board_id * 64
                    has_data = False
                    for fan_id in range(16):
                        offset = board_offset + fan_id * 4
                        pwm_val = struct.unpack_from('<H', packet, 10 + offset)[0]
                        if pwm_val > 0:
                            has_data = True
                            break
                    if has_data:
                        log_entry += f"    板{board_id}:\n"
                        for fan_id in range(16):
                            offset = board_offset + fan_id * 4
                            pwm_val = struct.unpack_from('<H', packet, 10 + offset)[0]
                            if pwm_val > 0:
                                percent = pwm_val * 100 // PROTOCOL_CONFIG['pwm_max']
                                log_entry += f"      风扇{fan_id:2d}: PWM={pwm_val:4d} ({percent:3d}%)\n"
                log_entry += f"  帧尾: 0x{packet[650]:02X}\n"

            log_entry += "\n"

            with self.csv_lock:
                with open(expected_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"记录原始数据失败: {e}")

    def _log_fan_data(self, ip: str, fan_id: int, chain_id: int, board_id: int, new_pwm: int):
        """记录风机通讯数据到CSV文件"""
        try:
            physical_fan_id = self.fan_id_mapping.get(fan_id, fan_id)
            fan_key = f"{ip}_{physical_fan_id}"

            with self.pwm_lock:
                old_pwm = self.fan_pwm_states.get(fan_key, 0)
                self.fan_pwm_states[fan_key] = new_pwm

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            pwm_change = new_pwm - old_pwm

            with self.csv_lock:
                date_str = datetime.now().strftime('%Y%m%d')
                expected_file = os.path.join(self.data_dir, f'fan_data_{date_str}.csv')
                if self.csv_file != expected_file:
                    self._init_csv_file()
                    expected_file = self.csv_file

                with open(expected_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, ip, physical_fan_id,
                        chain_id, board_id, old_pwm, new_pwm, pwm_change
                    ])
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"记录风机数据失败: {e}")

    def send_to_board(self, chain_id: int, board_id: int, fan_id: int, pwm_value: int) -> bool:
        """
        发送控制数据到单个风扇

        实际发送整条链路的651字节包，只有指定板+风扇有值

        Args:
            chain_id: 链路ID (0-9)
            board_id: 电驱板ID (0-9)
            fan_id: 风扇ID (0-15)
            pwm_value: PWM值 (0-1000)

        Returns:
            bool: 发送成功返回True
        """
        if chain_id < 0 or chain_id >= 10:
            if self.enable_logging and self.logger:
                self.logger.error(f"无效的链路ID: {chain_id}")
            return False

        if board_id < 0 or board_id >= 10:
            if self.enable_logging and self.logger:
                self.logger.error(f"无效的电驱板ID: {board_id}")
            return False

        if fan_id < 0 or fan_id >= 16:
            if self.enable_logging and self.logger:
                self.logger.error(f"无效的风扇ID: {fan_id}")
            return False

        try:
            # 只填充指定板+风扇的PWM值，其余全零
            pwm_values = [0] * 16
            pwm_values[fan_id] = max(0, min(PROTOCOL_CONFIG['pwm_max'], pwm_value))

            boards_data = {board_id: pwm_values}
            packet = self._build_chain_packet(boards_data)

            target_ip = self._get_chain_ip(chain_id)
            target_addr = (target_ip, self.udp_port)
            self.sock.sendto(packet, target_addr)

            self.stats['total_packets'] += 1
            self.stats['success_packets'] += 1
            self.stats['last_send_time'] = datetime.now()

            global_board_id = chain_id * 10 + board_id
            hex_str = ' '.join(f'{b:02X}' for b in packet)
            print(f"[UDP发送] 板ID:{global_board_id:2d} | IP:{target_ip}:{self.udp_port} | 链路:{chain_id} 板内:{board_id} | 风扇{fan_id} PWM:{pwm_value}")
            print(f"[UDP数据] {hex_str}")

            return True

        except Exception as e:
            self.stats['total_packets'] += 1
            self.stats['failed_packets'] += 1
            if self.enable_logging and self.logger:
                self.logger.error(f"发送失败: Chain={chain_id} Board={board_id} Fan={fan_id} Error={e}")
            return False

    def send_grid_to_boards(self, grid_data: np.ndarray,
                            callback=None) -> Dict[int, bool]:
        """
        将40x40的网格数据发送到所有电驱板（按链路打包）

        Args:
            grid_data: 40x40的numpy数组，值为0-100的百分比
            callback: 发送完成回调函数 (success_count, fail_count, elapsed_time)

        Returns:
            Dict[int, bool]: 每个风扇的发送结果
        """
        if grid_data.shape != (40, 40):
            if self.enable_logging and self.logger:
                self.logger.error(f"网格数据形状错误: {grid_data.shape}, 需要(40, 40)")
            return {}

        if self.enable_logging and self.logger:
            self.logger.info(f"开始发送100个控制板数据 (范围: {grid_data.min():.1f}%-{grid_data.max():.1f}%)")

        results = {}
        success_count = 0
        fail_count = 0
        start_time = time.time()

        for chain_id in range(10):
            for board_in_chain in range(10):
                global_board_id = chain_id * 10 + board_in_chain

                row_start = global_board_id // 10 * 4
                col_start = (global_board_id % 10) * 4
                module_data = grid_data[row_start:row_start + 4, col_start:col_start + 4]

                for logical_fan_id in range(16):
                    row = logical_fan_id // 4
                    col = logical_fan_id % 4
                    percent = module_data[row, col]
                    pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])

                    success = self.send_to_board(chain_id, board_in_chain, logical_fan_id, pwm_value)
                    results[global_board_id * 16 + logical_fan_id] = success

                    if success:
                        success_count += 1
                    else:
                        fail_count += 1

        elapsed_time = time.time() - start_time
        if self.enable_logging and self.logger:
            self.logger.info(f"发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms")

        if callback:
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_to_selected_boards(self, grid_data: np.ndarray,
                                 selected_cells: set,
                                 callback=None) -> Dict[int, bool]:
        """
        只发送选中的风扇对应的电驱板

        按链路分组，每个链路构建一包651字节数据

        Args:
            grid_data: 40x40的numpy数组
            selected_cells: 选中的单元格集合
            callback: 发送完成回调函数

        Returns:
            Dict[int, bool]: 每个模块的发送结果
        """
        results = {}
        success_count = 0
        fail_count = 0
        start_time = time.time()

        # 找出所有受影响的模块
        affected_boards = set()
        for cell in selected_cells:
            global_board_id = cell.row // 4 * 10 + cell.col // 4
            affected_boards.add(global_board_id)

        # 按链路分组
        chain_groups = {}
        for global_board_id in affected_boards:
            chain_id = global_board_id // 10
            board_in_chain = global_board_id % 10
            if chain_id not in chain_groups:
                chain_groups[chain_id] = {}
            chain_groups[chain_id][board_in_chain] = global_board_id

        # 每个链路构建一包
        for chain_id, boards in chain_groups.items():
            boards_pwm_data = {}
            for board_in_chain, global_board_id in boards.items():
                row_start = global_board_id // 10 * 4
                col_start = (global_board_id % 10) * 4
                module_data = grid_data[row_start:row_start + 4, col_start:col_start + 4]

                pwm_values = []
                for fan_id in range(16):
                    row = fan_id // 4
                    col = fan_id % 4
                    percent = module_data[row, col]
                    pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                    pwm_values.append(pwm_value)
                boards_pwm_data[board_in_chain] = pwm_values

            try:
                packet = self._build_chain_packet(boards_pwm_data)
                target_ip = self._get_chain_ip(chain_id)
                target_addr = (target_ip, self.udp_port)
                self.sock.sendto(packet, target_addr)

                self.stats['total_packets'] += 1
                self.stats['success_packets'] += 1
                self.stats['last_send_time'] = datetime.now()

                for global_board_id in boards.values():
                    results[global_board_id] = True
                    success_count += 1

                hex_str = ''.join(f'{b:02X}' for b in packet)
                board_list = list(boards.values())
                print(f"[UDP选中发送] 链路:{chain_id} 板:{board_list} | IP:{target_ip}:{self.udp_port}")
                print(f"[UDP数据] {hex_str}")

                # 日志记录
                for board_in_chain, global_board_id in boards.items():
                    pwm_values = boards_pwm_data[board_in_chain]
                    for fan_id in range(16):
                        self._log_fan_data(target_ip, fan_id, chain_id, board_in_chain, pwm_values[fan_id])

                self._log_raw_data(target_ip, self.udp_port, packet, '651byte')

            except Exception as e:
                self.stats['total_packets'] += 1
                self.stats['failed_packets'] += 1
                for global_board_id in boards.values():
                    results[global_board_id] = False
                    fail_count += 1
                if self.enable_logging and self.logger:
                    self.logger.error(f"发送失败: Chain={chain_id} Error={e}")

        if callback:
            elapsed_time = time.time() - start_time
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_grid_to_boards_bulk(self, grid_data: np.ndarray, callback=None) -> Dict[int, bool]:
        """
        按链路打包发送40x40网格数据到所有电驱板

        每个链路(10块板)构建一包651字节数据，共发送10包
        比逐板发送(100包)效率提升10倍

        Args:
            grid_data: 40x40的numpy数组，值为0-100的百分比
            callback: 发送完成回调函数

        Returns:
            Dict[int, bool]: 每个电驱板的发送结果
        """
        try:
            if grid_data is None or grid_data.shape != (40, 40):
                if self.enable_logging and self.logger:
                    self.logger.error(f"网格数据形状错误: {grid_data.shape if grid_data is not None else 'None'}, 需要(40, 40)")
                return {}

            is_playback = self.playback_mode

            if self.enable_logging and self.logger and not is_playback:
                self.logger.info(f"开始发送 (范围: {grid_data.min():.1f}%-{grid_data.max():.1f}%)")

            results = {}
            success_count = 0
            fail_count = 0
            start_time = time.time()

            # 按链路发送，每链路一包
            for chain_id in range(10):
                boards_pwm_data = {}

                for board_in_chain in range(10):
                    global_board_id = chain_id * 10 + board_in_chain
                    row_start = global_board_id // 10 * 4
                    col_start = (global_board_id % 10) * 4
                    module_data = grid_data[row_start:row_start + 4, col_start:col_start + 4]

                    pwm_values = []
                    for fan_id in range(16):
                        row = fan_id // 4
                        col = fan_id % 4
                        percent = module_data[row, col]
                        pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                        pwm_values.append(pwm_value)

                    boards_pwm_data[board_in_chain] = pwm_values

                # 构建该链路的651字节包
                packet = self._build_chain_packet(boards_pwm_data)

                if not packet or len(packet) != 651:
                    for board_in_chain in range(10):
                        global_board_id = chain_id * 10 + board_in_chain
                        results[global_board_id] = False
                        fail_count += 1
                    continue

                try:
                    target_ip = self._get_chain_ip(chain_id)
                    target_addr = (target_ip, self.udp_port)
                    self.sock.sendto(packet, target_addr)

                    self.stats['total_packets'] += 1
                    self.stats['success_packets'] += 1
                    self.stats['last_send_time'] = datetime.now()

                    for board_in_chain in range(10):
                        global_board_id = chain_id * 10 + board_in_chain
                        results[global_board_id] = True
                        success_count += 1

                    if not is_playback:
                        hex_str = ''.join(f'{b:02X}' for b in packet)
                        print(f"[UDP发送] 链路:{chain_id} | IP:{target_ip}:{self.udp_port} | 10块板打包")
                        print(f"[UDP数据] {hex_str}")

                        for board_in_chain in range(10):
                            pwm_values = boards_pwm_data[board_in_chain]
                            for fan_id in range(16):
                                self._log_fan_data(target_ip, fan_id, chain_id, board_in_chain, pwm_values[fan_id])

                        self._log_raw_data(target_ip, self.udp_port, packet, '651byte')

                except Exception as e:
                    self.stats['total_packets'] += 1
                    self.stats['failed_packets'] += 1
                    for board_in_chain in range(10):
                        global_board_id = chain_id * 10 + board_in_chain
                        results[global_board_id] = False
                        fail_count += 1
                    if self.enable_logging and self.logger:
                        self.logger.error(f"发送失败: Chain={chain_id} Error={e}")

            elapsed_time = time.time() - start_time
            if self.enable_logging and self.logger and not is_playback:
                self.logger.info(f"发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms ({success_count//10}包)")

            if callback:
                try:
                    callback(success_count, fail_count, elapsed_time)
                except Exception as cb_error:
                    pass

            return results

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.error(f"批量发送过程发生异常: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        if self.enable_logging and self.logger:
            self.logger.info('=' * 60)
            self.logger.info("UDP发送统计报告")
            self.logger.info('=' * 60)
            self.logger.info(f"总数据包: {stats['total_packets']}")
            self.logger.info(f"成功: {stats['success_packets']}")
            self.logger.info(f"失败: {stats['failed_packets']}")

            if stats['total_packets'] > 0:
                success_rate = (stats['success_packets'] / stats['total_packets']) * 100
                self.logger.info(f"成功率: {success_rate:.1f}%")

            if stats['last_send_time']:
                self.logger.info(f"最后发送: {stats['last_send_time']}")
            self.logger.info('=' * 60)

    def close(self):
        """关闭socket"""
        try:
            if self.sock:
                self.sock.close()
                if self.enable_logging and self.logger:
                    self.logger.info("UDP发送器已关闭")
        except Exception:
            pass

    def __del__(self):
        """析构函数"""
        self.close()


class AsyncFanUDPSender(FanUDPSender):
    """异步UDP风扇发送器

    在后台线程中发送数据，避免阻塞UI
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.send_queue = []
        self.queue_lock = threading.Lock()
        self.worker_thread = None
        self.running = False
        self.send_interval = 0.01

    def start(self):
        """启动后台发送线程"""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.worker_thread.start()

        if self.enable_logging:
            self.logger.info("异步发送线程已启动")

    def stop(self):
        """停止后台发送线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)

        if self.enable_logging:
            self.logger.info("异步发送线程已停止")

    def _send_loop(self):
        """后台发送循环"""
        while self.running:
            with self.queue_lock:
                if self.send_queue:
                    task = self.send_queue.pop(0)
                else:
                    task = None

            if task:
                try:
                    self._process_task(task)
                except Exception as e:
                    if self.enable_logging and self.logger:
                        self.logger.error(f"后台任务处理异常: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                time.sleep(self.send_interval)

    def _process_task(self, task):
        """处理发送任务"""
        try:
            task_type = task.get('type')

            if task_type == 'single':
                chain_id = task.get('chain_id', 0)
                board_id = task.get('board_id', 0)
                fan_id = task.get('fan_id', 0)
                pwm_value = task.get('pwm_value', 0)
                self.send_to_board(chain_id, board_id, fan_id, pwm_value)

            elif task_type == 'grid':
                grid_data = task['grid_data']
                callback = task.get('callback')
                self.send_grid_to_boards_bulk(grid_data, callback)

            elif task_type == 'bulk':
                grid_data = task['grid_data']
                self.send_grid_to_boards_bulk(grid_data, callback=None)

            elif task_type == 'selected':
                grid_data = task['grid_data']
                selected_cells = task['selected_cells']
                callback = task.get('callback')
                self.send_to_selected_boards(grid_data, selected_cells, callback)

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.error(f"后台任务处理异常: {e}")
            import traceback
            traceback.print_exc()

    def queue_send_to_fan(self, chain_id: int, board_id: int, fan_id: int, pwm_value: int):
        """将单个风扇控制任务加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'single',
                'chain_id': chain_id,
                'board_id': board_id,
                'fan_id': fan_id,
                'pwm_value': pwm_value
            })

    def queue_send_grid(self, grid_data: np.ndarray, callback=None):
        """将全网格发送任务加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'grid',
                'grid_data': grid_data.copy(),
                'callback': callback
            })

    def queue_send_selected(self, grid_data: np.ndarray,
                            selected_cells: set, callback=None):
        """将选中区域发送任务加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'selected',
                'grid_data': grid_data.copy(),
                'selected_cells': selected_cells,
                'callback': callback
            })

    def queue_send_bulk(self, grid_data: np.ndarray, callback=None):
        """将全网格批量发送任务加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'bulk',
                'grid_data': grid_data.copy(),
                'callback': callback
            })


# 便捷函数
def create_udp_sender(enable_logging: bool = True,
                      async_mode: bool = False) -> FanUDPSender:
    """创建UDP发送器"""
    if async_mode:
        return AsyncFanUDPSender(enable_logging=enable_logging)
    else:
        return FanUDPSender(enable_logging=enable_logging)
