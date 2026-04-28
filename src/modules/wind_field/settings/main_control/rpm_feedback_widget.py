# -*- coding: utf-8 -*-
"""
转速反馈窗口 - 显示电驱板返回的所有风扇实际转速

数据来源: UDP监听器收到的 BB 0x05 状态上报帧
帧结构: BB(1) + 计数器(4) + 类型(1) + 数据长度(2) + 数据区(680) + CC CC(2) = 690字节
数据区: 10板 × 68字节, 每板 = 板ID(1) + 电流(2) + 温度(1) + 16风扇×4字节(64)
每风扇: RPM1(2B LE) + RPM2(2B LE), 转速 = 150000 / raw
"""

import struct
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QLabel, QPushButton, QGraphicsEllipseItem
)
from PySide6.QtCore import Qt, QRectF, QSizeF, Signal
from PySide6.QtGui import QPen, QBrush, QPainter, QColor

from . import config
from . import utils


class RPMCell(QGraphicsRectItem):
    """转速反馈网格中的单个格子"""

    def __init__(self, row, col, size, spacing):
        total = size + spacing
        super().__init__(col * total, row * total, size, size)
        self.row = row
        self.col = col
        self.rpm1 = 0
        self.rpm2 = 0
        self._has_data = False
        self.setAcceptHoverEvents(True)
        # 默认白色背景（与PWM画布一致）
        self.bg_color = QColor(255, 255, 255)
        self.text_color = QColor(0, 0, 0)
        self.setBrush(QBrush(self.bg_color))
        self.setPen(QPen(Qt.NoPen))

    def set_rpm(self, rpm1, rpm2=0):
        self.rpm1 = rpm1
        self.rpm2 = rpm2
        self._has_data = True
        if rpm1 <= 0:
            # 0 RPM 也显示颜色（淡蓝，与PWM 0%一致）
            self.bg_color = utils.value_to_color(0)
            self.text_color = utils.get_contrasting_text_color(self.bg_color)
        else:
            # 按RPM比例映射到0-100，使用与PWM相同的颜色表
            ratio = min(rpm1 / 15000.0, 1.0) * 100
            self.bg_color = utils.value_to_color(ratio)
            self.text_color = utils.get_contrasting_text_color(self.bg_color)
        self.setBrush(QBrush(self.bg_color))
        self.update()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if not self._has_data or config.CELL_SIZE <= 12:
            return
        painter.setPen(self.text_color)
        painter.setFont(config.CELL_FONT)
        # 显示RPM值（除以100，3位数字适合格子大小）
        painter.drawText(self.boundingRect(), Qt.AlignCenter, f"{int(self.rpm1 / 100)}")


