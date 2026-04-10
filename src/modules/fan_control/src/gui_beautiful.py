"""
美观版动态表面分析系统 - 图形界面
现代化的UI设计
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.colors as colors

# 设置matplotlib的美观样式
try:
    plt.style.use('seaborn-darkgrid')
except:
    plt.style.use('default')

plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['grid.alpha'] = 0.3

# 简单的波形函数
def simple_wave(x, y, t=0):
    """简单波形"""
    return np.sin(x) * np.cos(y + t)

def radial_wave(x, y, t=0):
    """径向波"""
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - t) * np.exp(-0.1 * r)

def gaussian_wave(x, y, t=0):
    """高斯波包"""
    return np.exp(-0.1*(x**2 + y**2)) * np.sin(2*x + t) * np.cos(2*y + t)

def standing_wave(x, y, t=0):
    """驻波"""
    return np.sin(x) * np.sin(y) * np.cos(t)

class BeautifulGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动态表面分析系统 - 专业版")
        self.root.geometry("1200x800")

        # 设置主题色彩
        self.setup_colors()

        # 创建现代化样式
        self.setup_styles()

        # 创建主框架
        self.setup_ui()

        # 初始化3D图形
        self.setup_plot()

        # 初始显示
        self.update_plot()

    def setup_colors(self):
        """设置主题色彩"""
        # 现代化配色方案
        self.bg_color = "#2B2B2B"           # 深色背景
        self.panel_color = "#3C3F41"        # 面板背景
        self.accent_color = "#365880"        # 强调色
        self.text_color = "#A9B7C6"          # 主文字色
        self.button_color = "#4C5052"        # 按钮颜色
        self.button_hover = "#5C6163"        # 按钮悬停色
        self.success_color = "#3C8C50"       # 成功色
        self.warning_color = "#8C7A3C"       # 警告色

    def setup_styles(self):
        """创建现代化样式"""
        self.style = ttk.Style()
        self.root.configure(bg=self.bg_color)

        # 设置ttk主题
        self.style.theme_use('clam')

        # 配置各种控件样式
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabelframe', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.text_color, font=('Arial', 11, 'bold'))
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color, font=('Arial', 10))
        self.style.configure('TRadiobutton', background=self.bg_color, foreground=self.text_color, font=('Arial', 10))
        self.style.configure('TButton', background=self.button_color, foreground=self.text_color,
                           font=('Arial', 10, 'bold'), borderwidth=0)
        self.style.map('TButton',
                      background=[('active', self.button_hover)],
                      foreground=[('active', 'white')])

        # 配置滑块样式
        self.style.configure('Horizontal.TScale', background=self.bg_color)

        # 配置Notebook样式
        self.style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=self.panel_color, foreground=self.text_color,
                           padding=[20, 10], font=('Arial', 10, 'bold'))
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.accent_color)],
                      foreground=[('selected', 'white')])

    def setup_ui(self):
        """设置UI布局"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部标题栏
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = tk.Label(title_frame, text="动态表面分析系统",
                              font=('Arial', 18, 'bold'),
                              fg='white', bg=self.accent_color)
        title_label.pack(fill=tk.X, ipady=10)

        # 主内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧控制面板
        self.create_control_panel(content_frame)

        # 右侧显示区域
        self.create_display_area(content_frame)

        # 底部状态栏
        self.create_status_bar(main_container)

    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 创建Notebook
        self.notebook = ttk.Notebook(control_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各个标签页
        self.create_function_tab()
        self.create_parameter_tab()
        self.create_animation_tab()

    def create_function_tab(self):
        """函数选择标签页"""
        func_frame = ttk.Frame(self.notebook)
        self.notebook.add(func_frame, text="[函数] 函数选择")

        # 函数选择区域
        func_container = ttk.LabelFrame(func_frame, text="选择数学函数", padding=15)
        func_container.pack(fill=tk.X, padx=10, pady=10)

        # 函数选项
        self.func_var = tk.StringVar(value="simple_wave")
        functions = [
            ("[●] 简单波", "simple_wave", "基础的正弦波形"),
            ("[~] 径向波", "radial_wave", "从中心向外扩散的波"),
            ("[*] 高斯波包", "gaussian_wave", "高斯调制的波形"),
            ("[||] 驻波", "standing_wave", "固定的振动模式")
        ]

        for display_name, value, description in functions:
            frame = ttk.Frame(func_container)
            frame.pack(fill=tk.X, pady=5)

            rb = ttk.Radiobutton(frame, text=display_name,
                               variable=self.func_var, value=value,
                               command=self.update_plot)
            rb.pack(side=tk.LEFT)

            desc_label = tk.Label(frame, text=f"  {description}",
                                font=('Arial', 9), fg='gray60', bg=self.bg_color)
            desc_label.pack(side=tk.LEFT)

        # 快速操作按钮
        quick_frame = ttk.LabelFrame(func_frame, text="快速操作", padding=15)
        quick_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(quick_frame, text="[▶] 自动演示",
                  command=self.auto_demo).pack(fill=tk.X, pady=5)
        ttk.Button(quick_frame, text="[色彩] 切换配色",
                  command=self.change_colormap).pack(fill=tk.X, pady=5)
        ttk.Button(quick_frame, text="[相机] 截图保存",
                  command=self.save_screenshot).pack(fill=tk.X, pady=5)

    def create_parameter_tab(self):
        """参数控制标签页"""
        param_frame = ttk.Frame(self.notebook)
        self.notebook.add(param_frame, text="[设置] 参数控制")

        # 时间控制
        time_frame = ttk.LabelFrame(param_frame, text="[时间] 时间参数", padding=15)
        time_frame.pack(fill=tk.X, padx=10, pady=10)

        self.time_var = tk.DoubleVar(value=0)
        tk.Label(time_frame, text="时间进度:", font=('Arial', 10, 'bold'),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)

        self.time_slider = ttk.Scale(time_frame, from_=0, to=10,
                                    variable=self.time_var, orient=tk.HORIZONTAL,
                                    length=280, command=lambda e: self.update_plot())
        self.time_slider.pack(fill=tk.X, pady=5)

        self.time_label = tk.Label(time_frame, text="t = 0.00",
                                 font=('Arial', 12, 'bold'), fg=self.success_color,
                                 bg=self.bg_color)
        self.time_label.pack(pady=5)

        # 显示参数
        display_frame = ttk.LabelFrame(param_frame, text="[显示] 显示参数", padding=15)
        display_frame.pack(fill=tk.X, padx=10, pady=10)

        # 分辨率控制
        tk.Label(display_frame, text="网格分辨率:", font=('Arial', 10, 'bold'),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)

        self.res_var = tk.IntVar(value=40)
        self.res_slider = ttk.Scale(display_frame, from_=20, to=80,
                                   variable=self.res_var, orient=tk.HORIZONTAL,
                                   length=280, command=lambda e: self.update_plot())
        self.res_slider.pack(fill=tk.X, pady=5)

        self.res_label = tk.Label(display_frame, text="分辨率: 40×40",
                                font=('Arial', 10), fg=self.text_color, bg=self.bg_color)
        self.res_label.pack()

        # 视图参数
        view_frame = ttk.LabelFrame(param_frame, text="[视图] 视图参数", padding=15)
        view_frame.pack(fill=tk.X, padx=10, pady=10)

        # 仰角和方位角
        tk.Label(view_frame, text="仰角 (Elevation):", font=('Arial', 10),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)
        self.elev_var = tk.DoubleVar(value=30)
        ttk.Scale(view_frame, from_=0, to=90, variable=self.elev_var,
                 orient=tk.HORIZONTAL, length=280,
                 command=lambda e: self.update_plot()).pack(fill=tk.X, pady=2)

        tk.Label(view_frame, text="方位角 (Azimuth):", font=('Arial', 10),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)
        self.azim_var = tk.DoubleVar(value=45)
        ttk.Scale(view_frame, from_=0, to=360, variable=self.azim_var,
                 orient=tk.HORIZONTAL, length=280,
                 command=lambda e: self.update_plot()).pack(fill=tk.X, pady=2)

    def create_animation_tab(self):
        """动画控制标签页"""
        anim_frame = ttk.Frame(self.notebook)
        self.notebook.add(anim_frame, text="[动画] 动画控制")

        # 动画设置
        settings_frame = ttk.LabelFrame(anim_frame, text="[录像] 动画设置", padding=15)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)

        # 帧率设置
        tk.Label(settings_frame, text="帧率 (FPS):", font=('Arial', 10),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)
        self.fps_var = tk.IntVar(value=30)
        ttk.Spinbox(settings_frame, from_=10, to=60, textvariable=self.fps_var,
                   width=15).pack(anchor=tk.W, pady=5)

        # 动画时长
        tk.Label(settings_frame, text="动画时长 (秒):", font=('Arial', 10),
                fg=self.text_color, bg=self.bg_color).pack(anchor=tk.W)
        self.duration_var = tk.DoubleVar(value=5)
        ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.duration_var,
                   width=15, increment=0.5).pack(anchor=tk.W, pady=5)

        # 控制按钮
        control_frame = ttk.LabelFrame(anim_frame, text="[播放] 播放控制", padding=15)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.play_button = ttk.Button(button_frame, text="▶ 播放",
                                     command=self.toggle_animation, width=12)
        self.play_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="⏹ 停止",
                  command=self.stop_animation, width=12).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="⏺ 录制",
                  command=self.record_animation, width=12).pack(side=tk.LEFT, padx=5)

    def create_display_area(self, parent):
        """创建右侧显示区域"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建matplotlib容器
        self.setup_matplotlib_container(display_frame)

    def setup_matplotlib_container(self, parent):
        """设置matplotlib容器"""
        # 创建图形
        self.fig = plt.figure(figsize=(10, 8), facecolor='#FFFFFF')
        self.ax = self.fig.add_subplot(111, projection='3d')

        # 嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 创建工具栏
        toolbar_frame = tk.Frame(parent, bg=self.bg_color, height=30)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # 设置colormap
        self.current_colormap = 'plasma'
        self.colormaps = ['plasma', 'viridis', 'coolwarm', 'ocean', 'rainbow', 'twilight']

    def setup_plot(self):
        """初始化3D图形设置"""
        self.ax.grid(True, alpha=0.3)
        self.ax.set_facecolor('#F0F0F0')
        self.fig.patch.set_facecolor('white')

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
            self.time_label.config(text=f"t = {t:.2f}")
            self.res_label.config(text=f"分辨率: {res}×{res}")

            # 选择函数
            functions = {
                "simple_wave": simple_wave,
                "radial_wave": radial_wave,
                "gaussian_wave": gaussian_wave,
                "standing_wave": standing_wave
            }
            func = functions.get(func_name, simple_wave)

            # 创建网格
            x = np.linspace(-5, 5, res)
            y = np.linspace(-5, 5, res)
            X, Y = np.meshgrid(x, y)

            # 计算Z值
            Z = func(X, Y, t)

            # 绘制表面 - 使用更美观的样式
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap=self.current_colormap,
                                       alpha=0.9,
                                       edgecolor='none',
                                       antialiased=True,
                                       shade=True,
                                       linewidth=0)

            # 添加等高线投影
            self.ax.contour(X, Y, Z, zdir='z', offset=np.min(Z)-0.5,
                          cmap=self.current_colormap, alpha=0.5, levels=10)

            # 设置美观的坐标轴
            self.ax.set_xlabel('X轴', fontsize=12, fontweight='bold', color='#333333')
            self.ax.set_ylabel('Y轴', fontsize=12, fontweight='bold', color='#333333')
            self.ax.set_zlabel('Z轴', fontsize=12, fontweight='bold', color='#333333')
            self.ax.set_title(f'{func_name.replace("_", " ").title()} - 时间: {t:.2f}',
                            fontsize=14, fontweight='bold', color='#333333', pad=20)

            # 固定坐标轴范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-3, 3)

            # 设置视角
            self.ax.view_init(elev=elev, azim=azim)

            # 美化网格和背景
            self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            self.ax.xaxis.pane.fill = False
            self.ax.yaxis.pane.fill = False
            self.ax.zaxis.pane.fill = False

            # 设置刻度样式
            self.ax.tick_params(axis='x', labelsize=9, colors='#666666')
            self.ax.tick_params(axis='y', labelsize=9, colors='#666666')
            self.ax.tick_params(axis='z', labelsize=9, colors='#666666')

            # 刷新画布
            self.canvas.draw()

        except Exception as e:
            print(f"更新图形出错: {e}")
            messagebox.showerror("错误", f"更新图形时出错: {str(e)}")

    def auto_demo(self):
        """自动演示所有函数"""
        import threading
        import time

        def demo():
            functions = ["simple_wave", "radial_wave", "gaussian_wave", "standing_wave"]
            for func in functions:
                self.func_var.set(func)
                for t in np.linspace(0, 5, 20):
                    self.time_var.set(t)
                    self.update_plot()
                    self.root.update()
                    time.sleep(0.1)

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
            messagebox.showinfo("成功", f"截图已保存到: {filename}")

    def toggle_animation(self):
        """切换动画播放"""
        if not hasattr(self, 'animation_running') or not self.animation_running:
            self.start_animation()
        else:
            self.stop_animation()

    def start_animation(self):
        """开始动画"""
        self.animation_running = True
        self.play_button.config(text="⏸ 暂停")

        def animate():
            fps = self.fps_var.get()
            duration = self.duration_var.get()
            steps = int(fps * duration)

            for i in range(steps):
                if not self.animation_running:
                    break
                t = (i / steps) * 10  # 0到10秒
                self.time_var.set(t)
                self.update_plot()
                self.root.after(int(1000/fps))

        self.root.after(100, animate)

    def stop_animation(self):
        """停止动画"""
        self.animation_running = False
        self.play_button.config(text="▶ 播放")
        self.time_var.set(0)
        self.update_plot()

    def record_animation(self):
        """录制动画"""
        messagebox.showinfo("提示", "动画录制功能开发中...")

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # 状态信息
        self.status_label = tk.Label(status_frame, text="[√] 系统就绪",
                                   font=('Arial', 10), fg=self.success_color,
                                   bg=self.bg_color)
        self.status_label.pack(side=tk.LEFT)

        # 坐标信息
        self.coord_label = tk.Label(status_frame, text="坐标: X=0.00, Y=0.00, Z=0.00",
                                  font=('Arial', 9), fg='gray60', bg=self.bg_color)
        self.coord_label.pack(side=tk.RIGHT)

    def run(self):
        """运行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BeautifulGUI()
    app.run()