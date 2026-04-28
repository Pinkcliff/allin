# -*- coding: utf-8 -*-
"""
反馈信息面板 - 嵌入右侧Dock，显示电驱板返回数据和解析结果

解析三种帧格式：
  - BB...CCCC 板返回帧 (0x05状态上报、0x06查询反馈)
  - AA...CC   电脑发送帧 (0x01控制指令、0x03参数查询)
  - 纯680字节 状态上报Data区
"""

import struct
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QRadioButton, QButtonGroup, QLabel
)
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont


class FeedbackPanel(QGroupBox):
    """反馈信息面板 - 嵌入右侧Dock中"""

    def __init__(self, parent=None):
        super().__init__("反馈信息", parent)
        self._output_lines = []
        self._build_ui()

    # ================================================================
    # UI
    # ================================================================

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # 顶栏: 字节序 + 按钮
        top = QHBoxLayout()
        top.setSpacing(4)

        top.addWidget(QLabel("字节序:"))
        self.radio_big = QRadioButton("大端")
        self.radio_small = QRadioButton("小端")
        self.radio_big.setChecked(True)

        endian_group = QButtonGroup(self)
        endian_group.addButton(self.radio_big)
        endian_group.addButton(self.radio_small)
        top.addWidget(self.radio_big)
        top.addWidget(self.radio_small)

        top.addStretch()

        self.btn_parse = QPushButton("解析")
        self.btn_clear = QPushButton("清空")
        self.btn_parse.setFixedWidth(50)
        self.btn_clear.setFixedWidth(50)
        top.addWidget(self.btn_parse)
        top.addWidget(self.btn_clear)

        layout.addLayout(top)

        # HEX输入 (紧凑)
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(36)
        self.input_text.setFont(QFont("Consolas", 9))
        self.input_text.setAcceptRichText(False)
        self.input_text.setPlaceholderText("粘贴HEX数据后点解析，或自动接收电驱板返回数据")
        layout.addWidget(self.input_text)

        # 解析输出
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                border: none;
            }
        """)
        layout.addWidget(self.output_text)

        self.btn_parse.clicked.connect(self._analyze)
        self.btn_clear.clicked.connect(self._clear)

    # ================================================================
    # 属性
    # ================================================================

    @property
    def big_endian(self) -> bool:
        return self.radio_big.isChecked()

    def _endian_label(self) -> str:
        return "大端" if self.big_endian else "小端"

    # ================================================================
    # 输出辅助
    # ================================================================

    def _out(self, msg: str):
        self._output_lines.append(msg)

    def _flush_output(self):
        self.output_text.setPlainText("\n".join(self._output_lines))
        # 自动滚到底部
        sb = self.output_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear(self):
        self.input_text.clear()
        self.output_text.clear()
        self._output_lines.clear()

    # ================================================================
    # 外部调用接口 - 自动接收电驱板返回数据
    # ================================================================

    def display_raw_data(self, raw_bytes: bytes):
        """供外部调用：接收原始字节并自动解析显示"""
        self._output_lines.clear()
        self._out(f"[自动接收] {len(raw_bytes)} 字节")
        self._dispatch_parse(raw_bytes)
        self._flush_output()

    # ================================================================
    # 字节读取
    # ================================================================

    def _read_u16(self, b1: int, b2: int) -> int:
        if self.big_endian:
            return (b1 << 8) | b2
        else:
            return (b2 << 8) | b1

    # ================================================================
    # 手动解析入口
    # ================================================================

    @Slot()
    def _analyze(self):
        raw = self.input_text.toPlainText().strip().replace(" ", "").replace("\n", "")
        if not raw:
            return
        try:
            data = bytes.fromhex(raw)
        except ValueError as e:
            self._output_lines.clear()
            self._out(f"HEX格式错误: {e}")
            self._flush_output()
            return

        self._output_lines.clear()
        self._out(f"数据长度: {len(data)} 字节  字节序: {self._endian_label()}")
        self._dispatch_parse(data)
        self._flush_output()

    def _dispatch_parse(self, data: bytes):
        if len(data) >= 9 and data[0] == 0xBB:
            self._parse_response_frame(data)
        elif len(data) >= 10 and data[0] == 0xAA:
            self._parse_command_frame(data)
        elif len(data) == 680:
            self._out("[680字节 → 状态上报Data区]")
            self._parse_status_data(data)
        else:
            self._out(f"无法识别 (长度={len(data)})")
            self._out("支持: BB..CCCC / AA..CC / 680字节")

    # ================================================================
    # 板返回帧 (BB...CCCC)
    # ================================================================

    def _parse_response_frame(self, data: bytes):
        self._out(f"帧头: 0x{data[0]:02X} {'(BB)' if data[0] == 0xBB else '(异常!)'}")
        counter = struct.unpack('<I', data[1:5])[0]
        self._out(f"计数器: {counter} (0x{counter:08X})")

        frame_type = data[5]
        self._out(f"类型: 0x{frame_type:02X} ({self._type_name(frame_type)})")

        data_len = (data[6] << 8) | data[7]
        self._out(f"数据长度: {data_len}")

        tail = data[-2:]
        tail_ok = '正确' if tail == b'\xcc\xcc' else '异常!'
        self._out(f"帧尾: {tail.hex().upper()} ({tail_ok})")

        payload = data[8:-2] if len(data) > 10 else b''

        if frame_type == 0x05:
            self._parse_status_data(payload)
        elif frame_type == 0x06:
            self._parse_0x06(payload)
        else:
            self._out(f"不支持的类型 0x{frame_type:02X}")

    # ================================================================
    # 0x05 状态上报 (680字节 = 10板 x 68字节)
    # ================================================================

    def _parse_status_data(self, payload: bytes):
        if len(payload) < 68:
            self._out(f"数据不足 ({len(payload)}B, 需68B)")
            return

        board_count = min(len(payload) // 68, 10)

        for i in range(board_count):
            off = i * 68
            c = payload[off:off + 68]

            bid = c[0]
            cur_raw = self._read_u16(c[1], c[2])
            cur_ma = cur_raw * 2.4
            temp = c[3]

            self._out(f"── 板{bid}: 电流={cur_ma:.1f}mA 温度={temp}°C ──")

            for fan_pos in range(16):
                i1 = fan_pos * 2
                raw1 = self._read_u16(c[4 + i1 * 2], c[4 + i1 * 2 + 1])
                speed1 = 150000 / raw1 if raw1 > 0 else 0

                i2 = fan_pos * 2 + 1
                raw2 = self._read_u16(c[4 + i2 * 2], c[4 + i2 * 2 + 1])
                speed2 = 150000 / raw2 if raw2 > 0 else 0

                if raw1 > 0 or raw2 > 0:
                    self._out(f"  位{fan_pos:2d}: {speed1:.0f}/{speed2:.0f} RPM")

    # ================================================================
    # 0x06 参数查询反馈
    # ================================================================

    def _parse_0x06(self, payload: bytes):
        self._out("--- 0x06 查询反馈 ---")
        if len(payload) >= 1:
            self._out(f"  IP尾偏移: {payload[0]} → IP尾={100 + payload[0]}")
        if len(payload) >= 2:
            self._out(f"  板ID: {payload[1]} (0x{payload[1]:02X})")
        if len(payload) >= 3:
            self._out(f"  预留: 0x{payload[2]:02X}")

    # ================================================================
    # 电脑发送帧 (AA...CC)
    # ================================================================

    def _parse_command_frame(self, data: bytes):
        self._out(f"帧头: 0x{data[0]:02X} (AA)")
        counter = struct.unpack('<I', data[1:5])[0]
        self._out(f"帧号: {counter} (0x{counter:08X})")
        frame_type = data[5]
        self._out(f"类型: 0x{frame_type:02X} ({self._type_name(frame_type)})")
        self._out(f"链路ID: 0x{data[6]:02X}  板ID: {data[7]} (0x{data[7]:02X})")
        data_len = (data[8] << 8) | data[9]
        self._out(f"数据长度: {data_len}")
        self._out(f"帧尾: 0x{data[-1]:02X} {'正确' if data[-1] == 0xCC else '异常!'}")

        if frame_type == 0x01 and data_len == 640:
            payload = data[10:-1]
            self._out("--- 0x01 控制指令 (10板×64B) ---")
            for bid in range(10):
                boff = bid * 64
                vals = []
                for fid in range(16):
                    foff = boff + fid * 4
                    if foff + 4 <= len(payload):
                        v1 = struct.unpack_from('<H', payload, foff)[0]
                        v2 = struct.unpack_from('<H', payload, foff + 2)[0]
                        if v1 > 0 or v2 > 0:
                            vals.append(f"F{fid}={v1}")
                if vals:
                    self._out(f"  板{bid}: {', '.join(vals)}")
        elif frame_type == 0x03:
            self._out("--- 0x03 参数查询 (无Data区) ---")

    # ================================================================
    # 工具
    # ================================================================

    @staticmethod
    def _type_name(ft: int) -> str:
        names = {0x01: "控制指令", 0x03: "参数查询", 0x05: "状态上报", 0x06: "查询反馈"}
        return names.get(ft, "未知")