class RPMFeedbackWindow(QDialog):
    """转速反馈窗口 - 40x40 网格显示所有风扇实际转速"""

    fan_hover = Signal(int, int, float, float)  # row, col, rpm1, rpm2
    fan_hover_exit = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("转速反馈 (RPM Feedback)")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.rpm_data = np.zeros((config.GRID_DIM, config.GRID_DIM, 2))
        self.hover_info = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 顶部信息栏
        top_layout = QHBoxLayout()
        self.info_label = QLabel("等待电驱板返回数据...")
        self.info_label.setStyleSheet("color: #888;")
        top_layout.addWidget(self.info_label)
        top_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedWidth(60)
        top_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.setStyleSheet("QPushButton { color: #e57373; }")
        self.clear_btn.clicked.connect(self._clear_data)
        top_layout.addWidget(self.clear_btn)

        layout.addLayout(top_layout)

        # 悬停信息
        self.hover_label = QLabel("")
        self.hover_label.setStyleSheet(
            "color: #ccc; background: #2a2a3e; padding: 3px 6px; border-radius: 3px;"
        )
        layout.addWidget(self.hover_label)

        # 网格视图
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFixedSize(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
        self.scene.setSceneRect(
            -config.CELL_SPACING, -config.CELL_SPACING,
            config.CANVAS_WIDTH + config.CELL_SPACING,
            config.CANVAS_HEIGHT + config.CELL_SPACING
        )
        self.view.setMouseTracking(True)

        # 创建 40x40 网格
        self.cells = [[None] * config.GRID_DIM for _ in range(config.GRID_DIM)]
        for r in range(config.GRID_DIM):
            for c in range(config.GRID_DIM):
                cell = RPMCell(r, c, config.CELL_SIZE, config.CELL_SPACING)
                self.scene.addItem(cell)
                self.cells[r][c] = cell

        layout.addWidget(self.view)

        # 底部说明
        bottom = QLabel("数值: RPM/100 (如 75 = 7500RPM)  |  颜色: 低(淡蓝) → 中(绿/黄) → 高(红)  |  与PWM画布配色一致")
        bottom.setStyleSheet("color: #555; font-size: 10px;")
        layout.addWidget(bottom)

        # 模块边框 overlay
        self._draw_module_borders()

    def _draw_module_borders(self):
        """画模块分割线 (4x4格子一组)"""
        pen = QPen(config.MODULE_LINE_COLOR, config.MODULE_LINE_WIDTH, Qt.SolidLine)
        module_px = config.MODULE_DIM * config.TOTAL_CELL_SIZE
        offset = config.CELL_SPACING / 2
        for r in range(config.MODULE_DIM, config.GRID_DIM, config.MODULE_DIM):
            y = r * config.TOTAL_CELL_SIZE - offset
            self.scene.addLine(0, y, config.CANVAS_WIDTH, y, pen)
        for c in range(config.MODULE_DIM, config.GRID_DIM, config.MODULE_DIM):
            x = c * config.TOTAL_CELL_SIZE - offset
            self.scene.addLine(x, 0, x, config.CANVAS_HEIGHT, pen)

    def update_from_feedback(self, data: bytes, source_ip: str):
        """解析 BB 0x05 响应帧，更新 RPM 网格"""
        if len(data) < 10 or data[0] != 0xBB:
            return

        frame_type = data[5]
        if frame_type != 0x05:
            return

        data_len = (data[6] << 8) | data[7]
        payload = data[8:8 + data_len]

        if len(payload) < 680:
            return

        # 从源 IP 确定链路 ID
        try:
            last_octet = int(source_ip.split('.')[3])
            chain_id = last_octet - 100
        except (ValueError, IndexError):
            return

        if chain_id < 0 or chain_id >= 10:
            return

        updated = 0
        for board_idx in range(10):
            off = board_idx * 68
            bd = payload[off:off + 68]
            board_in_chain = bd[0]
            if board_in_chain >= 10:
                continue

            # 映射到网格位置 (与发送端一致)
            col_start = (9 - chain_id) * 4
            row_start = (9 - board_in_chain) * 4

            for fan_pos in range(16):
                fan_off = 4 + fan_pos * 4
                raw1 = struct.unpack_from('<H', bd, fan_off)[0]
                raw2 = struct.unpack_from('<H', bd, fan_off + 2)[0]

                rpm1 = 150000.0 / raw1 if raw1 > 0 else 0.0
                rpm2 = 150000.0 / raw2 if raw2 > 0 else 0.0

                fan_row = fan_pos // 4
                fan_col = fan_pos % 4
                gr = row_start + fan_row
                gc = col_start + fan_col

                if 0 <= gr < 40 and 0 <= gc < 40:
                    self.rpm_data[gr, gc, 0] = rpm1
                    self.rpm_data[gr, gc, 1] = rpm2
                    self.cells[gr][gc].set_rpm(rpm1, rpm2)
                    if rpm1 > 0:
                        updated += 1

        self.info_label.setText(
            f"链路{chain_id} ({source_ip}) 已更新 | "
            f"有效风扇: {updated} | "
            f"RPM范围: {self.rpm_data[:,:,0].max():.0f}"
        )
        self.info_label.setStyleSheet("color: #4CAF50;")

    def _clear_data(self):
        """清空所有 RPM 数据"""
        self.rpm_data.fill(0)
        for r in range(config.GRID_DIM):
            for c in range(config.GRID_DIM):
                cell = self.cells[r][c]
                cell._has_data = False
                cell.rpm1 = 0
                cell.rpm2 = 0
                cell.bg_color = QColor(255, 255, 255)
                cell.text_color = QColor(0, 0, 0)
                cell.setBrush(QBrush(cell.bg_color))
                cell.update()
        self.info_label.setText("数据已清空，等待电驱板返回...")
        self.info_label.setStyleSheet("color: #888;")
        self.hover_label.setText("")
