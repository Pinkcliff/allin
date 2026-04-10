import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib.widgets import Slider
import matplotlib as mpl

# Set font to avoid Chinese display issues
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

class DynamicSurface:
    """
    动态曲面分析工具
    用于分析和可视化 z = f(x, y, t) 形式的动态曲面函数
    """

    def __init__(self, func=None):
        """
        初始化动态曲面

        Parameters:
        -----------
        func : callable
            曲面函数，形式为 func(x, y, t) -> z
            x, y, t 可以是标量或numpy数组
        """
        self.func = func
        if func is None:
            # 默认使用一个示例函数：波动曲面
            self.func = lambda x, y, t: np.sin(x + t) * np.cos(y - t) * np.exp(-0.1 * t)

    def evaluate_surface(self, x_range, y_range, t, resolution=50):
        """
        在给定时间t计算曲面上的值

        Parameters:
        -----------
        x_range : tuple
            x的范围 (x_min, x_max)
        y_range : tuple
            y的范围 (y_min, y_max)
        t : float
            时间参数
        resolution : int
            网格分辨率

        Returns:
        --------
        X, Y, Z : numpy arrays
            网格坐标和对应的z值
        """
        x = np.linspace(x_range[0], x_range[1], resolution)
        y = np.linspace(y_range[0], y_range[1], resolution)
        X, Y = np.meshgrid(x, y)
        Z = self.func(X, Y, t)
        return X, Y, Z

    def get_time_series_at_point(self, x0, y0, t_range, num_points=100):
        """
        获取固定点(x0, y0)处z值随时间的变化

        Parameters:
        -----------
        x0, y0 : float
            固定坐标点
        t_range : tuple
            时间范围 (t_min, t_max)
        num_points : int
            时间点数量

        Returns:
        --------
        t, z : numpy arrays
            时间序列和对应的z值
        """
        t = np.linspace(t_range[0], t_range[1], num_points)
        z = self.func(x0, y0, t)
        return t, z

    def plot_surface_at_time(self, x_range, y_range, t, save_path=None):
        """
        绘制特定时刻的曲面

        Parameters:
        -----------
        x_range, y_range : tuple
            坐标范围
        t : float
            时间
        save_path : str, optional
            保存路径
        """
        X, Y, Z = self.evaluate_surface(x_range, y_range, t)

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'Dynamic Surface at t = {t:.2f}')

        fig.colorbar(surf)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_time_series(self, x0, y0, t_range, save_path=None):
        """
        绘制固定点的时间序列

        Parameters:
        -----------
        x0, y0 : float
            固定坐标点
        t_range : tuple
            时间范围
        save_path : str, optional
            保存路径
        """
        t, z = self.get_time_series_at_point(x0, y0, t_range)

        plt.figure(figsize=(10, 6))
        plt.plot(t, z, linewidth=2)
        plt.xlabel('Time (t)')
        plt.ylabel('Z Value')
        plt.title(f'Z Value Variation Over Time at Point ({x0}, {y0})')
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def interactive_surface_with_slider(self, x_range, y_range, t_range, resolution=50):
        """
        创建带时间滑块的交互式3D曲面

        Parameters:
        -----------
        x_range, y_range : tuple
            坐标范围
        t_range : tuple
            时间范围 (t_min, t_max)
        resolution : int
            曲面网格分辨率
        """
        # 创建图形和3D坐标轴
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d', position=[0.05, 0.25, 0.9, 0.7])

        # 创建初始曲面
        t_init = (t_range[0] + t_range[1]) / 2
        X, Y, Z = self.evaluate_surface(x_range, y_range, t_init, resolution)

        # 绘制初始曲面
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'Dynamic Surface at t = {t_init:.2f}')

        # 添加颜色条
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        # 为滑块创建坐标轴
        ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03])

        # 创建滑块
        time_slider = Slider(
            ax=ax_slider,
            label='Time',
            valmin=t_range[0],
            valmax=t_range[1],
            valinit=t_init,
            valstep=(t_range[1] - t_range[0]) / 100
        )

        # 滑块更新函数
        def update_surface(val):
            ax.clear()
            t = time_slider.val
            X, Y, Z = self.evaluate_surface(x_range, y_range, t, resolution)

            surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(f'Dynamic Surface at t = {t:.2f}')

            # 保持z轴范围一致
            z_min, z_max = self._get_z_range(x_range, y_range, t_range)
            ax.set_zlim(z_min, z_max)

            fig.canvas.draw_idle()

        # 将滑块连接到更新函数
        time_slider.on_changed(update_surface)

        plt.show()

    def create_animation(self, x_range, y_range, t_range, frames=50, interval=100):
        """
        创建曲面随时间变化的动画

        Parameters:
        -----------
        x_range, y_range : tuple
            坐标范围
        t_range : tuple
            时间范围
        frames : int
            动画帧数
        interval : int
            帧间隔（毫秒）
        """
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        X, Y = np.meshgrid(
            np.linspace(x_range[0], x_range[1], 50),
            np.linspace(y_range[0], y_range[1], 50)
        )

        t_values = np.linspace(t_range[0], t_range[1], frames)

        def update(frame):
            ax.clear()
            t = t_values[frame]
            Z = self.func(X, Y, t)

            surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(f'Dynamic Surface at t = {t:.2f}')

            # 设置固定的z轴范围
            z_min, z_max = self._get_z_range(x_range, y_range, t_range)
            ax.set_zlim(z_min, z_max)

            return [surf]

        anim = FuncAnimation(fig, update, frames=frames, interval=interval, blit=False)

        plt.show()
        return anim

    def _get_z_range(self, x_range, y_range, t_range, samples=10):
        """获取z值的范围"""
        t_samples = np.linspace(t_range[0], t_range[1], samples)
        z_values = []

        for t in t_samples:
            X, Y, Z = self.evaluate_surface(x_range, y_range, t, resolution=30)
            z_values.extend(Z.flatten())

        return min(z_values), max(z_values)

    def interactive_plot(self, x_range, y_range, t_range):
        """
        使用Plotly创建交互式可视化

        Parameters:
        -----------
        x_range, y_range, t_range : tuple
            坐标和时间范围
        """
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "surface"}, {"type": "xy"}],
                   [{"type": "xy"}, {"type": "xy"}]],
            subplot_titles=["3D Surface", "Contour Plot", "Time Series", "Multi-point Comparison"]
        )

        # 初始时刻
        t_init = (t_range[0] + t_range[1]) / 2
        X, Y, Z = self.evaluate_surface(x_range, y_range, t_init)

        # 3D曲面
        fig.add_trace(
            go.Surface(x=X[0], y=Y[:, 0], z=Z, colorscale='Viridis'),
            row=1, col=1
        )

        # 等高线图
        fig.add_trace(
            go.Contour(x=X[0], y=Y[:, 0], z=Z, colorscale='Viridis'),
            row=1, col=2
        )

        # 时间序列示例
        t_series = np.linspace(t_range[0], t_range[1], 100)
        z_series = self.func(x_range[0]/2, y_range[0]/2, t_series)
        fig.add_trace(
            go.Scatter(x=t_series, y=z_series, mode='lines'),
            row=2, col=1
        )

        fig.update_layout(
            title="Dynamic Surface Interactive Visualization",
            height=800,
            showlegend=False
        )

        fig.show()


def example_usage():
    """示例用法"""

    # 定义一个动态曲面函数
    def wave_surface(x, y, t):
        """波动曲面示例"""
        return np.sin(np.sqrt(x**2 + y**2) - 2*t) * np.exp(-0.1*t)

    # 创建动态曲面实例
    ds = DynamicSurface(wave_surface)

    # 设置范围
    x_range = (-5, 5)
    y_range = (-5, 5)
    t_range = (0, 10)

    # 1. 绘制特定时刻的曲面
    ds.plot_surface_at_time(x_range, y_range, t=2)

    # 2. 绘制固定点的时间序列
    ds.plot_time_series(x0=1, y0=1, t_range=t_range)

    # 3. 新增：带时间滑块的交互式曲面
    ds.interactive_surface_with_slider(x_range, y_range, t_range)

    # 4. 创建动画（可选）
    # ds.create_animation(x_range, y_range, t_range, frames=50)

    # 5. 交互式Plotly可视化
    # ds.interactive_plot(x_range, y_range, t_range)


if __name__ == "__main__":
    example_usage()