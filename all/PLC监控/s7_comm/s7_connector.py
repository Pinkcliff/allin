# -*- coding: utf-8 -*-
"""
西门子 S7 PLC 连接器
提供基础的 S7 协议通信功能
"""
import snap7
from snap7.util import *
import logging
from typing import Optional, Union, List, Dict
from dataclasses import dataclass
from enum import Enum
import sys
import os

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class DataType(Enum):
    """数据类型枚举"""
    INT = "INT"
    DINT = "DINT"
    REAL = "REAL"
    BOOL = "BOOL"
    BYTE = "BYTE"
    WORD = "WORD"
    DWORD = "DWORD"


@dataclass
class DBItem:
    """DB 块数据项定义"""
    name: str
    data_type: DataType
    start_offset: int
    bit_offset: int = 0  # 用于 BOOL 类型

    @property
    def size(self) -> int:
        """获取数据类型大小"""
        size_map = {
            DataType.BOOL: 1,
            DataType.BYTE: 1,
            DataType.WORD: 2,
            DataType.INT: 2,
            DataType.DWORD: 4,
            DataType.DINT: 4,
            DataType.REAL: 4
        }
        return size_map.get(self.data_type, 4)


class S7PLCConnector:
    """西门子 S7 PLC 连接器"""

    def __init__(self, ip_address: str, rack: int = 0, slot: int = 1):
        """
        初始化 PLC 连接器

        Args:
            ip_address: PLC IP 地址
            rack: 机架号，默认 0
            slot: 槽位号，默认 1
        """
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.is_connected = False
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """连接到 PLC"""
        try:
            self.client.connect(self.ip_address, self.rack, self.slot)
            self.is_connected = self.client.get_connected()
            if self.is_connected:
                self.logger.info(f"成功连接到 PLC: {self.ip_address}")
            else:
                self.logger.error(f"连接 PLC 失败: {self.ip_address}")
            return self.is_connected
        except Exception as e:
            self.logger.error(f"连接 PLC 异常: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            try:
                self.client.disconnect()
                self.is_connected = False
                self.logger.info("已断开 PLC 连接")
            except Exception as e:
                self.logger.error(f"断开连接异常: {e}")

    def read_db(self, db_number: int, start_offset: int, size: int) -> Optional[bytes]:
        """
        读取 DB 块数据

        Args:
            db_number: DB 块编号
            start_offset: 起始偏移量（字节）
            size: 读取的字节数

        Returns:
            bytes: 读取的数据，失败返回 None
        """
        if not self.is_connected:
            self.logger.error("未连接到 PLC")
            return None

        try:
            data = self.client.db_read(db_number, start_offset, size)
            self.logger.debug(f"读取 DB{db_number}.DB{start_offset} 成功，大小: {size} 字节")
            return data
        except Exception as e:
            self.logger.error(f"读取 DB{db_number}.DB{start_offset} 失败: {e}")
            return None

    def write_db(self, db_number: int, start_offset: int, data: bytes) -> bool:
        """
        写入 DB 块数据

        Args:
            db_number: DB 块编号
            start_offset: 起始偏移量（字节）
            data: 要写入的数据

        Returns:
            bool: 写入成功返回 True
        """
        if not self.is_connected:
            self.logger.error("未连接到 PLC")
            return False

        try:
            self.client.db_write(db_number, start_offset, data)
            self.logger.info(f"写入 DB{db_number}.DB{start_offset} 成功")
            return True
        except Exception as e:
            self.logger.error(f"写入 DB{db_number}.DB{start_offset} 失败: {e}")
            return False

    def read_item(self, item: DBItem, db_number: int = 5) -> Optional[Union[int, float, bool]]:
        """
        读取单个数据项

        Args:
            item: 数据项定义
            db_number: DB 块编号

        Returns:
            解析后的值
        """
        data = self.read_db(db_number, item.start_offset, item.size)
        if data is None:
            return None

        try:
            if item.data_type == DataType.INT:
                return get_int(data, 0)
            elif item.data_type == DataType.DINT:
                return get_dint(data, 0)
            elif item.data_type == DataType.REAL:
                return get_real(data, 0)
            elif item.data_type == DataType.BOOL:
                return get_bool(data, 0, item.bit_offset)
            elif item.data_type == DataType.BYTE:
                return get_byte(data, 0)
            elif item.data_type == DataType.WORD:
                return get_word(data, 0)
            elif item.data_type == DataType.DWORD:
                return get_dword(data, 0)
            else:
                self.logger.warning(f"不支持的数据类型: {item.data_type}")
                return None
        except Exception as e:
            self.logger.error(f"解析数据失败: {e}")
            return None

    def read_multiple_items(self, items: List[DBItem], db_number: int = 5) -> Dict[str, Union[int, float, bool]]:
        """
        批量读取多个数据项（优化为一次读取整个DB块）

        Args:
            items: 数据项列表
            db_number: DB 块编号

        Returns:
            {item_name: value} 字典
        """
        if not items:
            return {}

        # 计算需要读取的最大偏移量
        max_offset = max(item.start_offset + item.size for item in items)

        # 一次读取整个范围
        raw_data = self.read_db(db_number, 0, max_offset)
        if raw_data is None:
            return {}

        results = {}
        for item in items:
            try:
                if item.data_type == DataType.INT:
                    value = get_int(raw_data, item.start_offset)
                elif item.data_type == DataType.DINT:
                    value = get_dint(raw_data, item.start_offset)
                elif item.data_type == DataType.REAL:
                    value = get_real(raw_data, item.start_offset)
                elif item.data_type == DataType.BOOL:
                    value = get_bool(raw_data, item.start_offset, item.bit_offset)
                elif item.data_type == DataType.BYTE:
                    value = get_byte(raw_data, item.start_offset)
                elif item.data_type == DataType.WORD:
                    value = get_word(raw_data, item.start_offset)
                elif item.data_type == DataType.DWORD:
                    value = get_dword(raw_data, item.start_offset)
                else:
                    value = None

                results[item.name] = value
            except Exception as e:
                self.logger.error(f"解析 {item.name} 失败: {e}")
                results[item.name] = None

        return results

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
