# -*- coding: utf-8 -*-
"""
UDP风扇控制模块

根据协议文档，将40x40的风扇网格数据发送到100个独立的电驱板
每个电驱板有16个风机，使用UDP单播通信
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

# 协议配置
PROTOCOL_CONFIG = {
    'magic_fc': b'FC',  # Fan Control
    'magic_fr': b'FR',  # Fan Response
    'controller_ip': '192.168.1.10',
    'board_ip_start': '192.168.1.101',  # ID0 -> 101
    'board_ip_end': '192.168.1.200',    # ID99 -> 200
    'udp_port': 5001,
    'fans_per_board': 16,
    'pwm_max': 999,
    'control_packet_size': 100,  # 16 + 80 + 4
}


def setup_udp_logger(log_dir: str = None) -> logging.Logger:
    """
    设置UDP发送日志记录器

    Args:
        log_dir: 日志目录路径

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger('FanUDP')
    logger.setLevel(logging.INFO)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 默认日志文件路径
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'udp_send_{timestamp}.log')

    # 文件handler - 详细日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # 控制台handler - 重要信息
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # 添加handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 记录日志文件位置
    logger.info('=' * 80)
    logger.info(f'UDP发送日志文件: {log_file}')
    logger.info('=' * 80)

    return logger


