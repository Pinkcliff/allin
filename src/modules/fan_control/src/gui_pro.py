"""
专业版动态表面分析系统 - 高性能美优界面
支持DPI自适应、高帧率动画、精美字体
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import threading
import time
from matplotlib import cm

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ProGUI:
    def __init__(self):
        # 设置DPI感知
        self.setup_dpi_awareness()

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("动态表面分析系统 Pro")

        # 设置窗口大小和位置（自适应屏幕）
        self.setup_window()

        # 设置现代化样式
        self.setup_modern_style()

        # 创建UI
        self.setup_ui()

        # 初始化3D图形
        self.setup_plot()

        # 动画控制
        self.animation_running = False
        self.animation_thread = None

        # 当前设置
        self.current_colormap = 'viridis'
        self.colormaps = ['viridis', 'plasma', 'coolwarm', 'magma', 'ocean', 'twilight']

        # 初始显示
        self.update_plot()

    def setup_dpi_awareness(self):
        """设置DPI感知，让界面不受分辨率影响"""
        try:
            import ctypes
            # Windows DPI感知设置
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    def setup_window(self):
        """设置窗口大小和位置"""
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 设置合适的窗口大小
        window_width = min(1400, int(screen_width * 0.85))
        window_height = min(900, int(screen_height * 0.85))

        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 700)

    def setup_modern_style(self):
        """设置现代化样式"""
        # 创建样式
        self.style = ttk.Style()

        # 配置颜色方案
        self.colors = {
            'bg': '#2B2B2B',
            'fg': '#FFFFFF',
            'select_bg': '#4A90E2',
            'hover_bg': '#5A9F3F',
            'border': '#3C3F41',
            'accent': '#61DAFB',
            'success': '#4CAF50',
            'warning': '#FFC107',
            'error': '#F44336'
        }

        # 设置主窗口背景
        self.root.configure(bg=self.colors['bg'])

        # 配置各种控件样式
        self.style.theme_use('default')

        # Frame样式
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Dark.TFrame', background=self.colors['bg'])

        # Label样式
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('Title.TLabel', background=self.colors['bg'], foreground='#FFFFFF',
                           font=('Microsoft YaHei', 14, 'bold'))
        self.style.configure('Info.TLabel', background=self.colors['bg'], foreground='#CCCCCC',
                           font=('Microsoft YaHei', 10))

        # Button样式
        self.style.configure('Modern.TButton',
                           background=self.colors['select_bg'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Microsoft YaHei', 10, 'bold'),
                           padding=(20, 8))

        self.style.map('Modern.TButton',
                      background=[('active', self.colors['hover_bg'])])

        # Notebook样式
        self.style.configure('Modern.TNotebook',
                           background=self.colors['bg'],
                           borderwidth=0)

        self.style.configure('Modern.TNotebook.Tab',
                           background=self.colors['border'],
                           foreground='#CCCCCC',
                           padding=(30, 12),
                           font=('Microsoft YaHei', 10, 'bold'))

        self.style.map('Modern.TNotebook.Tab',
                      background=[('selected', self.colors['select_bg'])],
                      foreground=[('selected', 'white')])

    def setup_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 标题区域
        self.create_header(main_container)

        # 内容区域
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 左侧控制面板
        self.create_control_panel(content_frame)

        # 右侧显示区域
        self.create_display_area(content_frame)

        # 状态栏
        self.create_status_bar(main_container)

    def create_header(self, parent):
        """创建标题区域"""
        header_frame = tk.Frame(parent, bg=self.colors['select_bg'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # 标题文本
        title_label = tk.Label(header_frame, text="动态表面分析系统",
                             font=('Microsoft YaHei', 20, 'bold'),
                             fg='white', bg=self.colors['select_bg'])
        title_label.pack(side=tk.LEFT, padx=30, pady=15)

        # 版本信息
        version_label = tk.Label(header_frame, text="Pro Edition v2.0",
                               font=('Microsoft YaHei', 12),
                               fg='#B0BEC5', bg=self.colors['select_bg'])
        version_label.pack(side=tk.RIGHT, padx=30, pady=15)

    def create_control_panel(self, parent):
        """创建控制面板"""
        # 左侧面板容器
        left_frame = tk.Frame(parent, bg=self.colors['bg'], width=380)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_frame.pack_propagate(False)

        # 创建Notebook
        self.notebook = ttk.Notebook(left_frame, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建标签页
        self.create_function_tab()
        self.create_parameter_tab()
        self.create_animation_tab()

    def create_function_tab(self):
        """函数选择标签页"""
        func_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(func_frame, text="函数选择")

        # 函数选择区域
        func_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        func_container.pack(fill=tk.X, padx=10, pady=10)

        # 标题
        title_label = tk.Label(func_container, text="选择数学函数",
                             font=('Microsoft YaHei', 12, 'bold'),
                             fg='white', bg=self.colors['border'])
        title_label.pack(pady=(15, 10))

        # 函数选项
        self.func_var = tk.StringVar(value="simple_wave")
        functions = [
            ("● 简单波", "simple_wave", "基础正弦波形"),
            ("○ 径向波", "radial_wave", "同心圆扩散波"),
            ("★ 高斯波包", "gaussian_wave", "高斯调制波"),
            ("‖ 驻波", "standing_wave", "固定振动模式")
        ]

        for icon, value, desc in functions:
            # 函数选项框
            option_frame = tk.Frame(func_container, bg=self.colors['border'])
            option_frame.pack(fill=tk.X, padx=15, pady=5)

            # 单选按钮
            rb = tk.Radiobutton(option_frame, text=f" {icon} {value.replace('_', ' ').title()}",
                              variable=self.func_var, value=value,
                              command=self.update_plot,
                              font=('Microsoft YaHei', 11),
                              bg=self.colors['border'], fg='white',
                              selectcolor=self.colors['select_bg'],
                              activebackground=self.colors['hover_bg'])
            rb.pack(anchor=tk.W, pady=2)

            # 描述文本
            desc_label = tk.Label(option_frame, text=f"   {desc}",
                                font=('Microsoft YaHei', 9),
                                fg='#999999', bg=self.colors['border'])
            desc_label.pack(anchor=tk.W, padx=(25, 0), pady=(0, 8))

        # 快速操作区域
        quick_container = tk.Frame(func_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        quick_container.pack(fill=tk.X, padx=10, pady=10)

        quick_title = tk.Label(quick_container, text="快速操作",
                             font=('Microsoft YaHei', 12, 'bold'),
                             fg='white', bg=self.colors['border'])
        quick_title.pack(pady=(15, 10))

        # 操作按钮
        buttons = [
            ("▶ 自动演示", self.auto_demo),
            ("[色彩] 切换配色", self.change_colormap),
            ("[相机] 保存截图", self.save_screenshot),
            ("[重置] 重置视图", self.reset_view)
        ]

        for text, command in buttons:
            btn = tk.Button(quick_container, text=text,
                          command=command,
                          font=('Microsoft YaHei', 10, 'bold'),
                          bg=self.colors['select_bg'], fg='white',
                          relief=tk.FLAT, cursor='hand2',
                          activebackground=self.colors['hover_bg'])
            btn.pack(fill=tk.X, padx=15, pady=3)

    def create_parameter_tab(self):
        """参数控制标签页"""
        param_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(param_frame, text="参数控制")

        # 时间控制
        time_container = tk.Frame(param_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        time_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(time_container, text="时间控制",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=(15, 10))

        # 时间滑块
        self.time_var = tk.DoubleVar(value=0)
        time_frame = tk.Frame(time_container, bg=self.colors['border'])
        time_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(time_frame, text="时间 T:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.time_slider = tk.Scale(time_frame, from_=0, to=10,
                                   variable=self.time_var, orient=tk.HORIZONTAL,
                                   resolution=0.01, length=300,
                                   command=lambda e: self.update_plot(),
                                   bg=self.colors['border'], fg='white',
                                   troughcolor=self.colors['select_bg'],
                                   activebackground=self.colors['hover_bg'],
                                   highlightthickness=0)
        self.time_slider.pack(pady=5)

        self.time_label = tk.Label(time_container, text="T = 0.00 秒",
                                 font=('Microsoft YaHei', 11, 'bold'),
                                 fg=self.colors['success'], bg=self.colors['border'])
        self.time_label.pack(pady=(0, 10))

        # 显示参数
        display_container = tk.Frame(param_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        display_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(display_container, text="显示参数",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=(15, 10))

        # 分辨率
        res_frame = tk.Frame(display_container, bg=self.colors['border'])
        res_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(res_frame, text="网格分辨率:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.res_var = tk.IntVar(value=50)
        self.res_slider = tk.Scale(res_frame, from_=20, to=100,
                                  variable=self.res_var, orient=tk.HORIZONTAL,
                                  resolution=5, length=300,
                                  command=lambda e: self.update_plot(),
                                  bg=self.colors['border'], fg='white',
                                  troughcolor=self.colors['select_bg'],
                                  highlightthickness=0)
        self.res_slider.pack(pady=5)

        self.res_label = tk.Label(res_frame, text="分辨率: 50×50",
                                 font=('Microsoft YaHei', 10),
                                 fg='#CCCCCC', bg=self.colors['border'])
        self.res_label.pack()

        # 视角控制
        view_container = tk.Frame(param_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        view_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(view_container, text="视角控制",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=(15, 10))

        # 仰角
        elev_frame = tk.Frame(view_container, bg=self.colors['border'])
        elev_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(elev_frame, text="仰角:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.elev_var = tk.IntVar(value=30)
        tk.Scale(elev_frame, from_=0, to=90, variable=self.elev_var,
                orient=tk.HORIZONTAL, length=300,
                command=lambda e: self.update_plot(),
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg'],
                highlightthickness=0).pack(pady=5)

        # 方位角
        azim_frame = tk.Frame(view_container, bg=self.colors['border'])
        azim_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(azim_frame, text="方位角:",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.azim_var = tk.IntVar(value=45)
        tk.Scale(azim_frame, from_=0, to=360, variable=self.azim_var,
                orient=tk.HORIZONTAL, length=300,
                command=lambda e: self.update_plot(),
                bg=self.colors['border'], fg='white',
                troughcolor=self.colors['select_bg'],
                highlightthickness=0).pack(pady=5)

    def create_animation_tab(self):
        """动画控制标签页"""
        anim_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(anim_frame, text="动画控制")

        # 动画设置
        settings_container = tk.Frame(anim_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        settings_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(settings_container, text="动画设置",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=(15, 10))

        # 帧率设置 - 默认60FPS
        fps_frame = tk.Frame(settings_container, bg=self.colors['border'])
        fps_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(fps_frame, text="帧率 (FPS):",
                font=('Microsoft YaHei', 10),
                fg='#CCCCCC', bg=self.colors['border']).pack(anchor=tk.W)

        self.fps_var = tk.IntVar(value=60)
        fps_scale = tk.Scale(fps_frame, from_=30, to=120, variable=self.fps_var,
                            orient=tk.HORIZONTAL, length=300,
                            command=self.update_fps_label,
                            bg=self.colors['border'], fg='white',
                            troughcolor=self.colors['select_bg'],
                            highlightthickness=0)
        fps_scale.pack(pady=5)

        self.fps_label = tk.Label(fps_frame, text="FPS: 60",
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
                troughcolor=self.colors['select_bg'],
                highlightthickness=0).pack(pady=5)

        # 控制按钮
        control_container = tk.Frame(anim_frame, bg=self.colors['border'], relief=tk.RIDGE, bd=1)
        control_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(control_container, text="播放控制",
                font=('Microsoft YaHei', 12, 'bold'),
                fg='white', bg=self.colors['border']).pack(pady=(15, 10))

        # 按钮行
        button_frame = tk.Frame(control_container, bg=self.colors['border'])
        button_frame.pack(pady=10)

        self.play_button = tk.Button(button_frame, text="▶ 播放",
                                   command=self.toggle_animation,
                                   font=('Microsoft YaHei', 11, 'bold'),
                                   bg=self.colors['success'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#45A049',
                                   padx=20, pady=8)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ 停止",
                                   command=self.stop_animation,
                                   font=('Microsoft YaHei', 11, 'bold'),
                                   bg=self.colors['error'], fg='white',
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#D32F2F',
                                   padx=20, pady=8)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.record_button = tk.Button(button_frame, text="⏺ 录制",
                                     command=self.record_animation,
                                     font=('Microsoft YaHei', 11, 'bold'),
                                     bg=self.colors['warning'], fg='white',
                                     relief=tk.FLAT, cursor='hand2',
                                     activebackground='#FFA000',
                                     padx=20, pady=8)
        self.record_button.pack(side=tk.LEFT, padx=5)

    def create_display_area(self, parent):
        """创建显示区域"""
        # 右侧面板
        right_frame = tk.Frame(parent, bg=self.colors['bg'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 3D图形容器
        plot_container = tk.Frame(right_frame, bg='white', relief=tk.RIDGE, bd=1)
        plot_container.pack(fill=tk.BOTH, expand=True)

        # 创建matplotlib图形
        self.fig = plt.figure(figsize=(10, 8), facecolor='white', dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')

        # 嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, plot_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar_frame = tk.Frame(right_frame, bg=self.colors['bg'], height=40)
        toolbar_frame.pack(fill=tk.X, pady=(10, 0))

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['select_bg'], height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)

        # 状态信息
        self.status_label = tk.Label(status_frame, text="✓ 系统就绪",
                                   font=('Microsoft YaHei', 10),
                                   fg='white', bg=self.colors['select_bg'])
        self.status_label.pack(side=tk.LEFT, padx=15, pady=5)

        # 坐标信息
        self.coord_label = tk.Label(status_frame, text="坐标: X=0.00, Y=0.00, Z=0.00",
                                   font=('Microsoft YaHei', 9),
                                   fg='#B0BEC5', bg=self.colors['select_bg'])
        self.coord_label.pack(side=tk.RIGHT, padx=15, pady=5)

    def setup_plot(self):
        """初始化3D图形设置"""
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#F8F9FA')

    def update_plot(self):
        """更新3D图形"""
        try:
            # 清除当前图形
            self.ax.clear()

            # 获取参数
            func_name = self.func_var.get()
            t = self.time_var.get()
            res = self.res_var.get()
            elev = self.elev_var.get()
            azim = self.azim_var.get()

            # 更新标签
            self.time_label.config(text=f"T = {t:.2f} 秒")
            self.res_label.config(text=f"分辨率: {res}×{res}")

            # 选择函数
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

            # 计算Z值
            Z = func(X, Y, t)

            # 绘制表面
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap=self.current_colormap,
                                       alpha=0.85,
                                       edgecolor='none',
                                       antialiased=True,
                                       shade=True,
                                       linewidth=0,
                                       rcount=res//2, ccount=res//2)

            # 添加等高线投影
            self.ax.contour(X, Y, Z, zdir='z', offset=np.min(Z)-0.5,
                          cmap=self.current_colormap, alpha=0.4, levels=8)

            # 设置坐标轴
            self.ax.set_xlabel('X轴', fontsize=11, fontweight='bold', color='#333333')
            self.ax.set_ylabel('Y轴', fontsize=11, fontweight='bold', color='#333333')
            self.ax.set_zlabel('Z轴', fontsize=11, fontweight='bold', color='#333333')

            # 设置标题
            title_name = func_name.replace('_', ' ').title()
            self.ax.set_title(f'{title_name} - T = {t:.2f}s',
                            fontsize=13, fontweight='bold', color='#333333', pad=20)

            # 固定坐标轴范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-2.5, 2.5)

            # 设置视角
            self.ax.view_init(elev=elev, azim=azim)

            # 美化网格和背景
            self.ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            self.ax.xaxis.pane.fill = False
            self.ax.yaxis.pane.fill = False
            self.ax.zaxis.pane.fill = False

            # 设置刻度标签
            self.ax.tick_params(axis='x', labelsize=9, colors='#666666')
            self.ax.tick_params(axis='y', labelsize=9, colors='#666666')
            self.ax.tick_params(axis='z', labelsize=9, colors='#666666')

            # 更新状态
            self.status_label.config(text=f"✓ 已更新: {title_name}")

            # 刷新画布
            self.canvas.draw_idle()

        except Exception as e:
            print(f"更新图形出错: {e}")
            self.status_label.config(text=f"✗ 错误: {str(e)[:30]}...")

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

    def update_fps_label(self, value):
        """更新FPS标签"""
        self.fps_label.config(text=f"FPS: {int(float(value))}")

    def auto_demo(self):
        """自动演示"""
        def demo():
            functions = ["simple_wave", "radial_wave", "gaussian_wave", "standing_wave"]
            for func in functions:
                self.func_var.set(func)
                for t in np.linspace(0, 5, 30):
                    if not self.animation_running:
                        break
                    self.time_var.set(t)
                    self.update_plot()
                    time.sleep(1/60)  # 60 FPS
                    self.root.update()

        if not self.animation_running:
            threading.Thread(target=demo, daemon=True).start()

    def change_colormap(self):
        """切换配色方案"""
        current_index = self.colormaps.index(self.current_colormap)
        next_index = (current_index + 1) % len(self.colormaps)
        self.current_colormap = self.colormaps[next_index]
        self.update_plot()

    def save_screenshot(self):
        """保存截图"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("JPG文件", "*.jpg"), ("所有文件", "*.*")]
        )
        if filename:
            self.fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            self.status_label.config(text=f"✓ 已保存: {filename}")

    def reset_view(self):
        """重置视图"""
        self.time_var.set(0)
        self.elev_var.set(30)
        self.azim_var.set(45)
        self.res_var.set(50)
        self.update_plot()

    def toggle_animation(self):
        """切换动画"""
        if not self.animation_running:
            self.start_animation()
        else:
            self.pause_animation()

    def start_animation(self):
        """开始动画 - 高帧率版本"""
        self.animation_running = True
        self.play_button.config(text="⏸ 暂停")

        def animate():
            fps = self.fps_var.get()
            duration = self.duration_var.get()
            frame_time = 1.0 / fps
            total_frames = int(fps * duration)

            for i in range(total_frames):
                if not self.animation_running:
                    break

                # 计算时间
                t = (i / total_frames) * 10
                self.time_var.set(t)

                # 更新图形
                self.root.after_idle(self.update_plot)

                # 精确的帧率控制
                time.sleep(frame_time)

            self.animation_running = False
            self.play_button.config(text="▶ 播放")

        # 在新线程中运行动画
        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()

    def pause_animation(self):
        """暂停动画"""
        self.animation_running = False
        self.play_button.config(text="▶ 继续")

    def stop_animation(self):
        """停止动画"""
        self.animation_running = False
        self.play_button.config(text="▶ 播放")
        self.time_var.set(0)
        self.update_plot()

    def record_animation(self):
        """录制动画"""
        messagebox.showinfo("提示", "动画录制功能开发中...")

    def run(self):
        """运行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ProGUI()
    app.run()