"""
实时同步版动态表面分析系统
精确时间同步 + 预渲染缓存技术
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import threading
import time
import queue
from collections import deque
from matplotlib import cm
import pickle
import os

# 解决中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class RealtimeGUI:
    def __init__(self):
        # DPI感知
        self.setup_dpi_awareness()

        # 创建窗口
        self.root = tk.Tk()
        self.root.title("动态表面分析系统 - 实时同步版")

        # 设置窗口
        self.setup_window()

        # 设置样式
        self.setup_modern_style()

        # 动画缓存系统
        self.cache_system = CacheSystem()

        # 时间同步系统
        self.time_sync = TimeSync()

        # 创建UI
        self.setup_ui()

        # 初始化图形
        self.setup_plot()

        # 动画控制
        self.animation_state = {
            'running': False,
            'paused': False,
            'thread': None,
            'start_time': 0,
            'real_start_time': 0,
            'fps': 60,
            'duration': 5.0,
            'cache_enabled': True,
            'total_frames': 0
        }

        # 当前设置
        self.current_colormap = 'viridis'
        self.colormaps = ['viridis', 'plasma', 'coolwarm', 'magma', 'ocean', 'twilight']

        # 初始显示
        self.update_plot()

    def setup_dpi_awareness(self):
        """DPI感知设置"""
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    def setup_window(self):
        """窗口设置"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = min(1400, int(screen_width * 0.85))
        window_height = min(900, int(screen_height * 0.85))

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 700)

    def setup_modern_style(self):
        """样式设置"""
        self.style = ttk.Style()

        # 颜色方案
        self.colors = {
            'bg': '#1E1E1E',
            'fg': '#FFFFFF',
            'select_bg': '#007ACC',
            'hover_bg': '#3C3C3C',
            'border': '#2D2D30',
            'accent': '#569CD6',
            'success': '#4EC9B0',
            'warning': '#CE9178',
            'error': '#F44747'
        }

        self.root.configure(bg=self.colors['bg'])
        self.style.theme_use('default')

    def setup_ui(self):
        """UI设置"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 标题
        self.create_header(main_container)

        # 内容区
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 左侧控制面板
        self.create_control_panel(content_frame)

        # 右侧显示区
        self.create_display_area(content_frame)

        # 状态栏
        self.create_status_bar(main_container)

    def create_header(self, parent):
        """标题栏"""
        header_frame = tk.Frame(parent, bg=self.colors['select_bg'], height=50)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="动态表面分析系统 - 实时同步版",
                             font=('Microsoft YaHei', 16, 'bold'),
                             fg='white', bg=self.colors['select_bg'])
        title_label.pack(side=tk.LEFT, padx=30, pady=12)

        sync_label = tk.Label(header_frame, text="⚡ 实时同步",
                            font=('Microsoft YaHei', 11),
                            fg='#4EC9B0', bg=self.colors['select_bg'])
        sync_label.pack(side=tk.RIGHT, padx=30, pady=12)

    def create_control_panel(self, parent):
        """控制面板"""
        left_frame = tk.Frame(parent, bg=self.colors['bg'], width=380)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_frame.pack_propagate(False)

        # Notebook
        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 标签页
        self.create_function_tab()
        self.create_animation_tab()
        self.create_cache_tab()

    def create_function_tab(self):
        """函数标签页"""
        func_frame = ttk.Frame(self.notebook)
        self.notebook.add(func_frame, text="函数选择")

        # 函数选择
        func_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        func_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(func_container, text="选择数学函数",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 函数选项
        self.func_var = tk.StringVar(value="simple_wave")
        functions = [
            ("● 简单波", "simple_wave", "基础正弦波形"),
            ("○ 径向波", "radial_wave", "同心圆扩散波"),
            ("★ 高斯波包", "gaussian_wave", "高斯调制波"),
            ("‖ 驻波", "standing_wave", "固定振动模式")
        ]

        for icon, value, desc in functions:
            frame = tk.Frame(func_container, bg=self.colors['border'])
            frame.pack(fill=tk.X, padx=15, pady=3)

            rb = tk.Radiobutton(frame, text=f" {icon} {value.replace('_', ' ').title()}",
                              variable=self.func_var, value=value,
                              font=('Microsoft YaHei', 10),
                              bg=self.colors['border'], fg='white',
                              selectcolor=self.colors['select_bg'])
            rb.pack(anchor=tk.W, pady=2)

            desc_label = tk.Label(frame, text=f"   {desc}",
                                font=('Microsoft YaHei', 9),
                                fg='#999999', bg=self.colors['border'])
            desc_label.pack(anchor=tk.W, padx=(25, 0), pady=(0, 5))

        # 参数控制
        param_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        param_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(param_container, text="显示参数",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 分辨率
        res_frame = tk.Frame(param_container, bg=self.colors['border'])
        res_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(res_frame, text="网格分辨率:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.res_var = tk.IntVar(value=50)
        tk.Scale(res_frame, from_=20, to=80, variable=self.res_var,
                orient=tk.HORIZONTAL, resolution=5, length=300,
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg']).pack(pady=5)

        # 实时控制
        time_frame = tk.Frame(param_container, bg=self.colors['border'])
        time_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(time_frame, text="时间 T:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.time_var = tk.DoubleVar(value=0)
        self.time_slider = tk.Scale(time_frame, from_=0, to=10,
                                   variable=self.time_var, orient=tk.HORIZONTAL,
                                   resolution=0.01, length=300,
                                   bg=self.colors['border'], fg='white',
                                   troughcolor=self.colors['select_bg'])
        self.time_slider.pack(pady=5)

        self.time_label = tk.Label(time_frame, text="T = 0.00 秒",
                                 font=('Microsoft YaHei', 10, 'bold'),
                                 fg=self.colors['success'], bg=self.colors['border'])
        self.time_label.pack()

    def create_animation_tab(self):
        """动画标签页"""
        anim_frame = ttk.Frame(self.notebook)
        self.notebook.add(anim_frame, text="动画控制")

        # 动画设置
        settings_container = tk.Frame(anim_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        settings_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(settings_container, text="动画设置",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 帧率控制
        fps_frame = tk.Frame(settings_container, bg=self.colors['border'])
        fps_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(fps_frame, text="帧率 (FPS):",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.fps_var = tk.IntVar(value=60)
        tk.Scale(fps_frame, from_=24, to=120, variable=self.fps_var,
                orient=tk.HORIZONTAL, length=300,
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg']).pack(pady=5)

        self.fps_label = tk.Label(fps_frame, text=f"FPS: 60",
                                 font=('Microsoft YaHei', 10, 'bold'),
                                 fg=self.colors['accent'], bg=self.colors['border'])
        self.fps_label.pack()

        # 动画时长
        duration_frame = tk.Frame(settings_container, bg=self.colors['border'])
        duration_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(duration_frame, text="动画时长 (秒):",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.duration_var = tk.DoubleVar(value=5.0)
        tk.Scale(duration_frame, from_=1, to=20, variable=self.duration_var,
                orient=tk.HORIZONTAL, resolution=0.5, length=300,
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg']).pack(pady=5)

        # 控制按钮
        control_container = tk.Frame(anim_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        control_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(control_container, text="播放控制",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        button_frame = tk.Frame(control_container, bg=self.colors['border'])
        button_frame.pack(pady=10)

        self.play_button = tk.Button(button_frame, text="▶ 预渲染并播放",
                                   command=self.start_precached_animation,
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   bg=self.colors['success'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#3E999F',
                                   padx=15, pady=8)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.realtime_button = tk.Button(button_frame, text="⚡ 实时模式",
                                        command=self.start_realtime_animation,
                                        font=('Microsoft YaHei', 10, 'bold'),
                                        bg=self.colors['accent'], fg='white',
                                        relief=tk.FLAT, cursor='hand2',
                                        activebackground='#6BA6CD',
                                        padx=15, pady=8)
        self.realtime_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ 停止",
                                   command=self.stop_animation,
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   bg=self.colors['error'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#D45D5D',
                                   padx=15, pady=8)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def create_cache_tab(self):
        """缓存标签页"""
        cache_frame = ttk.Frame(self.notebook)
        self.notebook.add(cache_frame, text="缓存设置")

        # 缓存设置
        cache_container = tk.Frame(cache_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        cache_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(cache_container, text="缓存管理",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 缓存开关
        cache_enabled_frame = tk.Frame(cache_container, bg=self.colors['border'])
        cache_enabled_frame.pack(fill=tk.X, padx=15, pady=5)

        self.cache_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(cache_enabled_frame, text="启用预渲染缓存",
                      variable=self.cache_enabled_var,
                      font=('Microsoft YaHei', 10),
                      bg=self.colors['border'], fg='white',
                      selectcolor=self.colors['select_bg']).pack(anchor=tk.W)

        # 缓存大小显示
        cache_size_frame = tk.Frame(cache_container, bg=self.colors['border'])
        cache_size_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(cache_size_frame, text="缓存状态:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.cache_status_label = tk.Label(cache_size_frame,
                                         text="  缓存: 空 (0 帧)",
                                         font=('Microsoft YaHei', 10),
                                         fg=self.colors['accent'],
                                         bg=self.colors['border'])
        self.cache_status_label.pack(anchor=tk.W, pady=5)

        # 缓存控制按钮
        cache_control_frame = tk.Frame(cache_container, bg=self.colors['border'])
        cache_control_frame.pack(pady=10)

        tk.Button(cache_control_frame, text="清空缓存",
                 command=self.clear_cache,
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.colors['warning'], fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)

        tk.Button(cache_control_frame, text="预加载",
                 command=self.preload_cache,
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.colors['success'], fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=5)

        # 性能统计
        perf_container = tk.Frame(cache_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        perf_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(perf_container, text="性能统计",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        self.perf_label = tk.Label(perf_container,
                                 text="  实时FPS: --\n  渲染时间: --ms\n  时间偏差: --ms",
                                 font=('Microsoft YaHei', 9),
                                 fg='#CCCCCC', bg=self.colors['border'],
                                 justify=tk.LEFT)
        self.perf_label.pack(anchor=tk.W, padx=15, pady=5)

    def create_display_area(self, parent):
        """显示区域"""
        right_frame = tk.Frame(parent, bg=self.colors['bg'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        plot_container = tk.Frame(right_frame, bg='white', relief=tk.RIDGE, bd=1)
        plot_container.pack(fill=tk.BOTH, expand=True)

        # matplotlib图形
        self.fig = plt.figure(figsize=(10, 8), facecolor='white', dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')

        self.canvas = FigureCanvasTkAgg(self.fig, plot_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar_frame = tk.Frame(right_frame, bg=self.colors['bg'], height=40)
        toolbar_frame.pack(fill=tk.X, pady=(10, 0))

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def create_status_bar(self, parent):
        """状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['select_bg'], height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="✓ 系统就绪",
                                   font=('Microsoft YaHei', 10),
                                   fg='white', bg=self.colors['select_bg'])
        self.status_label.pack(side=tk.LEFT, padx=15, pady=5)

        self.sync_label = tk.Label(status_frame, text="⚡ 同步精度: ±0ms",
                                 font=('Microsoft YaHei', 10),
                                   fg='#4EC9B0', bg=self.colors['select_bg'])
        self.sync_label.pack(side=tk.RIGHT, padx=15, pady=5)

    def setup_plot(self):
        """图形设置"""
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#F8F9FA')

    def update_plot(self):
        """更新图形"""
        try:
            self.ax.clear()

            func_name = self.func_var.get()
            t = self.time_var.get()
            res = self.res_var.get()

            self.time_label.config(text=f"T = {t:.2f} 秒")

            # 获取函数
            functions = {
                "simple_wave": self.simple_wave,
                "radial_wave": self.radial_wave,
                "gaussian_wave": self.gaussian_wave,
                "standing_wave": self.standing_wave
            }
            func = functions.get(func_name, self.simple_wave)

            # 创建网格
            x = np.linspace(-5, 5, res)
            y = np.linspace(-5, 5, res)
            X, Y = np.meshgrid(x, y)
            Z = func(X, Y, t)

            # 绘制
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap=self.current_colormap,
                                       alpha=0.85,
                                       edgecolor='none',
                                       antialiased=True,
                                       shade=True)

            # 坐标轴
            self.ax.set_xlabel('X轴', fontsize=11, fontweight='bold')
            self.ax.set_ylabel('Y轴', fontsize=11, fontweight='bold')
            self.ax.set_zlabel('Z轴', fontsize=11, fontweight='bold')

            title_name = func_name.replace('_', ' ').title()
            self.ax.set_title(f'{title_name} - T = {t:.2f}s',
                            fontsize=13, fontweight='bold', pad=20)

            # 固定范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-2.5, 2.5)

            self.canvas.draw_idle()

        except Exception as e:
            print(f"更新图形出错: {e}")

    # 数学函数
    def simple_wave(self, x, y, t=0):
        return np.sin(x) * np.cos(y + t)

    def radial_wave(self, x, y, t=0):
        r = np.sqrt(x**2 + y**2)
        return np.sin(r - t) * np.exp(-0.1 * r)

    def gaussian_wave(self, x, y, t=0):
        return np.exp(-0.1*(x**2 + y**2)) * np.sin(2*x + t) * np.cos(2*y + t)

    def standing_wave(self, x, y, t=0):
        return np.sin(x) * np.sin(y) * np.cos(t)

    def start_precached_animation(self):
        """预渲染缓存动画"""
        if self.animation_state['running']:
            return

        def precache_and_play():
            try:
                # 更新状态
                self.status_label.config(text="⚙️ 正在预渲染...")
                self.root.update()

                # 获取参数
                fps = self.fps_var.get()
                duration = self.duration_var.get()
                total_frames = int(fps * duration)
                func_name = self.func_var.get()
                res = self.res_var.get()

                # 生成缓存键
                cache_key = f"{func_name}_{res}_{fps}_{duration}"

                # 检查缓存
                if not self.cache_system.has_cache(cache_key):
                    # 预渲染所有帧
                    self.cache_system.precache_frames(
                        func_name, res, fps, duration,
                        progress_callback=lambda p: self.update_cache_progress(p)
                    )

                # 播放缓存动画
                self.animation_state['running'] = True
                self.animation_state['total_frames'] = total_frames
                self.play_cached_animation(cache_key, total_frames, fps)

            except Exception as e:
                self.status_label.config(text=f"✗ 错误: {str(e)}")

        threading.Thread(target=precache_and_play, daemon=True).start()

    def start_realtime_animation(self):
        """实时动画模式"""
        if self.animation_state['running']:
            return

        def realtime_play():
            try:
                self.animation_state['running'] = True
                self.status_label.config(text="▶ 实时播放中...")

                fps = self.fps_var.get()
                duration = self.duration_var.get()
                frame_time = 1.0 / fps

                # 记录开始时间
                real_start_time = time.time()
                self.animation_state['real_start_time'] = real_start_time

                total_frames = int(fps * duration)

                for i in range(total_frames):
                    if not self.animation_state['running']:
                        break

                    # 计算应该的时间点
                    target_time = (i / fps)

                    # 计算实际经过的时间
                    real_elapsed = time.time() - real_start_time

                    # 时间偏差
                    time_diff = real_elapsed - target_time

                    # 更新性能统计
                    self.update_perf_stats(fps, time_diff)

                    # 计算动画时间
                    t = target_time / duration * 10  # 0-10秒范围
                    self.time_var.set(t)

                    # 更新图形
                    self.root.after_idle(self.update_plot)

                    # 精确等待到下一帧时间
                    next_frame_time = real_start_time + ((i + 1) / fps)
                    current_time = time.time()

                    if current_time < next_frame_time:
                        time.sleep(next_frame_time - current_time)

                self.animation_state['running'] = False
                self.status_label.config(text="✓ 动画完成")

            except Exception as e:
                self.status_label.config(text=f"✗ 错误: {str(e)}")
                self.animation_state['running'] = False

        threading.Thread(target=realtime_play, daemon=True).start()

    def play_cached_animation(self, cache_key, total_frames, fps):
        """播放缓存动画 - 在主线程中更新图形"""
        frame_queue = self.cache_system.get_cache(cache_key)
        if not frame_queue:
            self.status_label.config(text="✗ 缓存未找到")
            return

        def animation_loop():
            real_start_time = time.time()
            frame_time = 1.0 / fps

            for i in range(total_frames):
                if not self.animation_state['running']:
                    break

                # 精确时间控制
                target_time = real_start_time + (i * frame_time)
                current_time = time.time()

                # 如果还有时间，等待
                if current_time < target_time:
                    time.sleep(target_time - current_time)

                # 在主线程中显示缓存帧
                if i < len(frame_queue):
                    frame_data = frame_queue[i]
                    self.root.after_idle(self.display_cached_frame, frame_data)

            # 动画完成
            self.root.after(100, lambda: self._animation_complete())

        # 在后台线程中运行时间控制
        threading.Thread(target=animation_loop, daemon=True).start()

    def _animation_complete(self):
        """动画完成回调"""
        self.animation_state['running'] = False
        self.status_label.config(text="✓ 动画完成")

    def display_cached_frame(self, frame_data):
        """显示缓存帧 - 在主线程中绘制"""
        try:
            # 清除当前图形
            self.ax.clear()

            # 设置时间
            self.time_var.set(frame_data['time'])

            # 使用缓存的数据重新绘制
            X = frame_data['X']
            Y = frame_data['Y']
            Z = frame_data['Z']
            func_name = frame_data['func_name']

            # 在主线程中绘制表面
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap=self.current_colormap,
                                       alpha=0.85,
                                       edgecolor='none',
                                       antialiased=True,
                                       shade=True)

            # 设置坐标轴
            self.ax.set_xlabel('X轴', fontsize=11, fontweight='bold')
            self.ax.set_ylabel('Y轴', fontsize=11, fontweight='bold')
            self.ax.set_zlabel('Z轴', fontsize=11, fontweight='bold')

            title_name = func_name.replace('_', ' ').title()
            self.ax.set_title(f'{title_name} - T = {frame_data["time"]:.2f}s',
                            fontsize=13, fontweight='bold', pad=20)

            # 固定范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-2.5, 2.5)

            # 刷新画布
            self.canvas.draw_idle()

        except Exception as e:
            print(f"显示缓存帧出错: {e}")

    def update_cache_progress(self, progress):
        """更新缓存进度"""
        self.status_label.config(text=f"⚙️ 预渲染中: {progress:.1f}%")
        self.root.update()

    def update_perf_stats(self, fps, time_diff):
        """更新性能统计"""
        real_fps = fps * (1 - abs(time_diff) * 0.1)  # 估算实际FPS
        self.perf_label.config(
            text=f"  实时FPS: {real_fps:.1f}\n  时间偏差: {time_diff*1000:.1f}ms"
        )
        self.sync_label.config(text=f"⚡ 同步精度: {time_diff*1000:.1f}ms")

    def stop_animation(self):
        """停止动画"""
        self.animation_state['running'] = False
        self.status_label.config(text="⏹ 已停止")
        self.time_var.set(0)
        self.update_plot()

    def clear_cache(self):
        """清空缓存"""
        self.cache_system.clear_all()
        self.cache_status_label.config(text="  缓存: 空 (0 帧)")
        self.status_label.config(text="✓ 缓存已清空")

    def preload_cache(self):
        """预加载缓存"""
        self.status_label.config(text="⚙️ 正在预加载...")
        threading.Thread(target=self._preload_worker, daemon=True).start()

    def _preload_worker(self):
        """预加载工作线程"""
        try:
            fps = self.fps_var.get()
            duration = self.duration_var.get()
            func_name = self.func_var.get()
            res = self.res_var.get()

            cache_key = f"{func_name}_{res}_{fps}_{duration}"
            self.cache_system.precache_frames(func_name, res, fps, duration)

            frame_count = self.cache_system.get_cache_size(cache_key)
            self.cache_status_label.config(text=f"  缓存: {cache_key} ({frame_count} 帧)")
            self.status_label.config(text="✓ 预加载完成")
        except Exception as e:
            self.status_label.config(text=f"✗ 预加载失败: {str(e)}")

    def run(self):
        """运行"""
        self.root.mainloop()


