"""
动态表面分析系统 - 图形界面主程序
提供友好的GUI界面来操作和分析动态表面函数
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import Dict, Any, List, Tuple
import threading
import queue
import time

# 导入自定义模块
from dynamic_surface import DynamicSurface
from point_analyzer import PointAnalyzer
from config import simple_wave, radial_wave, gaussian_wave_packet, standing_wave, spiral_wave, interference_pattern, soliton


class DynamicSurfaceGUI:
    """动态表面GUI主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动态表面分析系统")
        self.root.geometry("1400x900")

        # 设置默认字体大小
        self.root.option_add('*Font', 'TkDefaultFont 11')

        # 创建样式
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('TkDefaultFont', 11))
        self.style.configure('TRadiobutton', font=('TkDefaultFont', 11))
        self.style.configure('TButton', font=('TkDefaultFont', 11))
        self.style.configure('TNotebook', font=('TkDefaultFont', 11))
        self.style.configure('TNotebook.Tab', font=('TkDefaultFont', 11))

        # 初始化变量
        self.current_function = tk.StringVar(value="simple_wave")
        self.current_surface = None
        self.animation_running = False
        self.animation_thread = None
        self.colorbar = None
        self.z_lim_fixed = True  # 固定z轴范围
        self.z_min = -2
        self.z_max = 2

        # 创建主框架
        self.setup_ui()

        # 绑定事件
        self.bind_events()

        # 初始化显示
        self.update_surface()

    def setup_ui(self):
        """设置UI布局"""
        # 创建主菜单
        self.create_menu()

        # 创建主面板
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧控制面板
        self.create_control_panel(main_frame)

        # 右侧显示面板
        self.create_display_panel(main_frame)

        # 底部状态栏
        self.create_status_bar()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出图像", command=self.export_image)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="重置视角", command=self.reset_view)
        view_menu.add_command(label="全屏显示", command=self.toggle_fullscreen)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", width=400)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        control_frame.pack_propagate(False)

        # 创建notebook用于分组控制
        notebook = ttk.Notebook(control_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 函数选择页
        self.create_function_tab(notebook)

        # 参数控制页
        self.create_parameter_tab(notebook)

        # 点分析页
        self.create_point_analysis_tab(notebook)

        # 动画控制页
        self.create_animation_tab(notebook)

    def create_function_tab(self, notebook):
        """创建函数选择标签页"""
        func_frame = ttk.Frame(notebook)
        notebook.add(func_frame, text="函数选择")

        # 函数类型选择
        ttk.Label(func_frame, text="选择函数:").pack(anchor=tk.W, padx=10, pady=5)

        functions = [
            ("简单波", "simple_wave"),
            ("径向波", "radial_wave"),
            ("高斯波包", "gaussian_wave_packet"),
            ("驻波", "standing_wave"),
            ("螺旋波", "spiral_wave"),
            ("干涉图样", "interference_pattern"),
            ("孤立子", "soliton")
        ]

        for name, value in functions:
            ttk.Radiobutton(func_frame, text=name, variable=self.current_function,
                          value=value, command=self.update_surface).pack(anchor=tk.W, padx=20)

        # 快速演示按钮
        ttk.Separator(func_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(func_frame, text="快速演示:").pack(anchor=tk.W, padx=10, pady=5)

        demo_frame = ttk.Frame(func_frame)
        demo_frame.pack(padx=10, pady=5)

        ttk.Button(demo_frame, text="所有函数演示",
                  command=self.demo_all_functions).pack(side=tk.LEFT, padx=5)
        ttk.Button(demo_frame, text="梯度分析",
                  command=self.demo_gradients).pack(side=tk.LEFT, padx=5)

    def create_parameter_tab(self, notebook):
        """创建参数控制标签页"""
        param_frame = ttk.Frame(notebook)
        notebook.add(param_frame, text="参数控制")

        # 参数输入框架
        params_label_frame = ttk.LabelFrame(param_frame, text="函数参数")
        params_label_frame.pack(fill=tk.X, padx=10, pady=10)

        # 坐标范围控制
        coord_frame = ttk.LabelFrame(param_frame, text="坐标范围")
        coord_frame.pack(fill=tk.X, padx=10, pady=10)

        # X范围
        x_frame = ttk.Frame(coord_frame)
        x_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(x_frame, text="X范围:").pack(side=tk.LEFT)
        self.x_min = ttk.Entry(x_frame, width=10)
        self.x_min.pack(side=tk.LEFT, padx=5)
        self.x_min.insert(0, "-5")
        ttk.Label(x_frame, text="到").pack(side=tk.LEFT)
        self.x_max = ttk.Entry(x_frame, width=10)
        self.x_max.pack(side=tk.LEFT, padx=5)
        self.x_max.insert(0, "5")

        # Y范围
        y_frame = ttk.Frame(coord_frame)
        y_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(y_frame, text="Y范围:").pack(side=tk.LEFT)
        self.y_min = ttk.Entry(y_frame, width=10)
        self.y_min.pack(side=tk.LEFT, padx=5)
        self.y_min.insert(0, "-5")
        ttk.Label(y_frame, text="到").pack(side=tk.LEFT)
        self.y_max = ttk.Entry(y_frame, width=10)
        self.y_max.pack(side=tk.LEFT, padx=5)
        self.y_max.insert(0, "5")

        # 时间控制
        time_frame = ttk.LabelFrame(param_frame, text="时间控制")
        time_frame.pack(fill=tk.X, padx=10, pady=10)

        t_frame = ttk.Frame(time_frame)
        t_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(t_frame, text="时间 t:").pack(side=tk.LEFT)
        self.time_var = tk.DoubleVar(value=0)
        self.time_slider = ttk.Scale(t_frame, from_=0, to=10, variable=self.time_var,
                                    orient=tk.HORIZONTAL, length=200)
        self.time_slider.pack(side=tk.LEFT, padx=10)
        self.time_label = ttk.Label(t_frame, text="0.00")
        self.time_label.pack(side=tk.LEFT)

        # 分辨率控制
        res_frame = ttk.Frame(time_frame)
        res_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(res_frame, text="分辨率:").pack(side=tk.LEFT)
        self.resolution = ttk.Spinbox(res_frame, from_=10, to=100, width=10, increment=10)
        self.resolution.pack(side=tk.LEFT, padx=5)
        self.resolution.set(50)

        # 更新按钮
        ttk.Button(param_frame, text="更新显示",
                  command=self.update_surface).pack(pady=10)

    def create_point_analysis_tab(self, notebook):
        """创建点分析标签页"""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="点分析")

        # 添加分析点
        add_frame = ttk.LabelFrame(analysis_frame, text="添加分析点")
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        # X坐标
        x_frame = ttk.Frame(add_frame)
        x_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(x_frame, text="X坐标:").pack(side=tk.LEFT)
        self.point_x = ttk.Entry(x_frame, width=10)
        self.point_x.pack(side=tk.LEFT, padx=5)
        self.point_x.insert(0, "0")

        # Y坐标
        y_frame = ttk.Frame(add_frame)
        y_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(y_frame, text="Y坐标:").pack(side=tk.LEFT)
        self.point_y = ttk.Entry(y_frame, width=10)
        self.point_y.pack(side=tk.LEFT, padx=5)
        self.point_y.insert(0, "0")

        # 标签
        label_frame = ttk.Frame(add_frame)
        label_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(label_frame, text="标签:").pack(side=tk.LEFT)
        self.point_label = ttk.Entry(label_frame, width=20)
        self.point_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(add_frame, text="添加点",
                  command=self.add_analysis_point).pack(pady=5)

        # 分析选项
        option_frame = ttk.LabelFrame(analysis_frame, text="分析选项")
        option_frame.pack(fill=tk.X, padx=10, pady=10)

        self.show_time_series = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="显示时间序列",
                       variable=self.show_time_series).pack(anchor=tk.W, padx=10)

        self.show_gradient = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="显示梯度分析",
                       variable=self.show_gradient).pack(anchor=tk.W, padx=10)

        # 执行分析按钮
        ttk.Button(analysis_frame, text="执行分析",
                  command=self.perform_analysis).pack(pady=10)

        # 点列表
        list_frame = ttk.LabelFrame(analysis_frame, text="分析点列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.point_listbox = tk.Listbox(list_frame, height=8)
        self.point_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(list_frame, text="清除所有点",
                  command=self.clear_points).pack(pady=5)

    def create_animation_tab(self, notebook):
        """创建动画控制标签页"""
        anim_frame = ttk.Frame(notebook)
        notebook.add(anim_frame, text="动画控制")

        # 动画参数
        param_frame = ttk.LabelFrame(anim_frame, text="动画参数")
        param_frame.pack(fill=tk.X, padx=10, pady=10)

        # 帧数
        frame_frame = ttk.Frame(param_frame)
        frame_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_frame, text="帧数:").pack(side=tk.LEFT)
        self.anim_frames = ttk.Spinbox(frame_frame, from_=10, to=200, width=10, increment=10)
        self.anim_frames.pack(side=tk.LEFT, padx=5)
        self.anim_frames.set(50)

        # 帧率
        fps_frame = ttk.Frame(param_frame)
        fps_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(fps_frame, text="帧率(FPS):").pack(side=tk.LEFT)
        self.anim_fps = ttk.Spinbox(frame_frame, from_=1, to=60, width=10, increment=5)
        self.anim_fps.pack(side=tk.LEFT, padx=5)
        self.anim_fps.set(30)

        # 时间范围
        time_range_frame = ttk.Frame(param_frame)
        time_range_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(time_range_frame, text="时间范围:").pack(side=tk.LEFT)
        ttk.Label(time_range_frame, text="从").pack(side=tk.LEFT, padx=5)
        self.t_start = ttk.Entry(time_range_frame, width=8)
        self.t_start.pack(side=tk.LEFT)
        self.t_start.insert(0, "0")
        ttk.Label(time_range_frame, text="到").pack(side=tk.LEFT, padx=5)
        self.t_end = ttk.Entry(time_range_frame, width=8)
        self.t_end.pack(side=tk.LEFT)
        self.t_end.insert(0, "10")

        # 控制按钮
        control_frame = ttk.Frame(anim_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=20)

        self.play_button = ttk.Button(control_frame, text="▶ 播放",
                                     command=self.toggle_animation)
        self.play_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="⏸ 暂停",
                  command=self.pause_animation).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="⏹ 停止",
                  command=self.stop_animation).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="保存动画",
                  command=self.save_animation).pack(side=tk.LEFT, padx=5)

        # 进度条
        progress_frame = ttk.LabelFrame(anim_frame, text="动画进度")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)

        self.anim_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.anim_progress.pack(fill=tk.X, padx=10, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.pack()

    def create_display_panel(self, parent):
        """创建右侧显示面板"""
        display_frame = ttk.LabelFrame(parent, text="3D可视化")
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # 创建matplotlib图形
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')

        # 嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, display_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加工具栏
        toolbar_frame = ttk.Frame(display_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # 绑定鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.coord_label = ttk.Label(self.status_frame, text="坐标: (0, 0, 0)", relief=tk.SUNKEN)
        self.coord_label.pack(side=tk.RIGHT)

    def bind_events(self):
        """绑定事件处理"""
        # 时间滑块变化
        self.time_slider.bind('<Motion>', self.on_time_change)

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_surface(self):
        """更新3D表面显示"""
        try:
            # 获取参数
            x_range = (float(self.x_min.get()), float(self.x_max.get()))
            y_range = (float(self.y_min.get()), float(self.y_max.get()))
            t = self.time_var.get()
            resolution = int(self.resolution.get())

            # 获取当前函数
            func_name = self.current_function.get()
            function_map = {
                "simple_wave": simple_wave,
                "radial_wave": radial_wave,
                "gaussian_wave_packet": gaussian_wave_packet,
                "standing_wave": standing_wave,
                "spiral_wave": spiral_wave,
                "interference_pattern": interference_pattern,
                "soliton": soliton
            }
            func = function_map.get(func_name, simple_wave)

            # 创建动态表面对象
            self.current_surface = DynamicSurface(func)

            # 计算表面
            X, Y, Z = self.current_surface.evaluate_surface(x_range, y_range, t, resolution)

            # 清除并重绘
            self.ax.clear()
            surf = self.ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

            # 设置标签和标题，使用大字体
            self.ax.set_xlabel('X', fontsize=12, fontweight='bold')
            self.ax.set_ylabel('Y', fontsize=12, fontweight='bold')
            self.ax.set_zlabel('Z', fontsize=12, fontweight='bold')
            self.ax.set_title(f'{func_name} - t={t:.2f}', fontsize=14, fontweight='bold')

            # 设置固定的坐标轴范围
            self.ax.set_xlim(float(self.x_min.get()), float(self.x_max.get()))
            self.ax.set_ylim(float(self.y_min.get()), float(self.y_max.get()))
            self.ax.set_zlim(self.z_min, self.z_max)  # 固定z轴范围

            # 设置刻度标签字体
            self.ax.tick_params(axis='x', labelsize=10)
            self.ax.tick_params(axis='y', labelsize=10)
            self.ax.tick_params(axis='z', labelsize=10)

            # 添加颜色条
            # 不添加颜色条以避免错误

            self.canvas.draw()

            # 更新状态
            self.status_label.config(text=f"已更新: {func_name}")

        except Exception as e:
            messagebox.showerror("错误", f"更新表面时出错: {str(e)}")

    def on_time_change(self, event=None):
        """时间滑块变化回调"""
        t = self.time_var.get()
        self.time_label.config(text=f"{t:.2f}")
        self.update_surface()

    def add_analysis_point(self):
        """添加分析点"""
        try:
            x = float(self.point_x.get())
            y = float(self.point_y.get())
            label = self.point_label.get() or f"点({x:.1f},{y:.1f})"

            # 添加到列表
            self.point_listbox.insert(tk.END, f"{label}: ({x:.2f}, {y:.2f})")

            # 如果已有表面，在图上标记点
            if self.current_surface:
                t = self.time_var.get()
                z = self.current_surface.evaluate_surface(
                    (x-0.1, x+0.1), (y-0.1, y+0.1), t, 5
                )[2][2, 2]  # 获取中心点的z值
                self.ax.scatter([x], [y], [z], color='red', s=50, marker='o')
                self.canvas.draw()

            self.status_label.config(text=f"已添加分析点: {label}")

        except ValueError:
            messagebox.showerror("错误", "请输入有效的坐标值")

    def clear_points(self):
        """清除所有分析点"""
        self.point_listbox.delete(0, tk.END)
        self.update_surface()  # 重绘表面以清除标记
        self.status_label.config(text="已清除所有分析点")

    def perform_analysis(self):
        """执行点分析"""
        if self.point_listbox.size() == 0:
            messagebox.showwarning("警告", "请先添加分析点")
            return

        # 创建分析窗口
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("点分析结果")
        analysis_window.geometry("800x600")

        # 创建分析图形
        fig = plt.Figure(figsize=(10, 6))

        if self.show_time_series.get():
            # 时间序列分析
            ax1 = fig.add_subplot(121)
            # 这里添加时间序列分析代码

        if self.show_gradient.get():
            # 梯度分析
            ax2 = fig.add_subplot(122)
            # 这里添加梯度分析代码

        # 显示在窗口中
        canvas = FigureCanvasTkAgg(fig, analysis_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def toggle_animation(self):
        """切换动画播放状态"""
        if not self.animation_running:
            self.start_animation()
        else:
            self.pause_animation()

    def start_animation(self):
        """开始动画"""
        if self.animation_running:
            return

        self.animation_running = True
        self.play_button.config(text="⏸ 暂停")

        # 创建动画线程
        self.animation_thread = threading.Thread(target=self.run_animation)
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def run_animation(self):
        """运行动画"""
        try:
            frames = int(self.anim_frames.get())
            fps = int(self.anim_fps.get())
            t_start = float(self.t_start.get())
            t_end = float(self.t_end.get())

            dt = (t_end - t_start) / frames
            interval = 1.0 / fps

            for i in range(frames):
                if not self.animation_running:
                    break

                t = t_start + i * dt
                self.time_var.set(t)

                # 更新进度条
                progress = (i + 1) / frames * 100
                self.anim_progress['value'] = progress
                self.progress_label.config(text=f"播放中: {i+1}/{frames}")

                # 在主线程中更新界面
                self.root.after_idle(self.update_surface)

                time.sleep(interval)

        except Exception as e:
            messagebox.showerror("错误", f"动画播放出错: {str(e)}")
        finally:
            self.animation_running = False
            self.play_button.config(text="▶ 播放")
            self.progress_label.config(text="动画完成")

    def pause_animation(self):
        """暂停动画"""
        self.animation_running = False
        self.play_button.config(text="▶ 继续")

    def stop_animation(self):
        """停止动画"""
        self.animation_running = False
        self.time_var.set(0)
        self.anim_progress['value'] = 0
        self.progress_label.config(text="准备就绪")
        self.update_surface()
        self.play_button.config(text="▶ 播放")

    def save_animation(self):
        """保存动画"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF文件", "*.gif"), ("MP4文件", "*.mp4"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                t_start = float(self.t_start.get())
                t_end = float(self.t_end.get())
                frames = int(self.anim_frames.get())
                fps = int(self.anim_fps.get())

                # 获取坐标范围
                x_range = (float(self.x_min.get()), float(self.x_max.get()))
                y_range = (float(self.y_min.get()), float(self.y_max.get()))

                # 创建动画
                anim = self.current_surface.create_animation(
                    x_range, y_range, (t_start, t_end), frames, 1000/fps
                )

                # 保存动画
                if filename.endswith('.gif'):
                    anim.save(filename, writer='pillow', fps=fps)
                else:
                    anim.save(filename, writer='ffmpeg', fps=fps)

                messagebox.showinfo("成功", f"动画已保存到: {filename}")

            except Exception as e:
                messagebox.showerror("错误", f"保存动画失败: {str(e)}")

    def demo_all_functions(self):
        """演示所有函数"""
        demo_window = tk.Toplevel(self.root)
        demo_window.title("函数演示")
        demo_window.geometry("1200x800")

        # 创建多个子图
        fig = plt.Figure(figsize=(15, 10))

        functions = [
            ("simple_wave", simple_wave),
            ("radial_wave", radial_wave),
            ("gaussian_wave_packet", gaussian_wave_packet),
            ("standing_wave", standing_wave),
            ("spiral_wave", spiral_wave),
            ("interference_pattern", interference_pattern),
            ("soliton", soliton)
        ]

        for i, (name, func) in enumerate(functions):
            ax = fig.add_subplot(3, 3, i+1, projection='3d')

            # 计算表面
            surface = DynamicSurface(func)
            X, Y, Z = surface.evaluate_surface((-5, 5), (-5, 5), 0, 30)

            # 绘制
            ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
            ax.set_title(name)

        # 显示
        canvas = FigureCanvasTkAgg(fig, demo_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def demo_gradients(self):
        """演示梯度分析"""
        messagebox.showinfo("提示", "梯度分析功能开发中...")

    def export_image(self):
        """导出当前图像"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("JPG文件", "*.jpg"), ("所有文件", "*.*")]
        )

        if filename:
            self.fig.savefig(filename, dpi=100, bbox_inches='tight')
            messagebox.showinfo("成功", f"图像已保存到: {filename}")

    def export_data(self):
        """导出数据"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            # 导出当前表面数据
            if self.current_surface:
                x_range = (float(self.x_min.get()), float(self.x_max.get()))
                y_range = (float(self.y_min.get()), float(self.y_max.get()))
                t = self.time_var.get()
                resolution = int(self.resolution.get())

                X, Y, Z = self.current_surface.evaluate_surface(x_range, y_range, t, resolution)

                # 保存为CSV
                data = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
                np.savetxt(filename, data, delimiter=',', header='X,Y,Z')

                messagebox.showinfo("成功", f"数据已保存到: {filename}")

    def reset_view(self):
        """重置3D视角"""
        self.ax.view_init(elev=30, azim=45)
        self.canvas.draw()

    def toggle_fullscreen(self):
        """切换全屏"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)

    def on_click(self, event):
        """鼠标点击事件"""
        if event.inaxes == self.ax:
            self.coord_label.config(text=f"点击坐标: ({event.xdata:.2f}, {event.ydata:.2f})")

    def on_closing(self):
        """窗口关闭事件"""
        if self.animation_running:
            self.stop_animation()
        self.root.quit()
        self.root.destroy()

    def show_help(self):
        """显示帮助"""
        help_text = """
动态表面分析系统使用说明

1. 函数选择：选择不同的数学函数来生成动态表面
2. 参数控制：调整坐标范围、时间参数和分辨率
3. 点分析：在表面上标记特定点并分析其属性
4. 动画控制：创建和播放表面演化动画
5. 导出功能：保存图像和动画文件

快捷操作：
- 鼠标拖动：旋转3D视图
- 滚轮：缩放视图
- 右键拖动：平移视图
        """
        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        """显示关于信息"""
        about_text = """
动态表面分析系统
版本 1.0

一个用于分析和可视化动态表面的交互式工具
支持多种数学函数和实时动画效果

开发语言：Python + Tkinter + Matplotlib
        """
        messagebox.showinfo("关于", about_text)

    def run(self):
        """运行GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    # 创建并运行GUI
    app = DynamicSurfaceGUI()
    app.run()