"""
优化版动态表面分析系统
解决时间同步问题 + 更多函数模板 + 性能优化
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import threading
import time
from collections import deque
import queue

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class OptimizedGUI:
    def __init__(self):
        # 设置退出标志
        self.is_running = True

        # DPI感知
        self.setup_dpi_awareness()

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("动态表面分析系统 - 优化版")

        # 窗口设置
        self.setup_window()

        # 绑定关闭事件
        self.setup_close_handler()

        # 样式设置
        self.setup_modern_style()

        # 性能优化设置
        self.setup_performance_optimization()

        # 创建UI
        self.setup_ui()

        # 初始化图形
        self.setup_plot()

        # 动画控制
        self.animation_state = {
            'running': False,
            'paused': False,
            'thread': None,
            'fps': 60,
            'duration': 5.0,
            'start_real_time': 0,
            'target_duration': 5.0,  # 目标播放时长
            'frame_skip_threshold': 0.016  # 帧跳过阈值(16ms)
        }

        # 渲染缓存
        self.render_cache = {}
        self.current_resolution = 50

        # 当前设置
        self.current_colormap = 'viridis'
        self.colormaps = ['viridis', 'plasma', 'coolwarm', 'magma', 'ocean', 'twilight', 'turbo', 'rainbow']

        # 更新队列
        self.update_queue = queue.Queue(maxsize=2)  # 限制队列大小防止堆积

        # 初始显示
        self.update_plot_async()

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

    def setup_close_handler(self):
        """设置窗口关闭事件处理"""
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 绑定Alt+F4快捷键
        self.root.bind('<Alt-F4>', lambda e: self.on_close())

        # 绑定Ctrl+Q快捷键
        self.root.bind('<Control-q>', lambda e: self.on_close())
        self.root.bind('<Control-Q>', lambda e: self.on_close())

    def on_close(self):
        """窗口关闭事件处理"""
        print("正在关闭程序...")

        try:
            # 1. 停止所有动画
            self.animation_state['running'] = False

            # 2. 等待动画线程结束
            if self.animation_state['thread'] and self.animation_state['thread'].is_alive():
                print("等待动画线程结束...")
                self.animation_state['thread'].join(timeout=1.0)  # 最多等待1秒

            # 3. 清空更新队列
            while not self.update_queue.empty():
                try:
                    self.update_queue.get_nowait()
                except queue.Empty:
                    break

            # 4. 关闭matplotlib图形
            try:
                plt.close('all')  # 关闭所有matplotlib图形
            except:
                pass

            # 5. 清理缓存
            self.render_cache.clear()

            # 6. 设置退出标志
            self.is_running = False

            print("清理完成，正在退出...")

            # 7. 销毁窗口
            self.root.quit()
            self.root.destroy()

        except Exception as e:
            print(f"关闭时出错: {e}")
            # 强制退出
            self.root.quit()
            self.root.destroy()

        # 8. 确保进程退出
        import os
        import sys
        sys.exit(0)

    def setup_modern_style(self):
        """样式设置"""
        self.style = ttk.Style()

        # 颜色方案
        self.colors = {
            'bg': '#1A1A1A',
            'fg': '#FFFFFF',
            'select_bg': '#2E7D32',
            'hover_bg': '#388E3C',
            'border': '#2D2D30',
            'accent': '#1976D2',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336'
        }

        self.root.configure(bg=self.colors['bg'])
        self.style.theme_use('default')

    def setup_performance_optimization(self):
        """性能优化设置"""
        # matplotlib性能优化
        plt.rcParams['figure.max_open_warning'] = 0
        plt.rcParams['agg.path.chunksize'] = 10000

        # 渲染质量平衡
        self.render_quality = {
            'low': {'rcount': 20, 'ccount': 20, 'alpha': 0.9},
            'medium': {'rcount': 30, 'ccount': 30, 'alpha': 0.85},
            'high': {'rcount': 40, 'ccount': 40, 'alpha': 0.8}
        }

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

        title_label = tk.Label(header_frame, text="动态表面分析系统 - 优化版",
                             font=('Microsoft YaHei', 16, 'bold'),
                             fg='white', bg=self.colors['select_bg'])
        title_label.pack(side=tk.LEFT, padx=30, pady=12)

        perf_label = tk.Label(header_frame, text="⚡ 高性能渲染",
                            font=('Microsoft YaHei', 11),
                            fg='#4CAF50', bg=self.colors['select_bg'])
        perf_label.pack(side=tk.RIGHT, padx=30, pady=12)

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
        self.create_performance_tab()

    def create_function_tab(self):
        """函数标签页"""
        func_frame = ttk.Frame(self.notebook)
        self.notebook.add(func_frame, text="函数选择")

        # 函数选择区域
        func_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        func_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(func_container, text="选择数学函数",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 函数选项 - 添加更多函数
        self.func_var = tk.StringVar(value="simple_wave")
        functions = [
            # 基础波形
            ("● 简单波", "simple_wave", "基础正弦波形"),
            ("○ 径向波", "radial_wave", "同心圆扩散波"),

            # 调制波
            ("★ 高斯波包", "gaussian_wave", "高斯调制波形"),
            ("† 驻波", "standing_wave", "固定振动模式"),

            # 渐变类
            ("▷ 线性渐变", "linear_gradient", "线性方向渐变"),
            ("◁ 径向渐变", "radial_gradient", "径向距离渐变"),
            ("◇ 棋盘格", "checkerboard", "棋盘格图案"),

            # 复杂波形
            ("∞ 螺旋波", "spiral_wave", "螺旋波形"),
            ("⚡ 干涉图样", "interference_pattern", "多波干涉"),
            ("☁ 噪声场", "noise_field", "随机噪声场"),

            # 多项式类
            ("∛ 多项式曲面", "polynomial_surface", "三次多项式曲面"),
            ("∫ 鞍形点", "saddle_point", "马鞍形曲面")
        ]

        # 分组显示
        categories = [
            ("基础波形", functions[:2]),
            ("调制波形", functions[2:4]),
            ("渐变图案", functions[4:7]),
            ("复杂波场", functions[7:10]),
            ("数学曲面", functions[10:])
        ]

        for category, cat_functions in categories:
            # 分组标题
            cat_label = tk.Label(func_container, text=f"【{category}】",
                               font=('Microsoft YaHei', 9, 'bold'),
                               fg='#81C784', bg=self.colors['border'])
            cat_label.pack(anchor=tk.W, padx=20, pady=(10, 5))

            # 分组函数
            for icon, value, desc in cat_functions:
                frame = tk.Frame(func_container, bg=self.colors['border'])
                frame.pack(fill=tk.X, padx=25, pady=2)

                rb = tk.Radiobutton(frame, text=f" {icon} {value.replace('_', ' ').title()}",
                                  variable=self.func_var, value=value,
                                  command=lambda: self.update_plot_async(),
                                  font=('Microsoft YaHei', 9),
                                  bg=self.colors['border'], fg='white',
                                  selectcolor=self.colors['select_bg'])
                rb.pack(anchor=tk.W, pady=1)

                desc_label = tk.Label(frame, text=f"     {desc}",
                                    font=('Microsoft YaHei', 8),
                                    fg='#999999', bg=self.colors['border'])
                desc_label.pack(anchor=tk.W, padx=(20, 0), pady=(0, 3))

        # 参数控制
        param_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        param_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(param_container, text="显示参数",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        # 分辨率控制
        res_frame = tk.Frame(param_container, bg=self.colors['border'])
        res_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(res_frame, text="渲染分辨率:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.res_var = tk.IntVar(value=50)
        res_scale = tk.Scale(res_frame, from_=20, to=100, variable=self.res_var,
                           orient=tk.HORIZONTAL, resolution=10, length=280,
                           bg=self.colors['border'], fg='white',
                           troughcolor=self.colors['select_bg'],
                           command=lambda v: self.update_plot_async())
        res_scale.pack(pady=5)

        self.res_label = tk.Label(res_frame, text="网格: 50×50",
                                font=('Microsoft YaHei', 10),
                                fg='#CCCCCC', bg=self.colors['border'])
        self.res_label.pack()

        # 实时时间控制
        time_frame = tk.Frame(param_container, bg=self.colors['border'])
        time_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(time_frame, text="时间参数 T:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.time_var = tk.DoubleVar(value=0)
        time_scale = tk.Scale(time_frame, from_=0, to=10,
                            variable=self.time_var, orient=tk.HORIZONTAL,
                            resolution=0.01, length=280,
                            bg=self.colors['border'], fg='white',
                            troughcolor=self.colors['select_bg'],
                            command=lambda v: self.update_plot_async())
        time_scale.pack(pady=5)

        self.time_label = tk.Label(time_frame, text="T = 0.00 秒",
                                 font=('Microsoft YaHei', 10, 'bold'),
                                 fg='#4CAF50', bg=self.colors['border'])
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

        tk.Label(fps_frame, text="播放帧率 (FPS):",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.fps_var = tk.IntVar(value=60)
        tk.Scale(fps_frame, from_=15, to=120, variable=self.fps_var,
                orient=tk.HORIZONTAL, length=280,
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg']).pack(pady=5)

        self.fps_label = tk.Label(fps_frame, text=f"FPS: 60",
                                 font=('Microsoft YaHei', 10, 'bold'),
                                 fg='#1976D2', bg=self.colors['border'])
        self.fps_label.pack()

        # 动画时长
        duration_frame = tk.Frame(settings_container, bg=self.colors['border'])
        duration_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(duration_frame, text="动画时长 (秒):",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.duration_var = tk.DoubleVar(value=5.0)
        tk.Scale(duration_frame, from_=1, to=30, variable=self.duration_var,
                orient=tk.HORIZONTAL, resolution=0.5, length=280,
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg']).pack(pady=5)

        # 同步模式
        sync_frame = tk.Frame(settings_container, bg=self.colors['border'])
        sync_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(sync_frame, text="时间同步模式:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.sync_mode = tk.StringVar(value="frame_skip")
        tk.Radiobutton(sync_frame, text="帧跳跃模式 (跳过慢帧)",
                      variable=self.sync_mode, value="frame_skip",
                      font=('Microsoft YaHei', 9),
                      bg=self.colors['border'], fg='white',
                      selectcolor=self.colors['select_bg']).pack(anchor=tk.W, padx=20)
        tk.Radiobutton(sync_frame, text="补偿模式 (延长下一帧)",
                      variable=self.sync_mode, value="compensate",
                      font=('Microsoft YaHei', 9),
                      bg=self.colors['border'], fg='white',
                      selectcolor=self.colors['select_bg']).pack(anchor=tk.W, padx=20)

        # 控制按钮
        control_container = tk.Frame(anim_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        control_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(control_container, text="播放控制",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        button_frame = tk.Frame(control_container, bg=self.colors['border'])
        button_frame.pack(pady=10)

        self.play_button = tk.Button(button_frame, text="▶ 播放",
                                   command=self.start_animation,
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   bg=self.colors['success'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#45A049',
                                   padx=20, pady=8)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ 停止",
                                   command=self.stop_animation,
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   bg=self.colors['error'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#D32F2F',
                                   padx=20, pady=8)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def create_performance_tab(self):
        """性能标签页"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="性能优化")

        # 渲染质量
        quality_container = tk.Frame(perf_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        quality_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(quality_container, text="渲染质量",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        self.quality_var = tk.StringVar(value="medium")
        qualities = [
            ("低质量 (最快)", "low", "60FPS+ 实时渲染"),
            ("中等质量 (推荐)", "medium", "30-60FPS 平衡"),
            ("高质量 (较慢)", "high", "15-30FPS 最佳效果")
        ]

        for name, value, desc in qualities:
            frame = tk.Frame(quality_container, bg=self.colors['border'])
            frame.pack(fill=tk.X, padx=15, pady=3)

            rb = tk.Radiobutton(frame, text=name,
                              variable=self.quality_var, value=value,
                              command=self.update_plot_async,
                              font=('Microsoft YaHei', 10),
                              bg=self.colors['border'], fg='white',
                              selectcolor=self.colors['select_bg'])
            rb.pack(anchor=tk.W)

            desc_label = tk.Label(frame, text=f"   {desc}",
                                font=('Microsoft YaHei', 9),
                                fg='#999999', bg=self.colors['border'])
            desc_label.pack(anchor=tk.W, padx=(20, 0), pady=(0, 5))

        # 配色方案
        color_container = tk.Frame(perf_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        color_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(color_container, text="配色方案",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        self.colormap_var = tk.StringVar(value="viridis")
        colormap_frame = tk.Frame(color_container, bg=self.colors['border'])
        colormap_frame.pack(fill=tk.X, padx=15, pady=5)

        # 配色方案选择
        colormap_options = [
            ("viridis", "紫绿渐变"),
            ("plasma", "紫红渐变"),
            ("coolwarm", "冷暖渐变"),
            ("magma", "岩浆色"),
            ("ocean", "海洋色"),
            ("turbo", "彩虹色")
        ]

        for value, name in colormap_options:
            tk.Radiobutton(colormap_frame, text=name,
                          variable=self.colormap_var, value=value,
                          command=self.update_colormap,
                          font=('Microsoft YaHei', 9),
                          bg=self.colors['border'], fg='white',
                          selectcolor=self.colors['select_bg']).pack(anchor=tk.W)

        # 性能统计
        stats_container = tk.Frame(perf_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        stats_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(stats_container, text="性能统计",
                font=('Microsoft YaHei', 11, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=10)

        self.stats_label = tk.Label(stats_container,
                                  text="  实时FPS: --\n  渲染时间: --ms\n  帧延迟: --ms",
                                  font=('Microsoft YaHei', 9),
                                  fg='#CCCCCC', bg=self.colors['border'],
                                  justify=tk.LEFT)
        self.stats_label.pack(anchor=tk.W, padx=15, pady=5)

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

        self.sync_label = tk.Label(status_frame, text="⏱️ 同步模式: 帧跳跃",
                                 font=('Microsoft YaHei', 10),
                                   fg='#FFC107', bg=self.colors['select_bg'])
        self.sync_label.pack(side=tk.RIGHT, padx=15, pady=5)

    def setup_plot(self):
        """图形设置"""
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#F8F9FA')

    def update_plot_async(self):
        """异步更新图形"""
        # 防止重复更新
        if not self.update_queue.empty():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                pass

        # 添加更新任务到队列
        try:
            self.update_queue.put_nowait(True)
            # 使用after延迟执行，避免阻塞
            self.root.after(10, self._update_plot_worker)
        except queue.Full:
            pass  # 队列满，跳过这次更新

    def _update_plot_worker(self):
        """实际更新图形的工作函数"""
        try:
            # 清空队列中的旧任务
            while not self.update_queue.empty():
                try:
                    self.update_queue.get_nowait()
                except queue.Empty:
                    break

            # 执行更新
            self._update_plot()

        except Exception as e:
            print(f"更新图形错误: {e}")

    def _update_plot(self):
        """实际的图形更新"""
        start_time = time.time()

        try:
            # 清除当前图形
            self.ax.clear()

            # 获取参数
            func_name = self.func_var.get()
            t = self.time_var.get()
            res = self.res_var.get()
            quality = self.quality_var.get()

            # 更新分辨率缓存
            if res != self.current_resolution:
                self.current_resolution = res
                self.render_cache.clear()  # 清除缓存

            # 更新标签
            self.time_label.config(text=f"T = {t:.2f} 秒")
            self.res_label.config(text=f"网格: {res}×{res}")
            self.fps_label.config(text=f"FPS: {self.fps_var.get()}")
            self.sync_label.config(text=f"⏱️ 同步模式: {'帧跳跃' if self.sync_mode.get() == 'frame_skip' else '补偿'}")

            # 获取函数
            func = self.get_function(func_name)

            # 创建网格（可以使用缓存）
            cache_key = f"grid_{res}"
            if cache_key in self.render_cache:
                X, Y = self.render_cache[cache_key]
            else:
                x = np.linspace(-5, 5, res)
                y = np.linspace(-5, 5, res)
                X, Y = np.meshgrid(x, y)
                self.render_cache[cache_key] = (X, Y)

            # 计算Z值
            Z = func(X, Y, t)

            # 获取渲染质量设置
            qual_settings = self.render_quality[quality]

            # 绘制表面（优化质量）
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap=self.current_colormap,
                                       alpha=qual_settings['alpha'],
                                       edgecolor='none',
                                       antialiased=True,
                                       shade=True,
                                       rcount=qual_settings['rcount'],
                                       ccount=qual_settings['ccount'])

            # 设置坐标轴
            self.ax.set_xlabel('X轴', fontsize=11, fontweight='bold')
            self.ax.set_ylabel('Y轴', fontsize=11, fontweight='bold')
            self.ax.set_zlabel('Z轴', fontsize=11, fontweight='bold')

            title_name = func_name.replace('_', ' ').title()
            self.ax.set_title(f'{title_name} - T = {t:.2f}s',
                            fontsize=13, fontweight='bold', pad=20)

            # 固定范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-3, 3)

            # 刷新画布
            self.canvas.draw_idle()

            # 更新性能统计
            render_time = (time.time() - start_time) * 1000
            self.update_stats(render_time)

        except Exception as e:
            print(f"更新图形出错: {e}")

    def get_function(self, func_name):
        """获取函数"""
        functions = {
            "simple_wave": self.simple_wave,
            "radial_wave": self.radial_wave,
            "gaussian_wave": self.gaussian_wave,
            "standing_wave": self.standing_wave,
            "linear_gradient": self.linear_gradient,
            "radial_gradient": self.radial_gradient,
            "checkerboard": self.checkerboard,
            "spiral_wave": self.spiral_wave,
            "interference_pattern": self.interference_pattern,
            "noise_field": self.noise_field,
            "polynomial_surface": self.polynomial_surface,
            "saddle_point": self.saddle_point
        }
        return functions.get(func_name, self.simple_wave)

    # 数学函数定义
    def simple_wave(self, x, y, t=0):
        """简单波形"""
        return np.sin(x) * np.cos(y + t)

    def radial_wave(self, x, y, t=0):
        """径向波"""
        r = np.sqrt(x**2 + y**2)
        return np.sin(r - t) * np.exp(-0.1 * r)

    def gaussian_wave(self, x, y, t=0):
        """高斯波包"""
        return np.exp(-0.1*(x**2 + y**2)) * np.sin(2*x + t) * np.cos(2*y + t)

    def standing_wave(self, x, y, t=0):
        """驻波"""
        return np.sin(x) * np.sin(y) * np.cos(t)

    def linear_gradient(self, x, y, t=0):
        """线性渐变"""
        return 0.5 * (x + y) * np.sin(t)

    def radial_gradient(self, x, y, t=0):
        """径向渐变"""
        r = np.sqrt(x**2 + y**2)
        return (r / 5) * np.cos(t + r)

    def checkerboard(self, x, y, t=0):
        """棋盘格"""
        size = 2
        return np.sin(x * size + t) * np.sin(y * size + t)

    def spiral_wave(self, x, y, t=0):
        """螺旋波"""
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        return np.sin(2*theta + r - t) * np.exp(-0.1 * r)

    def interference_pattern(self, x, y, t=0):
        """干涉图样"""
        source1 = np.sin(np.sqrt((x-2)**2 + y**2) - t)
        source2 = np.sin(np.sqrt((x+2)**2 + y**2) - t)
        return (source1 + source2) / 2

    def noise_field(self, x, y, t=0):
        """噪声场"""
        np.random.seed(int(t * 100))
        noise = np.random.randn(*x.shape) * 0.3
        return np.sin(x + t) * np.cos(y + t) + noise

    def polynomial_surface(self, x, y, t=0):
        """多项式曲面"""
        return (x**3 - 3*x*y**2) / 10 * np.sin(t)

    def saddle_point(self, x, y, t=0):
        """鞍形点"""
        return (x**2 - y**2) / 5 * np.cos(t)

    def update_colormap(self):
        """更新配色方案"""
        self.current_colormap = self.colormap_var.get()
        self.update_plot_async()

    def update_stats(self, render_time):
        """更新性能统计"""
        fps_text = f"{1000/render_time:.1f}" if render_time > 0 else "--"
        self.stats_label.config(
            text=f"  实时FPS: {fps_text}\n  渲染时间: {render_time:.1f}ms\n  帧延迟: {max(0, render_time-16.7):.1f}ms"
        )

    def start_animation(self):
        """开始动画 - 优化时间同步"""
        if self.animation_state['running']:
            return

        def optimized_animation():
            try:
                self.animation_state['running'] = True
                self.status_label.config(text="▶ 动画播放中...")

                fps = self.fps_var.get()
                duration = self.duration_var.get()
                sync_mode = self.sync_mode.get()

                frame_time = 1.0 / fps
                total_frames = int(fps * duration)

                # 记录开始时间
                real_start_time = time.time()

                for i in range(total_frames):
                    # 检查程序是否正在关闭
                    if not self.is_running or not self.animation_state['running']:
                        print("动画线程检测到关闭信号，正在退出...")
                        break

                    # 计算目标时间点
                    target_time = real_start_time + (i * frame_time)

                    # 计算动画时间
                    anim_t = (i / total_frames) * 10

                    # 渲染时间
                    render_start = time.time()

                    # 更新时间变量
                    self.time_var.set(anim_t)

                    # 异步更新图形
                    self.update_plot_async()

                    render_end = time.time()
                    render_duration = render_end - render_start

                    # 时间同步处理
                    current_time = time.time()

                    if sync_mode == "frame_skip":
                        # 帧跳跃模式：如果渲染太慢，跳过这一帧
                        if current_time > target_time + frame_time:
                            print(f"跳过帧 {i}, 延迟: {(current_time - target_time) * 1000:.1f}ms")
                            continue
                    else:
                        # 补偿模式：延长下一帧的时间来补偿
                        if current_time < target_time:
                            # 等待到目标时间
                            time.sleep(target_time - current_time)

                print("动画播放完成")
                self.animation_state['running'] = False
                if self.is_running:  # 只有在程序还在运行时才更新状态
                    self.status_label.config(text="✓ 动画完成")

            except Exception as e:
                print(f"动画错误: {e}")
                self.animation_state['running'] = False
                if self.is_running:
                    self.status_label.config(text=f"✗ 动画错误: {str(e)}")

        # 在后台线程中运行动画（非daemon，确保能正确关闭）
        self.animation_state['thread'] = threading.Thread(target=optimized_animation)
        self.animation_state['thread'].start()

    def stop_animation(self):
        """停止动画"""
        self.animation_state['running'] = False
        if self.is_running:
            self.status_label.config(text="⏹ 已停止")
        self.time_var.set(0)
        self.update_plot_async()

    def run(self):
        """运行"""
        try:
            print("程序启动完成")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n检测到中断信号，正在关闭...")
            self.on_close()
        except Exception as e:
            print(f"运行时错误: {e}")
            self.on_close()
        finally:
            print("程序已退出")

if __name__ == "__main__":
    app = OptimizedGUI()
    app.run()