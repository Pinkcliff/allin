"""
简化版动态表面分析系统 - 图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

# 简单的波形函数
def simple_wave(x, y, t=0):
    """简单波形"""
    return np.sin(x) * np.cos(y + t)

def radial_wave(x, y, t=0):
    """径向波"""
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - t) * np.exp(-0.1 * r)

class SimpleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("动态表面分析系统 - 简化版")
        self.root.geometry("1000x700")

        # 设置字体大小
        self.root.option_add('*Font', 'TkDefaultFont 11')
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('TkDefaultFont', 11))
        self.style.configure('TRadiobutton', font=('TkDefaultFont', 11))
        self.style.configure('TButton', font=('TkDefaultFont', 11))

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)

        # 函数选择
        ttk.Label(control_frame, text="选择函数:").pack(pady=10)
        self.func_var = tk.StringVar(value="simple_wave")
        ttk.Radiobutton(control_frame, text="简单波",
                       variable=self.func_var, value="simple_wave",
                       command=self.update_plot).pack(pady=5)
        ttk.Radiobutton(control_frame, text="径向波",
                       variable=self.func_var, value="radial_wave",
                       command=self.update_plot).pack(pady=5)

        # 时间控制
        ttk.Label(control_frame, text="时间:").pack(pady=(20, 5))
        self.time_var = tk.DoubleVar(value=0)
        time_scale = ttk.Scale(control_frame, from_=0, to=10,
                              variable=self.time_var, orient=tk.HORIZONTAL,
                              length=200, command=lambda e: self.update_plot())
        time_scale.pack(pady=5)

        self.time_label = ttk.Label(control_frame, text="t = 0.00")
        self.time_label.pack()

        # 分辨率控制
        ttk.Label(control_frame, text="分辨率:").pack(pady=(20, 5))
        self.res_var = tk.IntVar(value=30)
        ttk.Scale(control_frame, from_=10, to=50,
                 variable=self.res_var, orient=tk.HORIZONTAL,
                 length=200, command=lambda e: self.update_plot()).pack(pady=5)

        # 更新按钮
        ttk.Button(control_frame, text="更新",
                  command=self.update_plot).pack(pady=20)

        # 右侧图形显示
        plot_frame = ttk.Frame(main_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建matplotlib图形
        self.fig = plt.figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')

        # 嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始化显示
        self.update_plot()

    def update_plot(self):
        """更新3D图形"""
        try:
            # 清除当前图形
            self.ax.clear()

            # 获取参数
            func_name = self.func_var.get()
            t = self.time_var.get()
            res = self.res_var.get()

            # 更新时间标签
            self.time_label.config(text=f"t = {t:.2f}")

            # 选择函数
            if func_name == "simple_wave":
                func = simple_wave
            else:
                func = radial_wave

            # 创建网格
            x = np.linspace(-5, 5, res)
            y = np.linspace(-5, 5, res)
            X, Y = np.meshgrid(x, y)

            # 计算Z值
            Z = func(X, Y, t)

            # 绘制表面
            self.ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

            # 设置标签和标题，使用大字体
            self.ax.set_xlabel('X', fontsize=12, fontweight='bold')
            self.ax.set_ylabel('Y', fontsize=12, fontweight='bold')
            self.ax.set_zlabel('Z', fontsize=12, fontweight='bold')
            self.ax.set_title(f'{func_name} - t={t:.2f}', fontsize=14, fontweight='bold')

            # 设置固定的坐标轴范围
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-2, 2)  # 固定z轴范围

            # 设置刻度标签字体
            self.ax.tick_params(axis='x', labelsize=10)
            self.ax.tick_params(axis='y', labelsize=10)
            self.ax.tick_params(axis='z', labelsize=10)

            # 刷新画布
            self.canvas.draw()

        except Exception as e:
            print(f"更新出错: {e}")
            messagebox.showerror("错误", f"更新图形时出错: {str(e)}")

    def run(self):
        """运行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleGUI()
    app.run()