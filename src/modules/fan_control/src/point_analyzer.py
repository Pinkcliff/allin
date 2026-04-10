import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from typing import List, Tuple, Dict

class PointAnalyzer:
    """
    固定点分析器
    用于分析曲面上多个固定点处z值随时间的变化
    """

    def __init__(self, surface_func):
        """
        初始化分析器

        Parameters:
        -----------
        surface_func : callable
            曲面函数 f(x, y, t) -> z
        """
        self.surface_func = surface_func
        self.points_data = {}

    def add_point(self, x: float, y: float, label: str = None):
        """
        添加要分析的固定点

        Parameters:
        -----------
        x, y : float
            点的坐标
        label : str, optional
            点的标签，用于显示
        """
        if label is None:
            label = f'({x:.2f}, {y:.2f})'
        self.points_data[label] = (x, y)

    def analyze_points(self, t_range: Tuple[float, float], num_points: int = 100):
        """
        分析所有添加的点

        Parameters:
        -----------
        t_range : tuple
            时间范围 (t_min, t_max)
        num_points : int
            时间采样点数

        Returns:
        --------
        DataFrame
            包含所有点时间序列的DataFrame
        """
        t = np.linspace(t_range[0], t_range[1], num_points)
        data = {'时间': t}

        for label, (x, y) in self.points_data.items():
            z = self.surface_func(x, y, t)
            data[label] = z

        return pd.DataFrame(data)

    def plot_multiple_points(self, t_range: Tuple[float, float],
                           num_points: int = 100, save_path: str = None):
        """
        绘制多个点的时间序列

        Parameters:
        -----------
        t_range : tuple
            时间范围
        num_points : int
            时间采样点数
        save_path : str, optional
            保存路径
        """
        df = self.analyze_points(t_range, num_points)

        plt.figure(figsize=(12, 8))

        for label in self.points_data.keys():
            plt.plot(df['时间'], df[label], label=label, linewidth=2)

        plt.xlabel('时间 (t)', fontsize=12)
        plt.ylabel('Z 值', fontsize=12)
        plt.title('多个固定点处 Z 值随时间的变化', fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.show()

    def plot_heatmap(self, t_range: Tuple[float, float],
                    grid_size: Tuple[int, int] = (20, 20)):
        """
        创建时空热力图，显示z值在时空中的分布

        Parameters:
        -----------
        t_range : tuple
            时间范围
        grid_size : tuple
            空间网格大小
        """
        # 创建空间网格
        x_range = (-5, 5)  # 可根据需要调整
        y_range = (-5, 5)

        x = np.linspace(x_range[0], x_range[1], grid_size[0])
        y = np.linspace(y_range[0], y_range[1], grid_size[1])

        t_samples = np.linspace(t_range[0], t_range[1], 50)

        # 创建子图
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for idx, t in enumerate(t_samples[:6]):
            ax = axes[idx]

            X, Y = np.meshgrid(x, y)
            Z = self.surface_func(X, Y, t)

            im = ax.contourf(X, Y, Z, levels=20, cmap='viridis')
            ax.set_title(f't = {t:.2f}')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')

            # 标记分析的点
            for label, (px, py) in self.points_data.items():
                ax.plot(px, py, 'r*', markersize=10)
                ax.annotate(label, (px, py), xytext=(5, 5),
                           textcoords='offset points', color='white')

            plt.colorbar(im, ax=ax)

        plt.suptitle('时空热力图：Z值在不同时刻的空间分布', fontsize=16)
        plt.tight_layout()
        plt.show()

    def create_composite_plot(self, t_range: Tuple[float, float],
                            num_points: int = 100):
        """
        创建复合图：同时显示3D曲面和时间序列

        Parameters:
        -----------
        t_range : tuple
            时间范围
        num_points : int
            时间采样点数
        """
        fig = plt.figure(figsize=(16, 10))

        # 3D曲面子图
        ax1 = fig.add_subplot(121, projection='3d')
        t_mid = (t_range[0] + t_range[1]) / 2

        X = np.linspace(-5, 5, 50)
        Y = np.linspace(-5, 5, 50)
        X_grid, Y_grid = np.meshgrid(X, Y)
        Z_grid = self.surface_func(X_grid, Y_grid, t_mid)

        surf = ax1.plot_surface(X_grid, Y_grid, Z_grid, alpha=0.7, cmap='viridis')

        # 标记分析的点
        for label, (x, y) in self.points_data.items():
            z = self.surface_func(x, y, t_mid)
            ax1.scatter([x], [y], [z], color='red', s=100, label=label)

        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        ax1.set_title(f'曲面在 t = {t_mid:.2f}')

        # 时间序列子图
        ax2 = fig.add_subplot(122)
        df = self.analyze_points(t_range, num_points)

        for label in self.points_data.keys():
            ax2.plot(df['时间'], df[label], label=label, linewidth=2)

        ax2.axvline(x=t_mid, color='gray', linestyle='--', alpha=0.5)
        ax2.set_xlabel('时间 (t)')
        ax2.set_ylabel('Z 值')
        ax2.set_title('时间序列')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def export_data(self, t_range: Tuple[float, float],
                   num_points: int = 100, filename: str = 'point_data.csv'):
        """
        导出分析数据到CSV文件

        Parameters:
        -----------
        t_range : tuple
            时间范围
        num_points : int
            时间采样点数
        filename : str
            输出文件名
        """
        df = self.analyze_points(t_range, num_points)
        df.to_csv(filename, index=False)
        print(f"数据已导出到 {filename}")


def demo_point_analysis():
    """演示固定点分析"""

    # 定义一个更复杂的动态曲面
    def complex_surface(x, y, t):
        """复杂动态曲面示例"""
        # 径向波动
        r = np.sqrt(x**2 + y**2)
        wave = np.sin(r - 2*t) * np.exp(-0.05*t)
        # 行波
        wave2 = 0.5 * np.sin(x + t) * np.cos(y - t)
        return wave + wave2

    # 创建分析器
    analyzer = PointAnalyzer(complex_surface)

    # 添加要分析的点
    analyzer.add_point(0, 0, "中心点")
    analyzer.add_point(2, 2, "第一象限")
    analyzer.add_point(-2, 2, "第二象限")
    analyzer.add_point(-2, -2, "第三象限")
    analyzer.add_point(2, -2, "第四象限")
    analyzer.add_point(3, 0, "X轴上")
    analyzer.add_point(0, 3, "Y轴上")

    # 设置时间范围
    t_range = (0, 15)

    # 1. 绘制多个点的时间序列
    analyzer.plot_multiple_points(t_range)

    # 2. 创建时空热力图
    analyzer.plot_heatmap(t_range)

    # 3. 创建复合图
    analyzer.create_composite_plot(t_range)

    # 4. 导出数据
    analyzer.export_data(t_range, filename='surface_points_data.csv')


if __name__ == "__main__":
    demo_point_analysis()