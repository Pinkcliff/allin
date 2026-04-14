"""
电驱板风扇控制软件
目标: 192.168.1.100:6005
10块电驱板(0-9), 每块板16个风扇
勾选风扇后点击发送, 风扇转动
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import struct
import threading
from datetime import datetime


class FanControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电驱板风扇控制 - 192.168.1.100")
        self.root.resizable(False, False)

        # 网络参数
        self.target_ip = "192.168.1.100"
        self.target_port = 6005

        # 帧计数器
        self.frame_counter = 0

        # PWM 满速存储值 = 1000 (0x03E8, LE: e803)
        self.PWM_FULL = 1000

        # 数据区结构: 640字节 = 10块板 × 64字节
        # 每块板64字节 = 32个16位LE值(每个风扇2个值)
        # 板N的偏移 = N * 64
        self.BYTES_PER_BOARD = 64

        # 存储所有板的风扇勾选状态: board_vars[board_id][fan_id]
        self.board_vars = {}

        # 查询线程控制
        self.query_running = False
        self.query_thread = None

        self._build_ui()

    def _build_ui(self):
        # 顶部: 目标地址 + PWM 控制
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="目标: 192.168.1.100:6005", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)

        ttk.Label(top_frame, text="PWM转速(%):").pack(side=tk.LEFT, padx=(20, 5))
        self.pwm_var = tk.IntVar(value=100)
        self.pwm_scale = ttk.Scale(top_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                    variable=self.pwm_var, length=150)
        self.pwm_scale.pack(side=tk.LEFT, padx=5)
        self.pwm_label = ttk.Label(top_frame, text="100%", width=6)
        self.pwm_label.pack(side=tk.LEFT)
        self.pwm_var.trace_add("write", self._on_pwm_change)

        # 按钮: 全选 / 全不选 / 发送
        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="全部勾选", command=self._select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全部取消", command=self._deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="发送指令(勾选的风扇转动)", command=self._send_all).pack(side=tk.LEFT, padx=20)
        self.query_btn = ttk.Button(btn_frame, text="开始查询", command=self._toggle_query)
        self.query_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.RIGHT, padx=5)
        self.status_label = ttk.Label(btn_frame, text="就绪", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 主区域: 左边板子面板 + 右边日志
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左边: 10块板的面板
        boards_frame = ttk.Frame(main_frame, padding=5)
        boards_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        for board_id in range(10):
            self._build_board_panel(boards_frame, board_id)

        # 右边: 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="  命令日志  ", padding=3)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)

        self.log_text = tk.Text(log_frame, width=60, height=28, font=("Consolas", 9),
                                bg="#1e1e1e", fg="#cccccc", state=tk.DISABLED, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_board_panel(self, parent, board_id):
        frame = ttk.LabelFrame(parent, text=f"  板 {board_id}  ", padding=3)
        frame.grid(row=board_id // 2, column=board_id % 2, padx=3, pady=2, sticky="ew")
        parent.columnconfigure(board_id % 2, weight=1)

        fan_vars = {}

        # 每块板: 板选择勾 + 16个风扇勾
        board_var = tk.BooleanVar(value=False)
        self.board_vars[board_id] = {"board": board_var, "fans": fan_vars}

        header = ttk.Frame(frame)
        header.pack(fill=tk.X)

        board_cb = ttk.Checkbutton(header, text=f"电驱板 {board_id}", variable=board_var,
                                    command=lambda bid=board_id: self._toggle_board(bid))
        board_cb.pack(side=tk.LEFT)

        # 发送按钮(单独控制这块板)
        ttk.Button(header, text="发送", width=4,
                   command=lambda bid=board_id: self._send_board(bid)).pack(side=tk.RIGHT, padx=2)

        # 16个风扇, 排成2行8列
        fans_frame = ttk.Frame(frame)
        fans_frame.pack(fill=tk.X, pady=2)

        for fan_id in range(16):
            row = fan_id // 8
            col = fan_id % 8
            var = tk.BooleanVar(value=False)
            fan_vars[fan_id] = var
            cb = ttk.Checkbutton(fans_frame, text=f"F{fan_id}", variable=var)
            cb.grid(row=row, column=col, padx=1, sticky="w")

    def _on_pwm_change(self, *args):
        val = self.pwm_var.get()
        self.pwm_label.config(text=f"{val}%")

    def _log(self, msg):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        """清空日志"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _toggle_query(self):
        """开始/停止查询"""
        if self.query_running:
            self.query_running = False
            self.query_btn.config(text="开始查询")
            self._log("查询已停止")
        else:
            self.query_running = True
            self.query_btn.config(text="停止查询")
            self.query_thread = threading.Thread(target=self._query_loop, daemon=True)
            self.query_thread.start()
            self._log("查询已启动 (1秒/次)")

    def _query_loop(self):
        """后台线程: 每1秒发送查询帧"""
        query_frame = bytes.fromhex("aa000000000300000000cc")
        while self.query_running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2.0)
                sock.sendto(query_frame, (self.target_ip, self.target_port))
                # 接收响应
                try:
                    data, addr = sock.recvfrom(4096)
                    self.root.after(0, self._on_query_response, data)
                except socket.timeout:
                    self.root.after(0, self._log, "查询超时,无响应")
                sock.close()
            except Exception as e:
                self.root.after(0, self._log, f"查询发送失败: {e}")
            # 等1秒, 用小间隔检查退出标志
            for _ in range(10):
                if not self.query_running:
                    break
                threading.Event().wait(0.1)

    def _on_query_response(self, data):
        """处理查询响应(在主线程中更新UI)"""
        self._log(f"查询响应({len(data)}字节): {data.hex()}")

    def _toggle_board(self, board_id):
        checked = self.board_vars[board_id]["board"].get()
        for var in self.board_vars[board_id]["fans"].values():
            var.set(checked)

    def _select_all(self):
        for bid in range(10):
            self.board_vars[bid]["board"].set(True)
            for var in self.board_vars[bid]["fans"].values():
                var.set(True)

    def _deselect_all(self):
        for bid in range(10):
            self.board_vars[bid]["board"].set(False)
            for var in self.board_vars[bid]["fans"].values():
                var.set(False)

    def _build_frame(self, all_boards_fan_states):
        """
        构建一帧数据，包含所有板的风扇状态。
        all_boards_fan_states: {board_id: {fan_id: True/False, ...}, ...}
        640字节 = 10板 × 64字节，板N的偏移 = N × 64
        每板64字节 = 32个16位LE值，每个风扇占2个值(4字节)
        """
        # 帧头
        header = struct.pack('B', 0xAA)
        # 帧号 (4字节, 递增)
        frame_num = struct.pack('<I', self.frame_counter)
        self.frame_counter = (self.frame_counter + 1) & 0xFFFFFFFF
        # 帧类型
        frame_type = struct.pack('B', 0x01)
        # 链路ID
        link_id = struct.pack('B', 0x00)
        # 电驱板ID (固定0x00)
        board_id_byte = struct.pack('B', 0x00)
        # 数据长度 (640字节, 大端序)
        data_len = struct.pack('>H', 640)

        # 构建数据区 (640字节, 全零初始化)
        data = bytearray(640)

        # PWM百分比 -> 存储值 (100% -> 1000)
        pwm_value = int(self.pwm_var.get() * self.PWM_FULL / 100)

        # 填充每块板的风扇数据
        for board_id, fan_states in all_boards_fan_states.items():
            board_offset = board_id * self.BYTES_PER_BOARD  # 板N偏移 = N * 64
            for fan_id in range(16):
                if fan_states.get(fan_id, False):
                    val = pwm_value
                else:
                    val = 0
                # 每个风扇占2个参数位置(4字节)
                offset = board_offset + fan_id * 4
                struct.pack_into('<H', data, offset, val)
                struct.pack_into('<H', data, offset + 2, val)

        # 帧尾
        tail = struct.pack('B', 0xCC)

        frame = header + frame_num + frame_type + link_id + board_id_byte + data_len + bytes(data) + tail
        return frame

    def _send_frame(self, frame):
        """通过UDP发送帧"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.sendto(frame, (self.target_ip, self.target_port))
            sock.close()
            return True
        except Exception as e:
            return str(e)

    def _send_board(self, board_id):
        """发送单块板的控制指令(一包数据，只填这块板的位置)"""
        fan_states = {}
        for fan_id in range(16):
            fan_states[fan_id] = self.board_vars[board_id]["fans"][fan_id].get()

        selected = [f"F{i}" for i in range(16) if fan_states[i]]
        if not selected:
            self.status_label.config(text=f"板{board_id}: 没有选中任何风扇", foreground="orange")
            self._log(f"板{board_id}: 没有选中任何风扇，跳过")
            return

        all_boards = {board_id: fan_states}
        frame = self._build_frame(all_boards)
        self._log(f"发送 -> {self.target_ip}:{self.target_port} | 板ID:{board_id} | 风扇:{','.join(selected)} | PWM:{self.pwm_var.get()}% ({len(frame)}字节)")
        self._log(f"数据: {frame.hex()}")
        result = self._send_frame(frame)

        if result is True:
            self.status_label.config(
                text=f"板{board_id}: 已发送 ({len(selected)}个风扇, PWM={self.pwm_var.get()}%)",
                foreground="green"
            )
            self._log(f"板{board_id}: 发送成功")
        else:
            self.status_label.config(text=f"板{board_id}: 发送失败 - {result}", foreground="red")
            self._log(f"板{board_id}: 发送失败 - {result}")

    def _send_all(self):
        """一包数据发送所有有选中风扇的板"""
        self._log("=" * 40)

        # 收集所有选中风扇的板
        all_boards = {}
        for board_id in range(10):
            fan_states = {}
            has_selected = False
            for fan_id in range(16):
                checked = self.board_vars[board_id]["fans"][fan_id].get()
                fan_states[fan_id] = checked
                if checked:
                    has_selected = True
            if has_selected:
                all_boards[board_id] = fan_states

        if not all_boards:
            self.status_label.config(text="没有选中任何风扇", foreground="orange")
            self._log("没有选中任何风扇")
            self._log("=" * 40)
            return

        # 一包数据，各板数据在各自偏移位置
        board_list = [f"板{bid}({','.join([f'F{i}' for i in range(16) if all_boards[bid][i]])})" for bid in all_boards]
        self._log(f"合并发送: {', '.join(board_list)}")
        self._log(f"PWM: {self.pwm_var.get()}%")

        frame = self._build_frame(all_boards)
        self._log(f"帧大小: {len(frame)}字节")
        self._log(f"数据: {frame.hex()}")

        result = self._send_frame(frame)
        if result is True:
            self.status_label.config(
                text=f"发送成功 ({len(all_boards)}块板, PWM={self.pwm_var.get()}%)",
                foreground="green"
            )
            self._log(f"发送成功")
        else:
            self.status_label.config(text=f"发送失败 - {result}", foreground="red")
            self._log(f"发送失败 - {result}")
        self._log("=" * 40)


def main():
    root = tk.Tk()
    app = FanControlApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