class CacheSystem:
    """缓存系统"""
    def __init__(self):
        self.cache = {}
        self.cache_dir = "animation_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def has_cache(self, key):
        """检查是否有缓存"""
        return key in self.cache

    def get_cache(self, key):
        """获取缓存"""
        return self.cache.get(key)

    def get_cache_size(self, key):
        """获取缓存大小"""
        cache = self.cache.get(key)
        return len(cache) if cache else 0

    def precache_frames(self, func_name, resolution, fps, duration, progress_callback=None):
        """预渲染帧 - 只缓存数据，不创建图形"""
        cache_key = f"{func_name}_{resolution}_{fps}_{duration}"
        total_frames = int(fps * duration)
        frames = []

        # 获取函数
        functions = {
            "simple_wave": lambda x, y, t: np.sin(x) * np.cos(y + t),
            "radial_wave": lambda x, y, t: np.sin(np.sqrt(x**2 + y**2) - t) * np.exp(-0.1 * np.sqrt(x**2 + y**2)),
            "gaussian_wave": lambda x, y, t: np.exp(-0.1*(x**2 + y**2)) * np.sin(2*x + t) * np.cos(2*y + t),
            "standing_wave": lambda x, y, t: np.sin(x) * np.sin(y) * np.cos(t)
        }
        func = functions.get(func_name, functions["simple_wave"])

        # 创建网格（只计算一次）
        x = np.linspace(-5, 5, resolution)
        y = np.linspace(-5, 5, resolution)
        X, Y = np.meshgrid(x, y)

        print(f"开始预渲染 {total_frames} 帧...")

        # 预渲染每一帧的数据
        for i in range(total_frames):
            t = (i / total_frames) * 10  # 0-10秒范围

            # 只计算Z数据，不创建图形
            Z = func(X, Y, t)

            # 保存帧数据（只保存数据，不保存图形对象）
            frame_data = {
                'time': t,
                'X': X.copy(),  # 保存网格数据
                'Y': Y.copy(),
                'Z': Z.copy(),  # 保存计算结果
                'func_name': func_name
            }
            frames.append(frame_data)

            # 更新进度
            if progress_callback and i % max(1, total_frames // 20) == 0:  # 每5%更新一次
                progress = (i / total_frames) * 100
                progress_callback(progress)
                print(f"预渲染进度: {progress:.1f}%")

        print(f"预渲染完成，共缓存 {len(frames)} 帧")

        # 保存到缓存
        self.cache[cache_key] = frames

    def clear_all(self):
        """清空所有缓存"""
        self.cache.clear()


class TimeSync:
    """时间同步系统"""
    def __init__(self):
        self.start_time = 0
        self.target_fps = 60

    def sync_frame(self, frame_index):
        """同步帧时间"""
        current_time = time.time()
        target_time = self.start_time + (frame_index / self.target_fps)

        if current_time < target_time:
            time.sleep(target_time - current_time)

        return current_time - target_time


if __name__ == "__main__":
    app = RealtimeGUI()
    app.run()