# 全局日志记录器
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
    """

    def __init__(self, board_ip_start: str = None, udp_port: int = None,
                 enable_logging: bool = True):
        """
        初始化UDP发送器

        Args:
            board_ip_start: 电驱板起始IP，默认192.168.1.101
            udp_port: UDP端口，默认5001
            enable_logging: 是否启用日志
        """
        self.board_ip_start = board_ip_start or PROTOCOL_CONFIG['board_ip_start']
        self.udp_port = udp_port or PROTOCOL_CONFIG['udp_port']
        self.enable_logging = enable_logging

        # 创建UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        # 【修复】设置socket超时，避免阻塞
        self.sock.settimeout(0.1)  # 100ms超时

        # 序列号
        self.sequence_number = 0

        # 统计信息
        self.stats = {
            'total_packets': 0,
            'success_packets': 0,
            'failed_packets': 0,
            'last_send_time': None,
        }

        # 日志配置 - 使用新的日志记录器
        if self.enable_logging:
            self.logger = get_udp_logger()
            self.logger.info('FanUDPSender 初始化完成')
            self.logger.info(f'电驱板起始IP: {self.board_ip_start}')
            self.logger.info(f'UDP端口: {self.udp_port}')
        else:
            self.logger = None

    def _get_board_ip(self, board_id: int) -> str:
        """
        根据电驱板ID获取IP地址

        Args:
            board_id: 电驱板ID (0-99)

        Returns:
            str: IP地址
        """
        # ID0 -> 192.168.1.101, ID99 -> 192.168.1.200
        ip_parts = self.board_ip_start.split('.')
        last_octet = int(ip_parts[3]) + board_id
        return f"192.168.1.{last_octet}"

    def _calculate_crc32(self, data: bytes) -> int:
        """
        计算CRC32校验码

        Args:
            data: 需要校验的数据

        Returns:
            int: CRC32校验码
        """
        return zlib.crc32(data) & 0xFFFFFFFF

    def _build_control_packet(self, board_id: int, fan_pwm_values: List[int]) -> bytes:
        """
        构建控制数据包

        协议格式 (100字节):
        - 协议头 (16字节):
          - magic (2): "FC"
          - board_id (1): 电驱板ID
          - sequence_number (2): 序列号
          - timestamp (4): 时间戳(毫秒)
          - control_flags (2): 控制标志
          - reserved (5): 保留
        - 控制数据 (80字节):
          - 16个风扇，每个5字节:
            - fan_id (1): 风扇ID (0-15)
            - pwm_level (2): PWM值 (0-999)
            - fan_flags (2): 风扇标志
        - 校验和 (4字节): CRC32

        Args:
            board_id: 电驱板ID (0-99)
            fan_pwm_values: 16个风扇的PWM值列表 (0-999)

        Returns:
            bytes: 完整的控制数据包
        """
        import zlib

        # 协议头 (16字节) - 使用简单分步构建
        # magic(2) + board_id(1) + sequence_number(2) + timestamp(4) + control_flags(2) + reserved(5) = 16
        header_parts = []
        header_parts.append(struct.pack('<2s', PROTOCOL_CONFIG['magic_fc']))  # 2 bytes
        header_parts.append(struct.pack('<B', board_id))  # 1 byte
        header_parts.append(struct.pack('<H', self.sequence_number))  # 2 bytes
        # 时间戳取模32位无符号整数最大值，防止溢出
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF
        header_parts.append(struct.pack('<I', timestamp))  # 4 bytes
        header_parts.append(struct.pack('<H', 0))  # 2 bytes: control_flags
        header_parts.append(b'\x00' * 5)  # 5 bytes: reserved
        header = b''.join(header_parts)  # 总共 16 字节

        # 控制数据 (80字节) - 16个风扇，每个5字节
        control_data = b''
        for fan_id, pwm_value in enumerate(fan_pwm_values):
            # 限制PWM值范围
            pwm_value = max(0, min(PROTOCOL_CONFIG['pwm_max'], pwm_value))
            fan_flags = 0x0001  # bit0 = 启动
            control_data += struct.pack(
                '<BHH',  # fan_id(1) + pwm_level(2) + fan_flags(2) = 5 bytes
                fan_id,
                pwm_value,
                fan_flags
            )

        # 校验和 (4字节) - CRC32 of header + control_data
        crc_data = header + control_data
        crc32 = zlib.crc32(crc_data) & 0xFFFFFFFF

        # 完整数据包
        packet = header + control_data + struct.pack('<I', crc32)

        return packet

    def send_to_board(self, board_id: int, fan_pwm_values: List[int]) -> bool:
        """
        发送控制数据到单个电驱板

        Args:
            board_id: 电驱板ID (0-99)
            fan_pwm_values: 16个风扇的PWM值列表 (0-999)

        Returns:
            bool: 发送成功返回True
        """
        if board_id < 0 or board_id >= 100:
            if self.enable_logging and self.logger:
                self.logger.error(f"无效的电驱板ID: {board_id}")
            return False

        if len(fan_pwm_values) != 16:
            if self.enable_logging and self.logger:
                self.logger.error(f"风扇PWM值数量错误: {len(fan_pwm_values)}, 需要16个")
            return False

        try:
            # 构建数据包
            packet = self._build_control_packet(board_id, fan_pwm_values)

            # 获取目标IP
            target_ip = self._get_board_ip(board_id)
            target_addr = (target_ip, self.udp_port)

            # 发送数据
            send_time = time.time()
            self.sock.sendto(packet, target_addr)

            # 更新统计
            self.stats['total_packets'] += 1
            self.stats['success_packets'] += 1
            self.stats['last_send_time'] = datetime.now()
            seq = self.sequence_number
            self.sequence_number = (self.sequence_number + 1) % 65536

            # 【修复】减少日志输出，只记录关键信息
            # 不再每个板都输出日志，避免日志过多导致性能问题

            return True

        except Exception as e:
            self.stats['total_packets'] += 1
            self.stats['failed_packets'] += 1
            if self.enable_logging and self.logger:
                self.logger.error('-' * 60)
                self.logger.error(f"发送到电驱板 #{board_id} 失败")
                self.logger.error(f"  错误类型: {type(e).__name__}")
                self.logger.error(f"  错误信息: {e}")
            return False

    def send_grid_to_boards(self, grid_data: np.ndarray,
                            callback=None) -> Dict[int, bool]:
        """
        将40x40的网格数据发送到所有电驱板

        网格布局映射:
        - 40x40网格分为10x10个模块
        - 每个模块4x4，对应一个电驱板的16个风扇
        - 电驱板ID: 从左到右、从下到上（根据用户描述）
          - 下排（第0行模块）: 0, 1, 2, ..., 9
          - 上排（第9行模块）: 90, 91, 92, ..., 99

        Args:
            grid_data: 40x40的numpy数组，值为0-100的百分比
            callback: 发送完成回调函数 callback(board_id, success)

        Returns:
            Dict[int, bool]: 每个电驱板的发送结果
        """
        results = {}

        if grid_data.shape != (40, 40):
            if self.enable_logging and self.logger:
                self.logger.error(f"网格数据形状错误: {grid_data.shape}, 需要(40, 40)")
            return results

        # 【修复】简化日志输出
        if self.enable_logging and self.logger:
            self.logger.info(f"开始发送100个控制板数据 (范围: {grid_data.min():.0f}%-{grid_data.max():.0f}%)")

        success_count = 0
        fail_count = 0
        start_time = time.time()

        # 遍历10x10个模块
        for module_row in range(10):
            for module_col in range(10):
                # 计算电驱板ID
                # 根据用户描述：下角是1号机，横排从左到右
                # 假设"下角"指的是底部，从左到右编号
                # 那么底部（最后一行模块）是0-9，向上递增
                board_id = module_row * 10 + module_col

                # 提取模块的4x4风扇数据
                row_start = module_row * 4
                row_end = row_start + 4
                col_start = module_col * 4
                col_end = col_start + 4

                module_data = grid_data[row_start:row_end, col_start:col_end]

                # 转换为PWM值列表 (0-999)
                fan_pwm_values = []
                for r in range(4):
                    for c in range(4):
                        percent = module_data[r, c]
                        pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                        fan_pwm_values.append(pwm_value)

                # 发送到电驱板
                success = self.send_to_board(board_id, fan_pwm_values)
                results[board_id] = success

                if success:
                    success_count += 1
                else:
                    fail_count += 1

                # 【修复】不再每个板都调用回调，避免在发送循环中调用UI操作
                # if callback:
                #     callback(board_id, success)

        # 批量发送完成日志
        elapsed_time = time.time() - start_time
        if self.enable_logging and self.logger:
            self.logger.info(f"发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms")

        # 【修复】只在发送完成后调用一次回调，传递汇总结果
        if callback:
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_grid_to_boards_custom(self, grid_data: np.ndarray,
                                    board_mapping: callable = None,
                                    callback=None) -> Dict[int, bool]:
        """
        使用自定义映射将网格数据发送到电驱板

        Args:
            grid_data: 40x40的numpy数组
            board_mapping: 自定义映射函数，接收(module_row, module_col)，返回board_id
            callback: 发送完成回调函数

        Returns:
            Dict[int, bool]: 每个电驱板的发送结果
        """
        results = {}

        if grid_data.shape != (40, 40):
            if self.enable_logging:
                self.logger.error(f"网格数据形状错误: {grid_data.shape}")
            return results

        # 使用默认映射或自定义映射
        if board_mapping is None:
            board_mapping = lambda mr, mc: mr * 10 + mc

        start_time = time.time()
        success_count = 0
        fail_count = 0

        for module_row in range(10):
            for module_col in range(10):
                board_id = board_mapping(module_row, module_col)

                # 提取模块数据
                row_start = module_row * 4
                row_end = row_start + 4
                col_start = module_col * 4
                col_end = col_start + 4

                module_data = grid_data[row_start:row_end, col_start:col_end]

                # 转换为PWM值
                fan_pwm_values = []
                for r in range(4):
                    for c in range(4):
                        percent = module_data[r, c]
                        pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                        fan_pwm_values.append(pwm_value)

                # 发送
                success = self.send_to_board(board_id, fan_pwm_values)
                results[board_id] = success

                if success:
                    success_count += 1
                else:
                    fail_count += 1

                # 【修复】不再每个板都调用回调

        # 【修复】批量回调
        if callback:
            elapsed_time = time.time() - start_time
            callback(success_count, fail_count, elapsed_time)

        return results

    def send_to_selected_boards(self, grid_data: np.ndarray,
                                 selected_cells: set,
                                 callback=None) -> Dict[int, bool]:
        """
        只发送选中的风扇对应的电驱板

        Args:
            grid_data: 40x40的numpy数组
            selected_cells: 选中的单元格集合
            callback: 发送完成回调函数 (success_count, fail_count, elapsed_time)

        Returns:
            Dict[int, bool]: 每个电驱板的发送结果
        """
        results = {}

        # 找出受影响的模块（电驱板）
        affected_boards = {}  # {board_id: {cell_positions}}

        for cell in selected_cells:
            module_row = cell.row // 4
            module_col = cell.col // 4
            board_id = module_row * 10 + module_col

            if board_id not in affected_boards:
                affected_boards[board_id] = {
                    'module_row': module_row,
                    'module_col': module_col,
                    'cells': []
                }
            affected_boards[board_id]['cells'].append(cell)

        start_time = time.time()
        success_count = 0
        fail_count = 0

        # 对每个受影响的电驱板发送数据
        for board_id, info in affected_boards.items():
            mr, mc = info['module_row'], info['module_col']

            # 提取模块数据
            row_start = mr * 4
            row_end = row_start + 4
            col_start = mc * 4
            col_end = col_start + 4

            module_data = grid_data[row_start:row_end, col_start:col_end]

            # 转换为PWM值
            fan_pwm_values = []
            for r in range(4):
                for c in range(4):
                    percent = module_data[r, c]
                    pwm_value = int((percent / 100.0) * PROTOCOL_CONFIG['pwm_max'])
                    fan_pwm_values.append(pwm_value)

            # 发送
            success = self.send_to_board(board_id, fan_pwm_values)
            results[board_id] = success

            if success:
                success_count += 1
            else:
                fail_count += 1

            # 【修复】不再每个板都调用回调

        # 【修复】批量回调
        if callback:
            elapsed_time = time.time() - start_time
            callback(success_count, fail_count, elapsed_time)

        return results

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        # 同时记录到日志文件
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

        # 控制台输出
        print("\n" + "=" * 60)
        print("UDP风扇发送统计")
        print("=" * 60)
        print(f"总数据包: {stats['total_packets']}")
        print(f"成功: {stats['success_packets']}")
        print(f"失败: {stats['failed_packets']}")

        if stats['total_packets'] > 0:
            success_rate = (stats['success_packets'] / stats['total_packets']) * 100
            print(f"成功率: {success_rate:.1f}%")

        if stats['last_send_time']:
            print(f"最后发送: {stats['last_send_time']}")

        print("=" * 60 + "\n")

    def close(self):
        """关闭socket"""
        if self.sock:
            self.sock.close()
            # 【修复】添加异常处理，避免程序退出时的日志错误
            try:
                if self.enable_logging and self.logger:
                    self.logger.info('=' * 60)
                    self.logger.info("UDP发送器关闭")
                    self.print_statistics()
                    self.logger.info('=' * 60)
            except Exception:
                # 程序退出时忽略日志错误
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
                self._process_task(task)
            else:
                time.sleep(self.send_interval)

    def _process_task(self, task):
        """处理发送任务"""
        task_type = task.get('type')

        if task_type == 'board':
            self.send_to_board(task['board_id'], task['fan_pwm_values'])

        elif task_type == 'grid':
            grid_data = task['grid_data']
            callback = task.get('callback')
            self.send_grid_to_boards(grid_data, callback)

        elif task_type == 'selected':
            grid_data = task['grid_data']
            selected_cells = task['selected_cells']
            callback = task.get('callback')
            self.send_to_selected_boards(grid_data, selected_cells, callback)

    def queue_send_to_board(self, board_id: int, fan_pwm_values: List[int]):
        """将单板发送任务加入队列"""
        with self.queue_lock:
            self.send_queue.append({
                'type': 'board',
                'board_id': board_id,
                'fan_pwm_values': fan_pwm_values
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


# 导入zlib（如果未导入）
import zlib


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
        sender = AsyncFanUDPSender(enable_logging=enable_logging)
        sender.start()
        return sender
    else:
        return FanUDPSender(enable_logging=enable_logging)


# 测试代码
if __name__ == '__main__':
    # 测试发送
    sender = create_udp_sender(enable_logging=True)

    # 创建测试网格数据
    test_grid = np.zeros((40, 40), dtype=float)

    # 设置一些测试值
    test_grid[0:4, 0:4] = 50.0   # 板0: 50%
    test_grid[4:8, 0:4] = 75.0   # 板1: 75%
    test_grid[36:40, 36:40] = 100.0  # 板99: 100%

    print("开始发送测试数据...")
    results = sender.send_grid_to_boards(test_grid)

    print(f"\n发送完成，共{len(results)}个电驱板")
    sender.print_statistics()
    sender.close()
