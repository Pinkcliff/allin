# -*- coding: utf-8 -*-
"""
点位表监控模块
用于批量监控PLC点位数据
"""
import sys
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QGroupBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

import pandas as pd

# 添加s7_comm模块路径
sys.path.insert(0, os.path.dirname(__file__))
from s7_comm import S7PLCConnector, DBItem, DataType


@dataclass
class PointInfo:
    """点位信息"""
    name: str
    db_number: int
    byte_offset: int
    bit_offset: int = 0
    data_type: str = "REAL"
    size: int = 4

    @classmethod
    def from_address(cls, name: str, address: str, data_type: str) -> 'PointInfo':
        """从地址字符串解析点位信息"""
        match = re.match(r'DB(\d+)\.(\d+)\.(\d+)', address)
        if not match:
            raise ValueError(f"无效的地址格式: {address}")

        db_num = int(match.group(1))
        byte_off = int(match.group(2))
        bit_off = int(match.group(3))

        if data_type == "REAL":
            size = 4
        elif data_type == "BOOL":
            size = 1
        elif data_type == "INT":
            size = 2
        elif data_type == "DINT":
            size = 4
        else:
            size = 4

        return cls(name=name, db_number=db_num, byte_offset=byte_off,
                  bit_offset=bit_off, data_type=data_type, size=size)


class PLCConnectionThread(QThread):
    """PLC连接线程 - 避免UI卡顿"""

    connection_result = Signal(bool, str)  # (成功, 消息)

    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.connector = None

    def run(self):
        """执行连接操作"""
        try:
            self.connector = S7PLCConnector(self.ip_address)
            if self.connector.connect():
                self.connection_result.emit(True, "PLC连接成功")
            else:
                self.connection_result.emit(False, "PLC连接失败")
        except Exception as e:
            self.connection_result.emit(False, f"连接错误: {str(e)}")

    def get_connector(self):
        """获取连接器"""
        return self.connector


class PLCDataReadThread(QThread):
    """PLC数据读取线程 - 避免UI卡顿"""

    data_read_result = Signal(dict, dict)  # (数据, 统计)
    read_finished = Signal()

    def __init__(self, connector, points, db_groups):
        super().__init__()
        self.connector = connector
        self.points = points
        self.db_groups = db_groups

    def run(self):
        """执行数据读取"""
        success_count = 0
        failed_count = 0
        data_cache = {}

        # 读取数据
        for db_num, points in self.db_groups.items():
            max_offset = max(p.byte_offset + p.size for p in points)

            try:
                from snap7.util import get_real, get_bool, get_int, get_dint

                raw_data = self.connector.read_db(db_num, 0, max_offset)
                if raw_data is None:
                    for point in points:
                        failed_count += 1
                    continue

                for point in points:
                    try:
                        if point.data_type == "REAL":
                            value = get_real(raw_data, point.byte_offset)
                        elif point.data_type == "BOOL":
                            value = get_bool(raw_data, point.byte_offset, point.bit_offset)
                        elif point.data_type == "INT":
                            value = get_int(raw_data, point.byte_offset)
                        elif point.data_type == "DINT":
                            value = get_dint(raw_data, point.byte_offset)
                        else:
                            value = None

                        data_cache[point.name] = value
                        success_count += 1

                    except Exception:
                        failed_count += 1

            except Exception:
                for point in points:
                    failed_count += 1

        # 发送结果
        stats = {
            'success': success_count,
            'failed': failed_count
        }
        self.data_read_result.emit(data_cache, stats)
        self.read_finished.emit()


