import numpy as np
import matplotlib.pyplot as plt
from dynamic_surface_grid import DynamicSurfaceGrid

def demo_all_functions():
    """演示所有可用的动态函数"""

    # 创建20x20的网格用于快速演示
    grid = DynamicSurfaceGrid(x_range=(-5, 5), y_range=(-5, 5), divisions=20)

    # 要演示的函数列表
    functions = [
        ('wave', {'frequency': 1, 'amplitude': 1, 'wavelength': 2}),
        ('ripple', {'num_sources': 3, 'amplitude': 1}),
        ('interference', {'frequency': 0.5}),
        ('gaussian', {'width': 1, 'speed': 2}),
        ('linear_gradient', {'direction': 'xy', 'speed': 0.5}),
        ('circular_gradient', {'inner_radius': 0, 'outer_radius': 5, 'speed': 0.3}),
        ('radial_gradient', {'num_bands': 5, 'speed': 0.5}),
        ('spiral_wave', {'arms': 3, 'speed': 0.5}),
        ('checkerboard', {'size': 2, 'speed': 0.5}),
        ('noise_field', {'scale': 0.2, 'amplitude': 1}),
        ('polynomial_surface', {'order': 2, 'speed': 0.5}),
        ('wedge_pattern', {'num_wedges': 8, 'speed': 0.5})
    ]

    # 创建3x4的子图布局
    fig = plt.figure(figsize=(16, 12))

    for idx, (func_name, params) in enumerate(functions):
        ax = fig.add_subplot(3, 4, idx + 1, projection='3d')

        # 计算t=0时刻的z值
        Z = grid.calculate_z_values(t=0, function_type=func_name, **params)[0]

        # 绘制表面
        surf = ax.plot_surface(grid.X, grid.Y, Z, cmap='viridis',
                              linewidth=0, antialiased=True, alpha=0.8)

        # 设置标题和标签
        ax.set_title(f'{func_name}', fontsize=10)
        ax.set_xlabel('X', fontsize=8)
        ax.set_ylabel('Y', fontsize=8)
        ax.set_zlabel('Z', fontsize=8)

        # 设置视角
        ax.view_init(elev=30, azim=45)

        # 固定z轴范围
        ax.set_zlim(-3, 3)

        # 刻度字体大小
        ax.tick_params(axis='x', labelsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.tick_params(axis='z', labelsize=7)

    plt.suptitle('动态表面函数演示 (t=0)', fontsize=14, y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.show()

def demo_time_evolution():
    """演示特定函数的时间演化"""

    grid = DynamicSurfaceGrid(x_range=(-10, 10), y_range=(-10, 10), divisions=30)

    # 选择几个有趣的函数进行时间演化演示
    functions = [
        ('linear_gradient', {'direction': 'x', 'speed': 2}, 'X方向线性渐变'),
        ('spiral_wave', {'arms': 4, 'speed': 0.5}, '四臂螺旋波'),
        ('circular_gradient', {'inner_radius': 1, 'outer_radius': 6, 'speed': 1}, '扩展的圆形渐变'),
        ('radial_gradient', {'num_bands': 8, 'speed': 1}, '旋转的径向条纹')
    ]

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle('函数时间演化演示', fontsize=14)

    time_points = [0, 0.5, 1.0, 1.5]

    for row, (func_name, params, title) in enumerate(functions):
        for col, t in enumerate(time_points):
            ax = axes[row, col]
            Z = grid.calculate_z_values(t, func_name, **params)[0]

            # 使用二维颜色图显示
            im = ax.imshow(Z, cmap='viridis', origin='lower',
                          extent=[-10, 10, -10, 10], vmin=-3, vmax=3)

            ax.set_title(f'{title} (t={t}s)', fontsize=10)
            ax.set_xlabel('X', fontsize=8)
            ax.set_ylabel('Y', fontsize=8)
            ax.tick_params(labelsize=7)

    # 添加颜色条
    fig.subplots_adjust(right=0.9)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cbar_ax, label='Z值')

    plt.tight_layout()
    plt.show()

def demo_gradient_variations():
    """演示不同方向的渐变"""

    grid = DynamicSurfaceGrid(x_range=(-5, 5), y_range=(-5, 5), divisions=25)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('线性渐变方向对比', fontsize=14)

    directions = [
        ('x', 'X方向渐变'),
        ('y', 'Y方向渐变'),
        ('xy', '对角线渐变')
    ]

    for idx, (direction, title) in enumerate(directions):
        ax = axes[idx//2, idx%2]
        Z = grid.calculate_z_values(t=0, function_type='linear_gradient',
                                   direction=direction, speed=0)[0]

        im = ax.imshow(Z, cmap='viridis', origin='lower',
                      extent=[-5, 5, -5, 5])
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        plt.colorbar(im, ax=ax)

    # 第四个子图显示3D视图
    ax = axes[1, 1] = fig.add_subplot(224, projection='3d')
    Z = grid.calculate_z_values(t=0, function_type='linear_gradient',
                               direction='xy', speed=0)[0]
    ax.plot_surface(grid.X, grid.Y, Z, cmap='viridis', alpha=0.8)
    ax.set_title('对角线渐变 (3D)', fontsize=12)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("动态表面函数演示")
    print("=" * 50)
    print("\n1. 所有函数概览")
    demo_all_functions()

    print("\n2. 时间演化演示")
    demo_time_evolution()

    print("\n3. 渐变方向对比")
    demo_gradient_variations()