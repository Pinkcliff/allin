# -*- coding: utf-8 -*-
"""
编码器监控模块
用于实时监控编码器位置数据
"""
import sys
import os
from datetime import datetime
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QGridLayout, QTextEdit,
    QSpinBox, QLCDNumber, QFrame
)
from PySide6.QtCore import QTimer, QThread, Signal, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

# 添加s7_comm模块路径
sys.path.insert(0, os.path.dirname(__file__))
from s7_comm import S7PLCConnector, DBItem, DataType


class SimplePlotWidget(QFrame):
    """简单的实时绘图组件（不依赖pyqtgraph）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data_points = []
        self.max_points = 500
        self.y_scale = 1.0
        self.y_offset = 0

    def add_data_point(self, value):
        """添加数据点"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()

    def clear_data(self):
        """清除数据"""
        self.data_points.clear()
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), QColor(46, 52, 64))

        # 绘制网格
        self.draw_grid(painter)

        # 绘制数据
        if len(self.data_points) > 1:
            self.draw_data(painter)

    def draw_grid(self, painter):
        """绘制网格"""
        pen = QPen(QColor(129, 161, 193, 50))
        painter.setPen(pen)

        width = self.width()
        height = self.height()

        # 垂直网格线
        for i in range(0, width, 50):
            painter.drawLine(i, 0, i, height)

        # 水平网格线
        for i in range(0, height, 50):
            painter.drawLine(0, i, width, i)

        # 中心线
        pen = QPen(QColor(129, 161, 193, 100))
        painter.setPen(pen)
        painter.drawLine(0, height // 2, width, height // 2)

    def draw_data(self, painter):
        """绘制数据曲线"""
        pen = QPen(QColor(136, 192, 208), 2)
        painter.setPen(pen)

        width = self.width()
        height = self.height()

        # 计算缩放
        if self.data_points:
            min_val = min(self.data_points)
            max_val = max(self.data_points)
            range_val = max_val - min_val

            if range_val > 0:
                self.y_scale = (height - 40) / range_val
                self.y_offset = min_val - (20 / self.y_scale)

        # 绘制曲线
        points = []
        for i, value in enumerate(self.data_points):
            x = (i / self.max_points) * width
            y = height - ((value - self.y_offset) * self.y_scale) - 20
            points.append((x, y))

        if len(points) > 1:
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i + 1][0]), int(points[i + 1][1]))


class EncoderDataReader(QThread):
    """编码器数据读取线程"""

    data_received = Signal(float, datetime)
    connection_status = Signal(bool, str)

    def __init__(self, plc_ip="192.168.0.1", db_number=5, offset=124):
        super().__init__()
        self.plc_ip = plc_ip
        self.db_number = db_number
        self.offset = offset
        self.is_running = False
        self.connector = None

    def run(self):
        """线程运行主循环"""
        self.is_running = True

        while self.is_running:
            try:
                if self.connector is None:
                    self.connector = S7PLCConnector(self.plc_ip)
                    if self.connector.connect():
                        self.connection_status.emit(True, "PLC 连接成功")
                    else:
                        self.connection_status.emit(False, "PLC 连接失败")
                        self.msleep(1000)
                        continue

                # 读取编码器位置 (REAL类型，4字节)
                data = self.connector.read_db(self.db_number, self.offset, 4)
                if data:
                    # 解析REAL值
                    import struct
                    position = struct.unpack('>f', data)[0]  # 大端序
                    current_time = datetime.now()
                    self.data_received.emit(position, current_time)
                    self.connection_status.emit(True, "数据读取正常")
                else:
                    self.connection_status.emit(False, "读取数据失败")

            except Exception as e:
                self.connection_status.emit(False, f"错误: {str(e)}")

                # 尝试重新连接
                try:
                    if self.connector:
                        self.connector.disconnect()
                    self.connector = None
                except:
                    pass

            # 控制读取频率 (100ms)
            self.msleep(100)

    def stop(self):
        """停止线程"""
        self.is_running = False
        try:
            if self.connector:
                self.connector.disconnect()
        except:
            pass
        self.wait()


