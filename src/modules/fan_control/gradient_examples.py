import numpy as np
import matplotlib.pyplot as plt
from dynamic_surface_grid import DynamicSurfaceGrid

def demonstrate_gradients():
    """演示各种渐变函数"""
    grid = DynamicSurfaceGrid(x_range=(-10, 10), y_range=(-10, 10), divisions=50)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 1. X方向线性渐变动画
    ax = axes[0, 0]
    Z1 = grid.calculate_z_values(t=0, function_type='linear_gradient',
                                direction='x', speed=2)[0]
    im1 = ax.imshow(Z1, cmap='viridis', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('X方向线性渐变')
    plt.colorbar(im1, ax=ax, fraction=0.046)

    # 2. 圆形渐变（扩展动画）
    ax = axes[0, 1]
    Z2 = grid.calculate_z_values(t=1, function_type='circular_gradient',
                                inner_radius=1, outer_radius=4, speed=1)[0]
    im2 = ax.imshow(Z2, cmap='plasma', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('扩展的圆形渐变')
    plt.colorbar(im2, ax=ax, fraction=0.046)

    # 3. 径向条纹渐变
    ax = axes[0, 2]
    Z3 = grid.calculate_z_values(t=0.5, function_type='radial_gradient',
                                num_bands=10, speed=1)[0]
    im3 = ax.imshow(Z3, cmap='coolwarm', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('旋转的径向条纹')
    plt.colorbar(im3, ax=ax, fraction=0.046)

    # 4. 螺旋波
    ax = axes[1, 0]
    Z4 = grid.calculate_z_values(t=0.5, function_type='spiral_wave',
                                arms=4, speed=0.5)[0]
    im4 = ax.imshow(Z4, cmap='twilight', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('四臂螺旋波')
    plt.colorbar(im4, ax=ax, fraction=0.046)

    # 5. 棋盘模式
    ax = axes[1, 1]
    Z5 = grid.calculate_z_values(t=0, function_type='checkerboard',
                                size=3, speed=0)[0]
    im5 = ax.imshow(Z5, cmap='RdBu', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('棋盘模式')
    plt.colorbar(im5, ax=ax, fraction=0.046)

    # 6. 楔形模式（披萨切片）
    ax = axes[1, 2]
    Z6 = grid.calculate_z_values(t=0, function_type='wedge_pattern',
                                num_wedges=12, speed=0)[0]
    im6 = ax.imshow(Z6, cmap='hsv', origin='lower',
                   extent=[-10, 10, -10, 10])
    ax.set_title('楔形模式（12片）')
    plt.colorbar(im6, ax=ax, fraction=0.046)

    plt.suptitle('各种渐变和模式函数演示', fontsize=16)
    plt.tight_layout()
    plt.show()

def polynomial_demo():
    """演示多项式函数"""
    grid = DynamicSurfaceGrid(x_range=(-5, 5), y_range=(-5, 5), divisions=50)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 1阶多项式（线性）
    ax = axes[0]
    Z1 = grid.calculate_z_values(t=0, function_type='polynomial_surface',
                                order=1)[0]
    im1 = ax.imshow(Z1, cmap='seismic', origin='lower',
                   extent=[-5, 5, -5, 5], vmin=-1, vmax=1)
    ax.set_title('1阶多项式（线性平面）')
    plt.colorbar(im1, ax=ax)

    # 2阶多项式（抛物面）
    ax = axes[1]
    Z2 = grid.calculate_z_values(t=0, function_type='polynomial_surface',
                                order=2)[0]
    im2 = ax.imshow(Z2, cmap='terrain', origin='lower',
                   extent=[-5, 5, -5, 5])
    ax.set_title('2阶多项式（抛物面）')
    plt.colorbar(im2, ax=ax)

    # 3阶多项式
    ax = axes[2]
    Z3 = grid.calculate_z_values(t=0, function_type='polynomial_surface',
                                order=3)[0]
    im3 = ax.imshow(Z3, cmap='prism', origin='lower',
                   extent=[-5, 5, -5, 5])
    ax.set_title('3阶多项式（鞍形曲面）')
    plt.colorbar(im3, ax=ax)

    plt.suptitle('多项式表面函数演示', fontsize=16)
    plt.tight_layout()
    plt.show()

def noise_demo():
    """演示噪声场"""
    grid = DynamicSurfaceGrid(x_range=(-10, 10), y_range=(-10, 10), divisions=50)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 不同尺度的噪声
    scales = [0.1, 0.2, 0.5]
    titles = ['细粒度噪声', '中等噪声', '粗粒度噪声']

    for ax, scale, title in zip(axes, scales, titles):
        Z = grid.calculate_z_values(t=0, function_type='noise_field',
                                   scale=scale)[0]
        im = ax.imshow(Z, cmap='gray', origin='lower',
                      extent=[-10, 10, -10, 10])
        ax.set_title(f'{title} (scale={scale})')
        plt.colorbar(im, ax=ax)

    plt.suptitle('噪声场函数演示', fontsize=16)
    plt.tight_layout()
    plt.show()

def combine_functions():
    """演示如何组合多个函数"""
    grid = DynamicSurfaceGrid(x_range=(-10, 10), y_range=(-10, 10), divisions=50)

    # 组合多个函数
    Z1, _ = grid.calculate_z_values(t=0, function_type='spiral_wave', arms=3)
    Z2, _ = grid.calculate_z_values(t=0, function_type='radial_gradient', num_bands=5)

    # 加权组合
    Z_combined = 0.6 * Z1 + 0.4 * Z2

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 原始函数1
    im1 = axes[0].imshow(Z1, cmap='viridis', origin='lower',
                        extent=[-10, 10, -10, 10])
    axes[0].set_title('螺旋波')
    plt.colorbar(im1, ax=axes[0])

    # 原始函数2
    im2 = axes[1].imshow(Z2, cmap='plasma', origin='lower',
                        extent=[-10, 10, -10, 10])
    axes[1].set_title('径向渐变')
    plt.colorbar(im2, ax=axes[1])

    # 组合结果
    im3 = axes[2].imshow(Z_combined, cmap='magma', origin='lower',
                        extent=[-10, 10, -10, 10])
    axes[2].set_title('组合效果 (60%螺旋波 + 40%径向渐变)')
    plt.colorbar(im3, ax=axes[2])

    plt.suptitle('函数组合演示', fontsize=16)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("渐变函数演示")
    print("=" * 50)

    print("\n1. 基本渐变和模式")
    demonstrate_gradients()

    print("\n2. 多项式表面")
    polynomial_demo()

    print("\n3. 噪声场")
    noise_demo()

    print("\n4. 函数组合")
    combine_functions()