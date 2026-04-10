import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

class DynamicSurfaceGrid:
    def __init__(self, x_range=(-5, 5), y_range=(-5, 5), divisions=20):
        """
        初始化动态表面网格

        参数:
        - x_range: x轴范围 (min, max)
        - y_range: y轴范围 (min, max)
        - divisions: 每个轴的分割份数
        """
        # 确保x和y的范围相等
        x_length = x_range[1] - x_range[0]
        y_length = y_range[1] - y_range[0]

        if abs(x_length - y_length) > 1e-10:
            print(f"警告: x和y的范围不相等 (x长度={x_length:.3f}, y长度={y_length:.3f})")
            print(f"自动调整y范围以匹配x范围")
            center_y = (y_range[0] + y_range[1]) / 2
            y_range = (center_y - x_length/2, center_y + x_length/2)
            print(f"新的y范围: {y_range}")

        self.x_range = x_range
        self.y_range = y_range
        self.divisions = divisions

        # 生成网格点
        self.x = np.linspace(x_range[0], x_range[1], divisions)
        self.y = np.linspace(y_range[0], y_range[1], divisions)
        self.X, self.Y = np.meshgrid(self.x, self.y)

        print(f"创建了 {divisions}x{divisions} = {divisions*divisions} 个网格点")
        print(f"x范围: {x_range}")
        print(f"y范围: {y_range}")

    def wave_function(self, t, frequency=1, amplitude=1, wavelength=2):
        """
        波浪函数: z = A * sin(2π * (r/λ - ft))
        其中r是到原点的距离

        参数:
        - t: 时间
        - frequency: 频率
        - amplitude: 振幅
        - wavelength: 波长
        """
        R = np.sqrt(self.X**2 + self.Y**2)
        Z = amplitude * np.sin(2 * np.pi * (R/wavelength - frequency*t))
        return Z

    def ripple_function(self, t, num_sources=2, amplitude=1):
        """
        涟漪函数: 多个点源的干涉

        参数:
        - t: 时间
        - num_sources: 激发源数量
        - amplitude: 振幅
        """
        Z = np.zeros_like(self.X)

        # 在不同位置放置激发源
        for i in range(num_sources):
            angle = 2 * np.pi * i / num_sources
            source_x = 2 * np.cos(angle)
            source_y = 2 * np.sin(angle)

            R = np.sqrt((self.X - source_x)**2 + (self.Y - source_y)**2)
            Z += amplitude * np.sin(2 * np.pi * (R - 2*t)) / (R + 0.5)

        return Z

    def interference_pattern(self, t, frequency=0.5):
        """
        干涉图案

        参数:
        - t: 时间
        - frequency: 频率
        """
        Z1 = np.sin(2 * np.pi * (self.X - frequency*t))
        Z2 = np.sin(2 * np.pi * (self.Y - frequency*t))
        Z3 = 0.5 * np.sin(2 * np.pi * ((self.X + self.Y)/np.sqrt(2) - frequency*t))

        return (Z1 + Z2 + Z3) / 2.5

    def gaussian_pulse(self, t, width=1, speed=2):
        """
        高斯脉冲

        参数:
        - t: 时间
        - width: 脉冲宽度
        - speed: 传播速度
        """
        r = np.sqrt(self.X**2 + self.Y**2)
        center = (t * speed) % (np.max(r) * 2)
        Z = np.exp(-((r - center)**2) / (2 * width**2))
        return Z

    def linear_gradient(self, t, direction='x', speed=1):
        """
        线性渐变 - 在指定方向上的线性渐变

        参数:
        - t: 时间
        - direction: 'x', 'y', 或 'xy' (对角线)
        - speed: 移动速度
        """
        if direction == 'x':
            # x方向渐变
            Z = (self.X - t * speed) / np.max(np.abs(self.X))
        elif direction == 'y':
            # y方向渐变
            Z = (self.Y - t * speed) / np.max(np.abs(self.Y))
        elif direction == 'xy':
            # 对角线渐变
            Z = (self.X + self.Y - t * speed) / (np.max(np.abs(self.X)) + np.max(np.abs(self.Y)))
        else:
            raise ValueError("方向必须是 'x', 'y', 或 'xy'")

        return Z

    def circular_gradient(self, t, inner_radius=0, outer_radius=5, speed=0.5):
        """
        圆形渐变 - 从中心向外的圆形渐变

        参数:
        - t: 时间
        - inner_radius: 内圆半径
        - outer_radius: 外圆半径
        - speed: 扩展速度
        """
        r = np.sqrt(self.X**2 + self.Y**2)
        current_outer = outer_radius + t * speed
        Z = np.clip((r - inner_radius) / (current_outer - inner_radius), 0, 1)
        return Z

    def radial_gradient(self, t, num_bands=5, speed=1):
        """
        径向渐变 - 同心圆条纹渐变

        参数:
        - t: 时间
        - num_bands: 条纹数量
        - speed: 旋转/移动速度
        """
        r = np.sqrt(self.X**2 + self.Y**2)
        max_r = np.max(r)
        Z = (np.sin(2 * np.pi * num_bands * (r / max_r - t * speed)) + 1) / 2
        return Z

    def spiral_wave(self, t, arms=3, speed=1):
        """
        螺旋波 - 多臂螺旋波

        参数:
        - t: 时间
        - arms: 螺旋臂数量
        - speed: 旋转速度
        """
        r = np.sqrt(self.X**2 + self.Y**2)
        theta = np.arctan2(self.Y, self.X)

        # 创建螺旋波
        Z = np.sin(arms * theta - 2 * np.pi * r / 5 - 2 * np.pi * speed * t)
        # 添加径向衰减
        Z *= np.exp(-r / 10)

        return Z

    def checkerboard(self, t, size=2, speed=0.5):
        """
        棋盘模式 - 动态变化的棋盘格

        参数:
        - t: 时间
        - size: 格子大小
        - speed: 动画速度
        """
        # 创建随时间移动的棋盘格
        Z = np.sin(2 * np.pi * (self.X / size - speed * t)) * \
            np.sin(2 * np.pi * (self.Y / size - speed * t))
        return Z

    def noise_field(self, t, scale=0.1, amplitude=1):
        """
        随机噪声场 - 使用简化的Perlin噪声模拟

        参数:
        - t: 时间
        - scale: 噪声尺度
        - amplitude: 振幅
        """
        # 简化的噪声函数
        Z = amplitude * (
            np.sin(scale * self.X + t) * np.cos(scale * self.Y) +
            np.sin(scale * self.X * 1.5 + t * 1.3) * np.cos(scale * self.Y * 0.7) * 0.5 +
            np.sin(scale * self.X * 2.3 + t * 0.7) * np.cos(scale * self.Y * 1.7) * 0.25
        )
        return Z

    def polynomial_surface(self, t, order=2, speed=0.5):
        """
        多项式表面 - 简单的多项式函数

        参数:
        - t: 时间
        - order: 多项式阶数 (1, 2, 或 3)
        - speed: 动画速度
        """
        if order == 1:
            # 线性函数
            Z = 0.1 * (self.X + self.Y) * np.cos(t * speed)
        elif order == 2:
            # 二次函数 (抛物面)
            r2 = self.X**2 + self.Y**2
            Z = (r2 / 100) * np.sin(t * speed) - (r2 / 200)
        elif order == 3:
            # 三次函数
            Z = 0.01 * (self.X**3 - 3 * self.X * self.Y**2) * np.cos(t * speed)
        else:
            raise ValueError("阶数必须是 1, 2, 或 3")

        return Z

    def wedge_pattern(self, t, num_wedges=8, speed=1):
        """
        楔形模式 - 像披萨切片的楔形图案

        参数:
        - t: 时间
        - num_wedges: 楔形数量
        - speed: 旋转速度
        """
        theta = np.arctan2(self.Y, self.X)
        Z = np.sin(num_wedges * theta / 2 - t * speed)
        return Z

    def calculate_z_values(self, t, function_type='wave', **kwargs):
        """
        计算给定时间t时所有网格点的z值

        参数:
        - t: 时间
        - function_type: 函数类型 ('wave', 'ripple', 'interference', 'gaussian',
                             'linear_gradient', 'circular_gradient', 'radial_gradient',
                             'spiral_wave', 'checkerboard', 'noise_field',
                             'polynomial_surface', 'wedge_pattern')
        - **kwargs: 传递给具体函数的参数

        返回:
        - Z: z值矩阵
        - points: 网格点信息 [(x, y, z), ...]
        """
        if function_type == 'wave':
            Z = self.wave_function(t, **kwargs)
        elif function_type == 'ripple':
            Z = self.ripple_function(t, **kwargs)
        elif function_type == 'interference':
            Z = self.interference_pattern(t, **kwargs)
        elif function_type == 'gaussian':
            Z = self.gaussian_pulse(t, **kwargs)
        elif function_type == 'linear_gradient':
            Z = self.linear_gradient(t, **kwargs)
        elif function_type == 'circular_gradient':
            Z = self.circular_gradient(t, **kwargs)
        elif function_type == 'radial_gradient':
            Z = self.radial_gradient(t, **kwargs)
        elif function_type == 'spiral_wave':
            Z = self.spiral_wave(t, **kwargs)
        elif function_type == 'checkerboard':
            Z = self.checkerboard(t, **kwargs)
        elif function_type == 'noise_field':
            Z = self.noise_field(t, **kwargs)
        elif function_type == 'polynomial_surface':
            Z = self.polynomial_surface(t, **kwargs)
        elif function_type == 'wedge_pattern':
            Z = self.wedge_pattern(t, **kwargs)
        else:
            raise ValueError(f"未知的函数类型: {function_type}")

        # 生成所有点的列表
        points = []
        for i in range(self.divisions):
            for j in range(self.divisions):
                points.append((self.X[i,j], self.Y[i,j], Z[i,j]))

        return Z, points

    def get_point_time_series(self, x_idx, y_idx, time_points, function_type='wave', **kwargs):
        """
        获取特定点随时间变化的z值序列

        参数:
        - x_idx, y_idx: 网格点的索引
        - time_points: 时间点数组
        - function_type: 函数类型
        - **kwargs: 函数参数

        返回:
        - z_values: z值时间序列
        """
        x_pos = self.x[x_idx]
        y_pos = self.y[y_idx]

        z_values = []
        for t in time_points:
            if function_type == 'wave':
                r = np.sqrt(x_pos**2 + y_pos**2)
                z = kwargs.get('amplitude', 1) * np.sin(2 * np.pi * (r/kwargs.get('wavelength', 2) - kwargs.get('frequency', 1)*t))
            elif function_type == 'ripple':
                z = 0
                num_sources = kwargs.get('num_sources', 2)
                amplitude = kwargs.get('amplitude', 1)
                for i in range(num_sources):
                    angle = 2 * np.pi * i / num_sources
                    source_x = 2 * np.cos(angle)
                    source_y = 2 * np.sin(angle)
                    r = np.sqrt((x_pos - source_x)**2 + (y_pos - source_y)**2)
                    z += amplitude * np.sin(2 * np.pi * (r - 2*t)) / (r + 0.5)
            z_values.append(z)

        return z_values

    def plot_surface(self, Z, title='动态表面'):
        """绘制3D表面"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(self.X, self.Y, Z, cmap=cm.viridis,
                              linewidth=0, antialiased=True, alpha=0.8)

        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        ax.set_zlabel('Z轴')
        ax.set_title(title)

        fig.colorbar(surf, shrink=0.5, aspect=5)

        return fig, ax

    def animate_surface(self, function_type='wave', duration=5, fps=30, **kwargs):
        """
        创建表面动画

        参数:
        - function_type: 函数类型
        - duration: 动画持续时间(秒)
        - fps: 帧率
        - **kwargs: 函数参数
        """
        frames = duration * fps
        time_points = np.linspace(0, duration, frames)

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # 初始化表面
        Z_init = self.calculate_z_values(0, function_type, **kwargs)[0]
        surf = ax.plot_surface(self.X, self.Y, Z_init, cmap=cm.viridis,
                              linewidth=0, antialiased=True, alpha=0.8)

        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        ax.set_zlabel('Z轴')
        ax.set_title(f'{function_type} 动态表面')

        def update(frame):
            ax.clear()
            t = time_points[frame]
            Z = self.calculate_z_values(t, function_type, **kwargs)[0]

            ax.plot_surface(self.X, self.Y, Z, cmap=cm.viridis,
                          linewidth=0, antialiased=True, alpha=0.8)

            ax.set_xlabel('X轴')
            ax.set_ylabel('Y轴')
            ax.set_zlabel('Z轴')
            ax.set_title(f'{function_type} 动态表面 (t={t:.2f}s)')

            # 保持固定的z轴范围
            ax.set_zlim(-3, 3)

            return ax,

        anim = FuncAnimation(fig, update, frames=frames, interval=1000/fps, blit=False)

        return fig, anim

# 使用示例
if __name__ == "__main__":
    # 创建40x40的网格
    grid = DynamicSurfaceGrid(x_range=(-10, 10), y_range=(-10, 10), divisions=40)

    # 计算t=0时刻的波浪函数
    Z, points = grid.calculate_z_values(t=0, function_type='wave', frequency=1, amplitude=1, wavelength=2)

    print(f"\n前10个点的z值:")
    for i, (x, y, z) in enumerate(points[:10]):
        print(f"点{i+1}: x={x:.3f}, y={y:.3f}, z={z:.3f}")

    # 绘制表面
    fig, ax = grid.plot_surface(Z, 't=0时刻的波浪表面')
    plt.show()

    # 获取中心点(20,20)的时间序列
    time_points = np.linspace(0, 5, 100)
    z_series = grid.get_point_time_series(20, 20, time_points,
                                         function_type='wave',
                                         frequency=1, amplitude=1, wavelength=2)

    print(f"\n中心点(20,20)在5秒内的z值变化:")
    print(f"初始z值: {z_series[0]:.3f}")
    print(f"最终z值: {z_series[-1]:.3f}")
    print(f"最大z值: {max(z_series):.3f}")
    print(f"最小z值: {min(z_series):.3f}")