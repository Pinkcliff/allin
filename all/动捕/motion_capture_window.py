# -*- coding: utf-8 -*-
"""
动捕数据采集窗口

功能：
- 连接动捕系统
- 实时采集数据
- 保存为CSV文件
"""

import sys
import os
import csv
import time
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QGroupBox,
    QFileDialog, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer

# 添加SDK路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.join(current_dir, 'LuMoSDKPy')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)


class WorkerSignals(QObject):
    """工作线程信号"""
    data_received = Signal(int, int, str)  # frame_id, marker_count, status
    error_occurred = Signal(str)
    finished = Signal(str)  # 保存的文件路径
    log_message = Signal(str)


class MotionCaptureWorker(threading.Thread):
    """动捕数据采集工作线程"""

    def __init__(self, ip, save_dir, signals):
        super().__init__()
        self.ip = ip
        self.save_dir = save_dir
        self.signals = signals
        self.running = True
        self.paused = False

        # CSV管理
        self.current_csv_file = None
        self.current_writer = None
        self.current_marker_count = 0
        self.current_frame_count = 0
        self.total_frame_count = 0

        # 超时设置
        self.last_data_time = None
        self.data_timeout = 5  # 5秒无数据自动停止

    def stop(self):
        """停止采集"""
        self.running = False

    def pause(self):
        """暂停采集"""
        self.paused = True

    def resume(self):
        """恢复采集"""
        self.paused = False

    def create_new_csv_file(self, marker_count):
        """创建新的CSV文件"""
        # 关闭旧CSV文件
        if self.current_csv_file is not None:
            self.current_csv_file.close()
            self.signals.log_message.emit(
                f"CSV文件已保存: {self.current_csv_file.name} (共{self.current_frame_count}帧)"
            )

        # 生成新文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = os.path.join(
            self.save_dir,
            f"LuMo_Data_{timestamp}_markers{marker_count}.csv"
        )

        # 创建新CSV文件
        self.current_csv_file = open(csv_filename, 'w', newline='', encoding='utf-8-sig')
        self.current_writer = csv.writer(self.current_csv_file)
        self.current_marker_count = marker_count
        self.current_frame_count = 0

        # 生成表头
        headers = [
            '帧ID', '时间戳', '相机同步时间(原始)', '相机同步时间(可读)',
            '数据广播时间(原始)', '数据广播时间(可读)',
        ]

        # 添加标记点列
        for i in range(1, marker_count + 1):
            headers.extend([
                f'标记{i}_ID', f'标记{i}_名称', f'标记{i}_X', f'标记{i}_Y', f'标记{i}_Z'
            ])

        # 添加刚体列
        headers.extend([
            '刚体1_ID', '刚体1_名称', '刚体1_追踪状态', '刚体1_X', '刚体1_Y', '刚体1_Z',
            '刚体1_qx', '刚体1_qy', '刚体1_qz', '刚体1_qw', '刚体1_质量等级',
            '刚体1_速度', '刚体1_X速度', '刚体1_Y速度', '刚体1_Z速度',
            '刚体1_加速度', '刚体1_X加速度', '刚体1_Y加速度', '刚体1_Z加速度',
            '刚体1_X欧拉角', '刚体1_Y欧拉角', '刚体1_Z欧拉角',
            '刚体2_ID', '刚体2_名称', '刚体2_追踪状态', '刚体2_X', '刚体2_Y', '刚体2_Z',
            '刚体2_qx', '刚体2_qy', '刚体2_qz', '刚体2_qw', '刚体2_质量等级',
            '时码_时', '时码_分', '时码_秒', '时码_帧', '时码_子帧',
        ])

        self.current_writer.writerow(headers)
        self.signals.log_message.emit(f"新CSV文件已创建: {csv_filename}")

    def run(self):
        """运行采集线程"""
        try:
            import LuMoSDKClient

            self.signals.log_message.emit("正在初始化SDK...")
            LuMoSDKClient.Init()

            self.signals.log_message.emit(f"正在连接到 {self.ip}...")
            LuMoSDKClient.Connnect(self.ip)

            self.signals.log_message.emit("连接成功！开始采集数据...")
            self.last_data_time = time.time()

            while self.running:
                # 检查超时
                if self.last_data_time and (time.time() - self.last_data_time > self.data_timeout):
                    self.signals.error_occurred.emit(f"超过{self.data_timeout}秒未收到数据，自动停止")
                    break

                # 非阻塞接收数据
                frame = LuMoSDKClient.ReceiveData(1)
                if frame is None:
                    time.sleep(0.001)
                    continue

                # 更新数据时间
                self.last_data_time = time.time()
                self.total_frame_count += 1

                # 检查标记点数量
                current_marker_num = len(frame.markers)

                # 创建新CSV（如果需要）
                if self.current_csv_file is None or current_marker_num > self.current_marker_count:
                    self.create_new_csv_file(current_marker_num)

                # 发送数据更新信号
                self.signals.data_received.emit(
                    frame.FrameId,
                    current_marker_num,
                    f"采集: 帧{frame.FrameId}"
                )

                # 写入CSV
                row_data = self._build_row_data(frame)
                self.current_writer.writerow(row_data)
                self.current_frame_count += 1

                # 每100帧打印进度
                if self.total_frame_count % 100 == 0:
                    self.signals.log_message.emit(
                        f"已记录 {self.total_frame_count} 帧数据 (当前文件: {self.current_frame_count}帧)"
                    )

            # 清理
            LuMoSDKClient.Close()
            if self.current_csv_file:
                file_path = self.current_csv_file.name
                self.current_csv_file.close()
                self.signals.finished.emit(file_path)

        except Exception as e:
            self.signals.error_occurred.emit(f"采集错误: {str(e)}")
            if self.current_csv_file:
                self.current_csv_file.close()

    def _build_row_data(self, frame):
        """构建CSV行数据"""
        row_data = []

        # 基础帧信息
        camera_sync_readable = datetime.fromtimestamp(
            frame.uCameraSyncTime / 1000000
        ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        broadcast_readable = datetime.fromtimestamp(
            frame.uBroadcastTime / 1000000
        ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        row_data.extend([
            frame.FrameId,
            frame.TimeStamp,
            frame.uCameraSyncTime,
            camera_sync_readable,
            frame.uBroadcastTime,
            broadcast_readable,
        ])

        # 标记数据
        markers_list = list(frame.markers)
        for i in range(self.current_marker_count):
            if i < len(markers_list):
                m = markers_list[i]
                row_data.extend([m.Id, m.Name, m.X, m.Y, m.Z])
            else:
                row_data.extend(['', '', '', '', ''])

        # 刚体数据
        rigids_list = list(frame.rigidBodys)
        for i in range(2):
            if i < len(rigids_list):
                r = rigids_list[i]
                if i == 0 and r.IsTrack:
                    row_data.extend([
                        r.Id, r.Name, 1 if r.IsTrack else 0, r.X, r.Y, r.Z,
                        r.qx, r.qy, r.qz, r.qw, r.QualityGrade,
                        r.speeds.fSpeed, r.speeds.XfSpeed, r.speeds.YfSpeed, r.speeds.ZfSpeed,
                        r.acceleratedSpeeds.fAcceleratedSpeed,
                        r.acceleratedSpeeds.XfAcceleratedSpeed,
                        r.acceleratedSpeeds.YfAcceleratedSpeed,
                        r.acceleratedSpeeds.ZfAcceleratedSpeed,
                        r.eulerAngle.X, r.eulerAngle.Y, r.eulerAngle.Z,
                    ])
                else:
                    row_data.extend([r.Id, r.Name, 1 if r.IsTrack else 0, r.X, r.Y, r.Z,
                        '', '', '', '', ''])
            else:
                if i == 0:
                    row_data.extend(['', '', '', '', '', '', '', '', '', '', '',
                        '', '', '', '', '', '', '', '', '', ''])
                else:
                    row_data.extend(['', '', '', '', '', '', '', '', ''])

        # 时码信息
        row_data.extend([
            frame.timeCode.mHours,
            frame.timeCode.mMinutes,
            frame.timeCode.mSeconds,
            frame.timeCode.mFrames,
            frame.timeCode.mSubFrame,
        ])

        return row_data


class MotionCaptureWindow(QMainWindow):
    """动捕数据采集窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.signals = WorkerSignals()
        self.is_capturing = False
        self.save_dir = str(Path.cwd())

        # 连接信号
        self.signals.data_received.connect(self._on_data_received)
        self.signals.error_occurred.connect(self._on_error)
        self.signals.finished.connect(self._on_finished)
        self.signals.log_message.connect(self._on_log)

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('动捕数据采集')
        self.setGeometry(200, 200, 800, 600)

        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 连接配置组
        config_group = QGroupBox("连接配置")
        config_layout = QVBoxLayout()

        # IP地址
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("动捕系统IP:"))
        self.ip_input = QLineEdit("192.168.3.24")
        ip_layout.addWidget(self.ip_input)
        config_layout.addLayout(ip_layout)

        # 保存目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("保存目录:"))
        self.dir_label = QLabel(self.save_dir)
        self.dir_label.setStyleSheet("color: gray;")
        dir_layout.addWidget(self.dir_label)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)
        config_layout.addLayout(dir_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # 控制按钮组
        control_group = QGroupBox("采集控制")
        control_layout = QHBoxLayout()

        self.capture_btn = QPushButton("开始采集")
        self.capture_btn.clicked.connect(self._toggle_capture)
        self.capture_btn.setEnabled(True)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.stop_btn = QPushButton("停止采集")
        self.stop_btn.clicked.connect(self._stop_capture)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        control_layout.addWidget(self.capture_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # 状态显示组
        status_group = QGroupBox("采集状态")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("状态: 未开始")
        self.status_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        stats_layout = QHBoxLayout()
        self.frame_label = QLabel("帧数: 0")
        self.marker_label = QLabel("标记点: 0")
        stats_layout.addWidget(self.frame_label)
        stats_layout.addWidget(self.marker_label)
        status_layout.addLayout(stats_layout)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)

        self._log("动捕数据采集窗口已启动")
        self._log("请配置IP地址和保存目录，然后点击'开始采集'")

    def _browse_directory(self):
        """浏览保存目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.dir_label.setText(dir_path)
            self._log(f"保存目录已设置为: {dir_path}")

    def _toggle_capture(self):
        """切换采集状态"""
        if not self.is_capturing:
            self._start_capture()
        else:
            self._stop_capture()

    def _start_capture(self):
        """开始采集"""
        ip = self.ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "警告", "请输入动捕系统IP地址")
            return

        self.is_capturing = True
        self.capture_btn.setText("采集中...")
        self.capture_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 采集中")
        self.status_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")

        # 创建并启动工作线程
        self.worker = MotionCaptureWorker(ip, self.save_dir, self.signals)
        self.worker.start()

        self._log("=" * 50)
        self._log("开始采集数据...")
        self._log(f"目标IP: {ip}")
        self._log(f"保存目录: {self.save_dir}")

    def _stop_capture(self):
        """停止采集"""
        if self.worker:
            self.worker.stop()
            self._log("正在停止采集...")

        self.is_capturing = False
        self.capture_btn.setText("开始采集")
        self.capture_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.status_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")

    def _on_data_received(self, frame_id, marker_count, status):
        """数据接收回调"""
        self.frame_label.setText(f"帧数: {frame_id}")
        self.marker_label.setText(f"标记点: {marker_count}")

    def _on_error(self, error_msg):
        """错误回调"""
        self._log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)
        self._stop_capture()

    def _on_finished(self, file_path):
        """采集完成回调"""
        self._log(f"采集完成！数据已保存到: {file_path}")
        QMessageBox.information(
            self,
            "采集完成",
            f"数据采集已完成！\n保存位置: {file_path}"
        )

    def _on_log(self, message):
        """日志回调"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def _log(self, message):
        """输出日志"""
        self._on_log(message)

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_capturing:
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "正在采集中，确定要关闭窗口吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._stop_capture()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