class EncoderMonitorWidget(QWidget):
    """编码器监控组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_reader = None
        self.position_history = []
        self.last_position = 0
        self.change_count = 0
        self.start_time = None

        # 编码器配置
        self.plc_ip = "192.168.0.1"
        self.db_number = 5
        self.offset = 124

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题
        title = QLabel("编码器实时监控")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # 主要显示区域
        main_layout = QHBoxLayout()

        # 左侧：位置显示
        left_widget = self.create_position_widget()
        main_layout.addWidget(left_widget, stretch=1)

        # 右侧：实时曲线
        right_widget = self.create_chart_widget()
        main_layout.addWidget(right_widget, stretch=2)

        layout.addLayout(main_layout)

        # 控制和统计区域
        control_stats_layout = QHBoxLayout()

        # 控制面板
        control_widget = self.create_control_widget()
        control_stats_layout.addWidget(control_widget, stretch=1)

        # 统计信息
        stats_widget = self.create_stats_widget()
        control_stats_layout.addWidget(stats_widget, stretch=1)

        layout.addLayout(control_stats_layout)

        # 日志区域
        log_widget = self.create_log_widget()
        layout.addWidget(log_widget)

        # 定时器更新统计
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)

        self.setLayout(layout)

    def create_position_widget(self):
        """位置显示组件"""
        group = QGroupBox("当前位置")
        layout = QVBoxLayout()

        # 当前位置显示
        self.position_label = QLabel("0.000 mm")
        self.position_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #88C0D0;
            background-color: #2E3440;
            padding: 15px;
            border: 2px solid #4C566A;
            border-radius: 8px;
            text-align: center;
        """)
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.position_label)

        # 变化指示
        self.change_indicator = QLabel("● 无变化")
        self.change_indicator.setStyleSheet("color: #4C566A; font-size: 12px;")
        self.change_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.change_indicator)

        layout.addStretch()
        return group

    def create_chart_widget(self):
        """图表组件"""
        group = QGroupBox("位置变化曲线")
        layout = QVBoxLayout()

        # 创建简单绘图组件
        self.plot_widget = SimplePlotWidget()
        layout.addWidget(self.plot_widget)

        # 图表说明
        info_label = QLabel("显示最近 500 个数据点的位置变化")
        info_label.setStyleSheet("color: #4C566A; font-size: 10px;")
        layout.addWidget(info_label)

        return group

    def create_control_widget(self):
        """控制面板"""
        group = QGroupBox("控制")
        layout = QVBoxLayout()

        # 开始/停止按钮
        self.start_btn = QPushButton("开始监控")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)

        # 清除按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                color: white;
                padding: 6px;
                border-radius: 5px;
            }
        """)
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)

        # 变化阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("变化阈值:"))
        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(1, 100)
        self.threshold_spinbox.setValue(1)
        self.threshold_spinbox.setSuffix(" mm")
        threshold_layout.addWidget(self.threshold_spinbox)
        layout.addLayout(threshold_layout)

        layout.addStretch()
        return group

    def create_stats_widget(self):
        """统计信息"""
        group = QGroupBox("统计信息")
        layout = QGridLayout()

        # 当前值
        layout.addWidget(QLabel("当前值:"), 0, 0)
        self.current_label = QLabel("0.000 mm")
        layout.addWidget(self.current_label, 0, 1)

        # 最大值
        layout.addWidget(QLabel("最大值:"), 1, 0)
        self.max_label = QLabel("0.000 mm")
        self.max_label.setStyleSheet("color: #A3BE8C;")
        layout.addWidget(self.max_label, 1, 1)

        # 最小值
        layout.addWidget(QLabel("最小值:"), 2, 0)
        self.min_label = QLabel("0.000 mm")
        self.min_label.setStyleSheet("color: #BF616A;")
        layout.addWidget(self.min_label, 2, 1)

        # 变化次数
        layout.addWidget(QLabel("变化次数:"), 3, 0)
        self.changes_label = QLabel("0 次")
        self.changes_label.setStyleSheet("color: #EBCB8B; font-weight: bold;")
        layout.addWidget(self.changes_label, 3, 1)

        # 运行时间
        layout.addWidget(QLabel("运行时间:"), 4, 0)
        self.runtime_label = QLabel("00:00:00")
        layout.addWidget(self.runtime_label, 4, 1)

        layout.setRowStretch(5, 1)
        return group

    def create_log_widget(self):
        """日志组件"""
        group = QGroupBox("日志信息")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #3B4252;
                color: #D8DEE9;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border: 1px solid #4C566A;
            }
        """)
        layout.addWidget(self.log_text)

        return group

    def toggle_monitoring(self):
        """切换监控状态"""
        if self.data_reader is None or not self.data_reader.isRunning():
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """开始监控"""
        try:
            self.data_reader = EncoderDataReader(self.plc_ip, self.db_number, self.offset)
            self.data_reader.data_received.connect(self.on_data_received)
            self.data_reader.connection_status.connect(self.on_status_update)
            self.data_reader.start()

            self.start_btn.setText("停止监控")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #BF616A;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 5px;
                }
            """)

            self.start_time = datetime.now()
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控...")

        except Exception as e:
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 启动失败: {e}")

    def stop_monitoring(self):
        """停止监控"""
        if self.data_reader:
            self.data_reader.stop()
            self.data_reader = None

        self.start_btn.setText("开始监控")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
        """)

        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 监控已停止")

    def on_data_received(self, position, timestamp):
        """接收数据"""
        # 更新显示
        self.position_label.setText(f"{position:.3f} mm")
        self.current_label.setText(f"{position:.3f} mm")

        # 添加到历史数据
        self.position_history.append(position)
        if len(self.position_history) > 500:
            self.position_history.pop(0)

        # 更新图表
        self.plot_widget.add_data_point(position)

        # 检测变化
        if abs(position - self.last_position) >= self.threshold_spinbox.value():
            self.change_count += 1
            self.change_indicator.setText(f"● 发生变化 ({self.change_count} 次)")
            self.change_indicator.setStyleSheet("color: #A3BE8C; font-size: 12px;")

            # 记录到日志
            self.log_text.append(
                f"[{timestamp.strftime('%H:%M:%S')}] 位置变化: {self.last_position:.3f} → {position:.3f} mm"
            )

            self.last_position = position

            # 3秒后恢复指示器
            QTimer.singleShot(3000, lambda: self.change_indicator.setStyleSheet("color: #4C566A; font-size: 12px;"))

    def on_status_update(self, connected, message):
        """状态更新"""
        if connected:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #A3BE8C; font-size: 12px; font-weight: bold;")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #BF616A; font-size: 12px; font-weight: bold;")

    def update_display(self):
        """更新显示"""
        # 更新统计信息
        if self.position_history:
            max_val = max(self.position_history)
            min_val = min(self.position_history)

            self.max_label.setText(f"{max_val:.3f} mm")
            self.min_label.setText(f"{min_val:.3f} mm")
            self.changes_label.setText(f"{self.change_count} 次")

        # 更新运行时间
        if self.start_time:
            runtime = datetime.now() - self.start_time
            hours, remainder = divmod(runtime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def clear_data(self):
        """清除数据"""
        self.position_history.clear()
        self.plot_widget.clear_data()
        self.change_count = 0
        self.change_indicator.setText("● 无变化")
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 数据已清除")

    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