class PointTableMonitorWidget(QWidget):
    """点位表监控组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points: List[PointInfo] = []
        self.connector: Optional[S7PLCConnector] = None
        self.is_connected = False
        self.is_monitoring = False
        self.data_cache: Dict[str, any] = {}

        # 连接线程
        self.connection_thread = None
        self.read_thread = None
        self.is_connecting = False

        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'real_count': 0,
            'bool_count': 0
        }

        # PLC配置
        self.plc_ip = "192.168.0.1"
        self.point_table_file = "点位表.xlsx"

        self.init_ui()
        self.load_point_table()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题
        title = QLabel("PLC点位表监控")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # 统计信息面板
        stats_panel = self.create_stats_panel()
        layout.addWidget(stats_panel)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["序号", "点位名称", "地址", "数据类型", "当前值"])
        self.table.setMinimumHeight(300)

        # 设置表格样式
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #444;
                background-color: #1e1e1e;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: white;
                padding: 6px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # 设置行高
        self.table.verticalHeader().setDefaultSectionSize(25)

        layout.addWidget(self.table)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)

        self.setLayout(layout)

    def create_control_panel(self):
        """创建控制面板"""
        group = QGroupBox("控制面板")
        layout = QHBoxLayout()

        # 连接按钮
        self.connect_btn = QPushButton("连接PLC")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)

        # 开始监控按钮
        self.monitor_btn = QPushButton("开始监控")
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setEnabled(False)
        layout.addWidget(self.monitor_btn)

        # 刷新按钮
        refresh_btn = QPushButton("单次刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        refresh_btn.clicked.connect(self.single_refresh)
        refresh_btn.setEnabled(False)
        self.refresh_btn = refresh_btn
        layout.addWidget(refresh_btn)

        # 清除按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_stats_panel(self):
        """创建统计信息面板"""
        group = QGroupBox("统计信息")
        layout = QHBoxLayout()

        self.stats_labels = {}

        stats_config = [
            ('total', '总点数', '#2196F3'),
            ('success', '读取成功', '#4CAF50'),
            ('failed', '读取失败', '#f44336'),
            ('real_count', 'REAL类型', '#FF9800'),
            ('bool_count', 'BOOL类型', '#9C27B0')
        ]

        for key, label, color in stats_config:
            stat_label = QLabel(f"{label}: 0")
            stat_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    padding: 5px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
            """)
            layout.addWidget(stat_label)
            self.stats_labels[key] = stat_label

        layout.addStretch()
        group.setLayout(layout)
        return group

    def load_point_table(self):
        """加载点位表"""
        try:
            # 尝试从项目目录加载
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

            # 先尝试CSV文件
            csv_path = os.path.join(data_dir, self.point_table_file.replace('.xlsx', '.csv'))
            if os.path.exists(csv_path):
                self.load_from_csv(csv_path)
                return

            # 再尝试Excel文件
            file_path = os.path.join(data_dir, self.point_table_file)
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                self.load_from_dataframe(df)
                return

            # 如果都不存在，创建默认点位
            self.create_default_points()

        except Exception as e:
            self.status_label.setText(f"加载点位表失败: {e}")
            # 创建默认点位
            self.create_default_points()

    def load_from_csv(self, file_path):
        """从CSV文件加载点位表"""
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头

            for row in reader:
                if len(row) >= 3:
                    name, addr, dtype = row[0], row[1], row[2]
                    if not addr or addr == "nan" or addr == "NaN":
                        continue

                    try:
                        point = PointInfo.from_address(name, addr, dtype)
                        self.points.append(point)
                    except:
                        pass

        # 填充表格和更新统计
        self.fill_table_and_stats()

    def load_from_dataframe(self, df):
        """从DataFrame加载点位表"""
        for idx, row in df.iterrows():
            name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            addr = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            dtype = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""

            if not addr or addr == "nan" or addr == "NaN":
                continue

            try:
                point = PointInfo.from_address(name, addr, dtype)
                self.points.append(point)
            except:
                pass

        # 填充表格和更新统计
        self.fill_table_and_stats()

    def fill_table_and_stats(self):
        """填充表格并更新统计"""
        # 填充表格
        self.table.setRowCount(len(self.points))
        for idx, point in enumerate(self.points):
            self.set_row_data(idx, point)

        # 更新统计
        self.stats['total'] = len(self.points)
        self.stats['real_count'] = sum(1 for p in self.points if p.data_type == 'REAL')
        self.stats['bool_count'] = sum(1 for p in self.points if p.data_type == 'BOOL')
        self.update_stats_display()

        self.status_label.setText(f"已加载 {len(self.points)} 个点位")

    def create_default_points(self):
        """创建默认点位"""
        # 默认点位示例
        default_points = [
            ("温度1", "DB5.0.0", "REAL"),
            ("温度2", "DB5.4.0", "REAL"),
            ("压力1", "DB5.8.0", "REAL"),
            ("电机状态", "DB5.12.0", "BOOL"),
        ]

        for name, addr, dtype in default_points:
            try:
                point = PointInfo.from_address(name, addr, dtype)
                self.points.append(point)
            except:
                pass

        # 填充表格
        self.table.setRowCount(len(self.points))
        for idx, point in enumerate(self.points):
            self.set_row_data(idx, point)

        # 更新统计
        self.stats['total'] = len(self.points)
        self.stats['real_count'] = sum(1 for p in self.points if p.data_type == 'REAL')
        self.stats['bool_count'] = sum(1 for p in self.points if p.data_type == 'BOOL')
        self.update_stats_display()

        self.status_label.setText(f"已加载 {len(self.points)} 个默认点位")

    def set_row_data(self, idx: int, point, value=None):
        """设置表格行数据"""
        # 序号
        item0 = QTableWidgetItem(str(idx + 1))
        item0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 0, item0)

        # 点位名称
        item1 = QTableWidgetItem(point.name)
        self.table.setItem(idx, 1, item1)

        # 地址
        addr = f"DB{point.db_number}.{point.byte_offset}.{point.bit_offset}"
        item2 = QTableWidgetItem(addr)
        item2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 2, item2)

        # 数据类型
        item3 = QTableWidgetItem(point.data_type)
        item3.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 3, item3)

        # 当前值
        if value is not None:
            item4 = QTableWidgetItem(str(value))
            if point.data_type == "BOOL":
                if value:
                    item4.setBackground(QColor(76, 175, 80))
                else:
                    item4.setBackground(QColor(158, 158, 158))
            else:
                item4.setBackground(QColor(33, 150, 243))
        else:
            item4 = QTableWidgetItem("--")
            item4.setForeground(QColor(100, 100, 100))

        item4.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 4, item4)

    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            self.connect_to_plc()
        else:
            self.disconnect_from_plc()

    def connect_to_plc(self):
        """连接到PLC - 使用后台线程避免卡顿"""
        if self.is_connecting:
            return  # 防止重复连接

        self.is_connecting = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("连接中...")
        self.status_label.setText("⏳ 正在连接PLC...")

        # 创建并启动连接线程
        self.connection_thread = PLCConnectionThread(self.plc_ip)
        self.connection_thread.connection_result.connect(self.on_connection_result)
        self.connection_thread.finished.connect(self.on_connection_finished)
        self.connection_thread.start()

    def on_connection_result(self, success, message):
        """连接结果回调"""
        if success:
            self.connector = self.connection_thread.get_connector()
            self.is_connected = True
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.monitor_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.status_label.setText(f"✅ {message}")
        else:
            self.is_connected = False
            self.connect_btn.setText("连接PLC")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.status_label.setText(f"❌ {message}")

        self.connect_btn.setEnabled(True)

    def on_connection_finished(self):
        """连接线程结束"""
        self.is_connecting = False
        if self.connection_thread:
            self.connection_thread.deleteLater()
            self.connection_thread = None

    def disconnect_from_plc(self):
        """断开PLC连接"""
        # 停止监控
        self.timer.stop()
        self.is_monitoring = False
        self.monitor_btn.setText("开始监控")

        # 等待连接线程结束
        if self.connection_thread and self.connection_thread.isRunning():
            self.connection_thread.terminate()
            self.connection_thread.wait()

        # 等待读取线程结束
        if self.read_thread and self.read_thread.isRunning():
            self.read_thread.terminate()
            self.read_thread.wait()

        # 断开连接
        if self.connector:
            try:
                self.connector.disconnect()
            except:
                pass
            self.connector = None

        self.is_connected = False
        self.connect_btn.setText("连接PLC")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        self.monitor_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("已断开连接")

    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_btn.setText("停止监控")
            self.timer.start(1000)  # 1秒刷新一次
            self.status_label.setText("🔍 开始监控...")
        else:
            self.is_monitoring = False
            self.monitor_btn.setText("开始监控")
            self.timer.stop()
            self.status_label.setText("⏸ 停止监控")

    def single_refresh(self):
        """单次刷新 - 使用后台线程避免卡顿"""
        if not self.is_connected or not self.connector:
            self.status_label.setText("⚠️ 请先连接PLC")
            return

        if self.read_thread and self.read_thread.isRunning():
            self.status_label.setText("⏳ 正在读取数据...")
            return

        self.status_label.setText("⏳ 正在读取数据...")
        self.refresh_btn.setEnabled(False)

        # 按DB块分组
        db_groups = {}
        for point in self.points:
            if point.db_number not in db_groups:
                db_groups[point.db_number] = []
            db_groups[point.db_number].append(point)

        # 创建并启动读取线程
        self.read_thread = PLCDataReadThread(self.connector, self.points, db_groups)
        self.read_thread.data_read_result.connect(self.on_data_read_result)
        self.read_thread.read_finished.connect(self.on_read_finished)
        self.read_thread.start()

    def on_data_read_result(self, data_cache, stats):
        """数据读取结果回调"""
        # 更新数据缓存
        self.data_cache.update(data_cache)

        # 更新表格显示
        for point_name, value in data_cache.items():
            for idx, point in enumerate(self.points):
                if point.name == point_name:
                    self.set_row_data(idx, point, value)
                    break

        # 更新统计
        self.stats['success'] = stats['success']
        self.stats['failed'] = stats['failed']
        self.update_stats_display()

        self.status_label.setText(f"✅ 更新完成 | 成功: {stats['success']} 失败: {stats['failed']}")

    def on_read_finished(self):
        """读取线程结束"""
        self.refresh_btn.setEnabled(True)
        if self.read_thread:
            self.read_thread.deleteLater()
            self.read_thread = None

    def update_data(self):
        """更新数据（定时器调用）- 使用后台线程避免卡顿"""
        if not self.is_connected or not self.connector:
            return

        if self.read_thread and self.read_thread.isRunning():
            return  # 上次读取还未完成，跳过本次更新

        # 按DB块分组
        db_groups = {}
        for point in self.points:
            if point.db_number not in db_groups:
                db_groups[point.db_number] = []
            db_groups[point.db_number].append(point)

        # 创建并启动读取线程
        self.read_thread = PLCDataReadThread(self.connector, self.points, db_groups)
        self.read_thread.data_read_result.connect(self.on_data_read_result)
        self.read_thread.read_finished.connect(self.on_read_finished)
        self.read_thread.start()

    def update_stats_display(self):
        """更新统计显示"""
        self.stats_labels['total'].setText(f"总点数: {self.stats['total']}")
        self.stats_labels['success'].setText(f"读取成功: {self.stats['success']}")
        self.stats_labels['failed'].setText(f"读取失败: {self.stats['failed']}")
        self.stats_labels['real_count'].setText(f"REAL类型: {self.stats['real_count']}")
        self.stats_labels['bool_count'].setText(f"BOOL类型: {self.stats['bool_count']}")

    def clear_data(self):
        """清除数据显示"""
        for idx, point in enumerate(self.points):
            self.set_row_data(idx, point, None)

        self.stats['success'] = 0
        self.stats['failed'] = 0
        self.update_stats_display()
        self.status_label.setText("已清除数据")

    def cleanup(self):
        """清理资源"""
        # 停止监控
        self.timer.stop()
        self.is_monitoring = False

        # 终止并等待连接线程结束
        if self.connection_thread and self.connection_thread.isRunning():
            self.connection_thread.terminate()
            self.connection_thread.wait()

        # 终止并等待读取线程结束
        if self.read_thread and self.read_thread.isRunning():
            self.read_thread.terminate()
            self.read_thread.wait()

        # 断开PLC连接
        if self.connector:
            try:
                self.connector.disconnect()
            except:
                pass
            self.connector = None

        self.is_connected = False

