# -*- coding: utf-8 -*-
"""
UDP风扇控制模块 - 新协议版本

协议说明（5字节包）：
  0-1字节: chain_id    链路ID (0-9)
  1-1字节: board_id    电驱板ID (0-9)
  2-1字节: fan_id      风扇ID (0-15)
  3-1字节: pwm低字节   PWM等级低字节 (0-999)
  4-1字节: pwm高字节   PWM等级高字节 (0-999)

IP映射: 板ID 0-99 -> 192.168.1.1-100
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
    'board_ip_start': '192.168.1.1',    # ID0 -> 1
    'board_ip_end': '192.168.1.100',     # ID99 -> 100
    'udp_port': 5001,
    'fans_per_board': 16,
    'boards_per_chain': 10,  # 每个链路10个板
    'chains_total': 10,       # 总共10个链路
    'pwm_max': 999,
    'control_packet_size': 5,   # 5字节包
    'bulk_packet_size': 80,     # 80字节包（16个风扇 × 5字节）
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
        '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s',
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
    """UDP风扇数据发送器 - 新协议版本

    将40x40的风扇网格数据发送到100个电驱板
    每个电驱板对应4x4的风扇块，ID从0-99
    """

    def __init__(self, board_ip_start: str = None, udp_port: int = None,
                 local_bind_ip: str = None, enable_logging: bool = True):
        """
        初始化UDP发送器

        Args:
            board_ip_start: 电驱板起始IP，默认192.168.1.1
            udp_port: UDP端口，默认5001
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
        # 【关键修复】禁用接收缓冲区，防止电驱板回复数据导致崩溃
        # 我们只需要发送数据，不需要接收回复
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
        # 【修复】设置socket超时，避免阻塞
        self.sock.settimeout(0.1)  # 100ms超时

        # 【关键】绑定到指定网口，确保从该网口发送数据
        try:
            self.sock.bind((self.local_bind_ip, 0))  # 端口0表示系统自动分配
            if self.enable_logging and self.logger:
                self.logger.info(f'已绑定到本地网口: {self.local_bind_ip}')
                self.logger.info(f'已禁用接收缓冲区（只发送模式）')
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f'绑定到网口 {self.local_bind_ip} 失败: {e}')

        # 序列号
        self.sequence_number = 0

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

        # 记录每个风扇的当前PWM值（用于记录变化）
        # key: f"{ip}_{fan_id}", value: pwm_value
        self.fan_pwm_states = {}
        self.pwm_lock = threading_module.Lock()

        # 风扇ID映射表：逻辑风扇ID -> 物理风扇ID
        self.fan_id_mapping = {
            0: 13,   # 0号风扇 -> 13号风扇
            1: 9,    # 1号风扇 -> 9号风扇
            2: 5,    # 2号风扇 -> 5号风扇
            3: 1,    # 3号风扇 -> 1号风扇
            4: 14,   # 4号风扇 -> 14号风扇
            5: 10,   # 5号风扇 -> 10号风扇
            6: 6,    # 6号风扇 -> 6号风扇
            7: 2,    # 7号风扇 -> 2号风扇
            8: 15,   # 8号风扇 -> 15号风扇
            9: 11,   # 9号风扇 -> 11号风扇
            10: 7,   # 10号风扇 -> 7号风扇
            11: 3,   # 11号风扇 -> 3号风扇
            12: 16,  # 12号风扇 -> 16号风扇
            13: 12,  # 13号风扇 -> 12号风扇
            14: 8,   # 14号风扇 -> 8号风扇
            15: 4,   # 15号风扇 -> 4号风扇
        }

        # 反向映射表：物理风扇ID -> 逻辑风扇ID（用于批量数据包）
        self.physical_to_logical_fan = {v: k for k, v in self.fan_id_mapping.items()}

        # CSV文件锁和写入器
        self.csv_lock = threading_module.Lock()
        self.csv_writer = None
        self.csv_file = None
        self._init_csv_file()

        # 【新增】播放模式标志 - 播放时跳过磁盘日志，大幅提升发送速度
        self.playback_mode = False

        # 原始数据TXT文件路径
        self.raw_data_file = None
        self._init_raw_data_file()

        # 打印初始化信息
        if self.enable_logging and self.logger:
            self.logger.info('=' * 60)
            self.logger.info('FanUDPSender 初始化完成 (新协议: 5字节包)')
            self.logger.info(f'本地绑定网口: {self.local_bind_ip}')
            self.logger.info(f'电驱板起始IP: {self.board_ip_start}')
            self.logger.info(f'UDP端口: {self.udp_port}')
            self.logger.info(f'IP范围: 192.168.1.1-100 (板ID 0-99)')
            self.logger.info('=' * 60)

    def _get_board_ip(self, board_id: int) -> str:
        """
        根据电驱板ID获取IP地址

        Args:
            board_id: 电驱板ID (0-99)

        Returns:
            str: IP地址
        """
        # ID0 -> 192.168.1.1, ID99 -> 192.168.1.100
        ip_parts = self.board_ip_start.split('.')
        last_octet = int(ip_parts[3]) + board_id
        return f"192.168.1.{last_octet}"

    def _init_csv_file(self):
        """初始化CSV文件，写入表头"""
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            csv_file = os.path.join(self.data_dir, f'fan_data_{date_str}.csv')

            # 如果文件不存在，创建并写入表头
            if not os.path.exists(csv_file):
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        '时间',
                        'IP地址',
                        '风扇ID',
                        '链路ID',
                        '板ID',
                        '原PWM值',
                        '新PWM值',
                        '变化值'
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

            # 如果文件不存在，创建并写入表头
            if not os.path.exists(raw_data_file):
                with open(raw_data_file, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"风机通讯原始数据记录 - {date_str}\n")
                    f.write("=" * 80 + "\n\n")

            self.raw_data_file = raw_data_file

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"初始化原始数据文件失败: {e}")

    def _log_raw_data(self, ip: str, port: int, packet: bytes, packet_type: str):
        """
        记录发送给板子的原始数据包到TXT文件

        Args:
            ip: 目标IP地址
            port: 目标端口
            packet: 发送的数据包
            packet_type: 数据包类型（single/bulk）
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            # 检查是否需要切换到新日期的文件
            date_str = datetime.now().strftime('%Y%m%d')
            expected_file = os.path.join(self.data_dir, f'raw_data_{date_str}.txt')

            if self.raw_data_file != expected_file:
                self._init_raw_data_file()
                expected_file = self.raw_data_file

            # 格式化数据包内容
            hex_str = ' '.join(f'{b:02X}' for b in packet)
            packet_length = len(packet)

            # 构建记录内容
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

            # 解析数据包内容
            if packet_type == 'single' and packet_length == 5:
                log_entry += f"  链路ID: {packet[0]} (0x{packet[0]:02X})\n"
                log_entry += f"  板ID:   {packet[1]} (0x{packet[1]:02X})\n"
                log_entry += f"  风扇ID: {packet[2]} (0x{packet[2]:02X}) - 物理风扇编号\n"
                pwm_low = packet[3]
                pwm_high = packet[4]
                pwm_value = pwm_low | (pwm_high << 8)
                log_entry += f"  PWM低字节: {pwm_low} (0x{pwm_low:02X})\n"
                log_entry += f"  PWM高字节: {pwm_high} (0x{pwm_high:02X})\n"
                log_entry += f"  PWM值:     {pwm_value}\n"
            elif packet_type == 'bulk' and packet_length == 80:
                log_entry += f"  80字节批量包（16个风扇 × 5字节）\n\n"
                for i in range(16):
                    offset = i * 5
                    fan_id = packet[offset + 2]
                    pwm_low = packet[offset + 3]
                    pwm_high = packet[offset + 4]
                    pwm_value = pwm_low | (pwm_high << 8)
                    log_entry += f"  风扇{fan_id:2d}: PWM={pwm_value:3d} | "
                    log_entry += f" bytes: {packet[offset]:02X} {packet[offset+1]:02X} {packet[offset+2]:02X} {packet[offset+3]:02X} {packet[offset+4]:02X}\n"

            log_entry += "\n"

            # 追加写入文件
            with self.csv_lock:
                with open(expected_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"记录原始数据失败: {e}")

    def _log_fan_data(self, ip: str, fan_id: int, chain_id: int, board_id: int, new_pwm: int):
        """
        记录风机通讯数据到CSV文件

        Args:
            ip: IP地址
            fan_id: 风扇ID (0-15，逻辑ID)
            chain_id: 链路ID (0-9)
            board_id: 板ID (0-9)
            new_pwm: 新的PWM值
        """
        try:
            # 应用风扇ID映射：逻辑ID -> 物理ID
            physical_fan_id = self.fan_id_mapping.get(fan_id, fan_id)
            fan_key = f"{ip}_{physical_fan_id}"

            with self.pwm_lock:
                old_pwm = self.fan_pwm_states.get(fan_key, 0)
                self.fan_pwm_states[fan_key] = new_pwm

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            pwm_change = new_pwm - old_pwm

            with self.csv_lock:
                # 检查是否需要切换到新日期的文件
                date_str = datetime.now().strftime('%Y%m%d')
                expected_file = os.path.join(self.data_dir, f'fan_data_{date_str}.csv')

                if self.csv_file != expected_file:
                    self._init_csv_file()
                    expected_file = self.csv_file

                # 追加写入CSV（使用映射后的物理风扇ID）
                with open(expected_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        ip,
                        physical_fan_id,  # 使用映射后的物理风扇ID
                        chain_id,
                        board_id,
                        old_pwm,
                        new_pwm,
                        pwm_change
                    ])

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.warning(f"记录风机数据失败: {e}")

    def _build_control_packet(self, chain_id: int, board_id: int, fan_id: int, pwm_value: int) -> bytes:
        """
        构建控制数据包（5字节协议）

        注意：chain_id和board_id都固定为0x00，因为IP地址已经标识了是哪个板

        Args:
            chain_id: 链路ID (0-9) - 固定为0x00
            board_id: 电驱板ID (0-9) - 固定为0x00
            fan_id: 逻辑风扇ID (0-15)
            pwm_value: PWM值 (0-999)

        Returns:
            bytes: 5字节的控制数据包
        """
        # 应用风扇ID映射：逻辑ID -> 物理ID
        physical_fan_id = self.fan_id_mapping.get(fan_id, fan_id)

        # 限制PWM值范围
        pwm_value = max(0, min(PROTOCOL_CONFIG['pwm_max'], pwm_value))

        # 构建5字节数据包（前两个字节固定为0x00）
        packet = struct.pack(
            '<BBBBB',  # 5个1字节: little-endian
            0x00,                    # 1字节: 链路ID（固定0）
            0x00,                    # 1字节: 板ID（固定0）
            physical_fan_id & 0xFF,  # 1字节: 风扇ID（使用映射后的物理ID）
            pwm_value & 0xFF,        # 1字节: PWM低字节
            (pwm_value >> 8) & 0xFF  # 1字节: PWM高字节
        )

        return packet

    def _build_bulk_packet(self, chain_id: int, board_id: int, pwm_values: list) -> bytes:
        """
        构建80字节批量控制数据包（16个风扇 × 5字节）

        注意：chain_id和board_id都固定为0x00，因为IP地址已经标识了是哪个板

        Args:
            chain_id: 链路ID (0-9) - 固定为0x00
            board_id: 电驱板ID (0-9) - 固定为0x00
            pwm_values: 16个PWM值的列表 (0-999)

        Returns:
            bytes: 80字节的批量控制数据包
        """
        if len(pwm_values) != 16:
            if self.enable_logging and self.logger:
                self.logger.error(f"批量数据包需要16个PWM值，收到{len(pwm_values)}个")
            return b''

        # 构建80字节数据包（16个风扇，每个5字节）
        # 注意：物理风扇ID范围是1-16，不是0-15
        packet_parts = []
        for physical_fan_id in range(1, 17):  # 1-16，不是0-15
            # 找到对应的逻辑风扇ID
            logical_fan_id = self.physical_to_logical_fan.get(physical_fan_id, physical_fan_id - 1)
            # 从逻辑PWM值列表中取出对应的PWM值
            pwm_value = max(0, min(PROTOCOL_CONFIG['pwm_max'], pwm_values[logical_fan_id]))
            packet_parts.append(struct.pack(
                '<BBBBB',  # 5个1字节
                0x00,                    # 链路ID（固定0）
                0x00,                    # 板ID（固定0）
                physical_fan_id & 0xFF,  # 物理风扇ID（1-16）
                pwm_value & 0xFF,        # PWM低字节
                (pwm_value >> 8) & 0xFF  # PWM高字节
            ))

        return b''.join(packet_parts)

    def send_to_board(self, chain_id: int, board_id: int, fan_id: int, pwm_value: int) -> bool:
        """
        发送控制数据到单个风扇

        Args:
            chain_id: 链路ID (0-9)
            board_id: 电驱板ID (0-9)
            fan_id: 风扇ID (0-15)
            pwm_value: PWM值 (0-999)

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
            # 构建数据包
            packet = self._build_control_packet(chain_id, board_id, fan_id, pwm_value)

            # 获取目标IP
            # 计算全局板ID: chain_id * 10 + board_id
            global_board_id = chain_id * 10 + board_id
            target_ip = self._get_board_ip(global_board_id)
            target_addr = (target_ip, self.udp_port)

            # 发送数据
            self.sock.sendto(packet, target_addr)

            # 更新统计
            self.stats['total_packets'] += 1
            self.stats['success_packets'] += 1
            self.stats['last_send_time'] = datetime.now()

            # 记录风机通讯数据（CSV格式）
            self._log_fan_data(target_ip, fan_id, chain_id, board_id, pwm_value)

            # 记录原始数据包（TXT格式）
            self._log_raw_data(target_ip, self.udp_port, packet, 'single')

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
        将40x40的网格数据发送到所有电驱板

        网格布局:
        - 40x40网格分为10x10个模块
        - 每个模块4x4，对应一个电驱板的16个风扇
        - 10个链路，每个链路10个板（共100个板）

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

        # 遍历所有链路和板
        for chain_id in range(10):
            for board_in_chain in range(10):
                # 计算全局板ID
                global_board_id = chain_id * 10 + board_in_chain

                # 提取模块的4x4风扇数据
                row_start = global_board_id // 10 * 4
                row_end = row_start + 4
                col_start = (global_board_id % 10) * 4
                col_end = col_start + 4

                module_data = grid_data[row_start:row_end, col_start:col_end]

                # 发送16个风扇的数据
                # 注意：fan_id 在这里既是 module_data 的索引，也是逻辑风扇ID
                for logical_fan_id in range(16):
                    row = logical_fan_id // 4
                    col = logical_fan_id % 4
                    percent = module_data[row, col]
                    pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])

                    success = self.send_to_board(chain_id, board_in_chain, logical_fan_id, pwm_value)

                    # 记录结果：使用 chain_id*10+board_in_chain 作为key
                    results[global_board_id * 16 + fan_id] = success

                    if success:
                        success_count += 1
                    else:
                        fail_count += 1

        # 批量发送完成
        elapsed_time = time.time() - start_time
        if self.enable_logging and self.logger:
            self.logger.info(f"发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms")

        # 批量回调
        if callback:
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_to_selected_boards(self, grid_data: np.ndarray,
                                 selected_cells: set,
                                 callback=None) -> Dict[int, bool]:
        """
        只发送选中的风扇对应的电驱板（发送整个模块的80字节包）

        注意：即使只选中1个风扇，也会发送该风扇所在模块的全部16个风扇的数据

        Args:
            grid_data: 40x40的numpy数组
            selected_cells: 选中的单元格集合
            callback: 发送完成回调函数 (success_count, fail_count, elapsed_time)

        Returns:
            Dict[int, bool]: 每个模块的发送结果
        """
        results = {}
        success_count = 0
        fail_count = 0
        start_time = time.time()

        # 找出所有受影响的模块（去重）
        affected_boards = set()
        for cell in selected_cells:
            global_board_id = cell.row // 4 * 10 + cell.col // 4
            affected_boards.add(global_board_id)

        # 对每个受影响的模块，发送80字节批量包
        for global_board_id in affected_boards:
            chain_id = global_board_id // 10
            board_in_chain = global_board_id % 10

            # 提取模块的4x4风扇数据
            row_start = global_board_id // 10 * 4
            row_end = row_start + 4
            col_start = (global_board_id % 10) * 4
            col_end = col_start + 4

            module_data = grid_data[row_start:row_end, col_start:col_end]

            # 构建16个风扇的PWM值列表（按逻辑风扇ID顺序）
            # pwm_values[i] = 逻辑风扇i的PWM值
            pwm_values = []
            for logical_fan_id in range(16):
                row = logical_fan_id // 4
                col = logical_fan_id % 4
                percent = module_data[row, col]
                pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                pwm_values.append(pwm_value)

            # 构建80字节数据包（会自动将逻辑PWM值映射到物理风扇位置）
            packet = self._build_bulk_packet(chain_id, board_in_chain, pwm_values)

            # 检查数据包是否有效
            if not packet or len(packet) != 80:
                if self.enable_logging and self.logger:
                    self.logger.error(f"数据包构建失败: 板ID={global_board_id}, 长度={len(packet) if packet else 0}")
                results[global_board_id] = False
                fail_count += 1
                continue

            # 发送到对应IP
            try:
                target_ip = self._get_board_ip(global_board_id)
                target_addr = (target_ip, self.udp_port)
                self.sock.sendto(packet, target_addr)

                self.stats['total_packets'] += 1
                self.stats['success_packets'] += 1
                self.stats['last_send_time'] = datetime.now()

                results[global_board_id] = True
                success_count += 1

                # 记录每个风扇的数据（CSV格式）
                for fan_id in range(16):
                    self._log_fan_data(target_ip, fan_id, chain_id, board_in_chain, pwm_values[fan_id])

                # 记录原始数据包（TXT格式）
                self._log_raw_data(target_ip, self.udp_port, packet, 'bulk')

            except Exception as e:
                self.stats['total_packets'] += 1
                self.stats['failed_packets'] += 1
                results[global_board_id] = False
                fail_count += 1
                if self.enable_logging and self.logger:
                    self.logger.error(f"发送失败: IP={target_ip} Error={e}")

        # 批量回调
        if callback:
            elapsed_time = time.time() - start_time
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_grid_to_boards_bulk(self, grid_data: np.ndarray, callback=None) -> Dict[int, bool]:
        """
        使用80字节批量包将40x40的网格数据发送到所有电驱板

        播放模式下跳过所有磁盘日志记录，实现高速发送。
        正常模式下保留完整的CSV和TXT日志记录。

        Args:
            grid_data: 40x40的numpy数组，值为0-100的百分比
            callback: 发送完成回调函数 (success_count, fail_count, elapsed_time)

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
                self.logger.info(f"开始发送100个控制板数据（80字节批量包） (范围: {grid_data.min():.1f}%-{grid_data.max():.1f}%)")
                self.logger.info(f"调试: 板ID 0 的80字节数据包预览:")
                first_board_pwm = []
                for fan_id in range(16):
                    row = fan_id // 4
                    col = fan_id % 4
                    percent = grid_data[row, col]
                    pwm = int((percent / 100.0) * 999)
                    first_board_pwm.append(pwm)
                self.logger.info(f"  PWM值: {first_board_pwm}")

            results = {}
            success_count = 0
            fail_count = 0
            start_time = time.time()

            # 【优化】预计算所有板的PWM值（避免在循环中重复计算）
            # 40x40网格分为10x10个4x4模块，共100个板
            all_pwm_values = []
            for global_board_id in range(100):
                row_start = global_board_id // 10 * 4
                col_start = (global_board_id % 10) * 4
                module_data = grid_data[row_start:row_start + 4, col_start:col_start + 4]

                pwm_values = []
                for logical_fan_id in range(16):
                    row = logical_fan_id // 4
                    col = logical_fan_id % 4
                    percent = module_data[row, col]
                    pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                    pwm_values.append(pwm_value)
                all_pwm_values.append(pwm_values)

            # 遍历所有板发送数据
            for global_board_id in range(100):
                chain_id = global_board_id // 10
                board_in_chain = global_board_id % 10
                pwm_values = all_pwm_values[global_board_id]

                # 构建80字节数据包
                packet = self._build_bulk_packet(chain_id, board_in_chain, pwm_values)

                if not packet or len(packet) != 80:
                    results[global_board_id] = False
                    fail_count += 1
                    continue

                try:
                    target_ip = self._get_board_ip(global_board_id)
                    target_addr = (target_ip, self.udp_port)
                    self.sock.sendto(packet, target_addr)

                    self.stats['total_packets'] += 1
                    self.stats['success_packets'] += 1
                    self.stats['last_send_time'] = datetime.now()

                    results[global_board_id] = True
                    success_count += 1

                    # 【关键优化】播放模式下跳过所有磁盘日志记录
                    if not is_playback:
                        for fan_id in range(16):
                            self._log_fan_data(target_ip, fan_id, chain_id, board_in_chain, pwm_values[fan_id])
                        self._log_raw_data(target_ip, self.udp_port, packet, 'bulk')

                except Exception as e:
                    self.stats['total_packets'] += 1
                    self.stats['failed_packets'] += 1
                    results[global_board_id] = False
                    fail_count += 1
                    if self.enable_logging and self.logger:
                        self.logger.error(f"发送失败: IP={target_ip} Error={e}")

            # 批量发送完成
            elapsed_time = time.time() - start_time
            if self.enable_logging and self.logger and not is_playback:
                self.logger.info(f"发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms")

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
        self.send_interval = 0.01  # 发送间隔(秒)

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
                    # 捕获处理任务时的异常，防止后台线程崩溃
                    if self.enable_logging and self.logger:
                        self.logger.error(f"后台任务处理异常: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                time.sleep(self.send_interval)

    def _process_task(self, task):
        """处理发送任务（添加异常处理）"""
        try:
            task_type = task.get('type')

            if task_type == 'single':
                # 单个风扇控制
                chain_id = task.get('chain_id', 0)
                board_id = task.get('board_id', 0)
                fan_id = task.get('fan_id', 0)
                pwm_value = task.get('pwm_value', 0)
                self.send_to_board(chain_id, board_id, fan_id, pwm_value)

            elif task_type == 'grid':
                grid_data = task['grid_data']
                callback = task.get('callback')
                # 【修改】统一使用80字节批量包模式
                self.send_grid_to_boards_bulk(grid_data, callback)

            elif task_type == 'bulk':
                # 【新增】80字节批量发送（异步线程中不传callback，避免跨线程调用）
                grid_data = task['grid_data']
                # 在异步线程中不调用callback，避免跨线程UI更新问题
                self.send_grid_to_boards_bulk(grid_data, callback=None)

            elif task_type == 'selected':
                grid_data = task['grid_data']
                selected_cells = task['selected_cells']
                callback = task.get('callback')
                self.send_to_selected_boards(grid_data, selected_cells, callback)

        except Exception as e:
            # 捕获处理任务时的异常，防止后台线程崩溃
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
        """将全网格批量发送任务（80字节包）加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'bulk',
                'grid_data': grid_data.copy(),
                'callback': callback
            })


# 便捷函数
def create_udp_sender(enable_logging: bool = True,
                      async_mode: bool = False) -> FanUDPSender:
    """
    创建UDP发送器

    Args:
        enable_logging: 是否启用日志
        async_mode: 是否使用异步模式

    Returns:
        FanUDPSender: UDP发送器实例
    """
    if async_mode:
        return AsyncFanUDPSender(enable_logging=enable_logging)
    else:
        return FanUDPSender(enable_logging=enable_logging)
