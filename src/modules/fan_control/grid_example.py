from dynamic_surface_grid import DynamicSurfaceGrid
import numpy as np
import matplotlib.pyplot as plt

def main():
    print("动态表面网格演示")
    print("=" * 50)

    # 用户输入参数
    range_val = float(input("请输入x和y的范围长度 (例如10表示-5到5): "))
    divisions = int(input("请输入每个轴的分割份数 (例如40): "))

    # 创建网格
    half_range = range_val / 2
    grid = DynamicSurfaceGrid(
        x_range=(-half_range, half_range),
        y_range=(-half_range, half_range),
        divisions=divisions
    )

    print("\n可选的动态函数:")
    print("1. wave - 波浪函数")
    print("2. ripple - 涟漪干涉")
    print("3. interference - 干涉图案")
    print("4. gaussian - 高斯脉冲")
    print("5. linear_gradient - 线性渐变")
    print("6. circular_gradient - 圆形渐变")
    print("7. radial_gradient - 径向渐变")
    print("8. spiral_wave - 螺旋波")
    print("9. checkerboard - 棋盘模式")
    print("10. noise_field - 随机噪声场")
    print("11. polynomial_surface - 多项式表面")
    print("12. wedge_pattern - 楔形模式")

    choice = input("\n选择函数类型 (1-12): ")
    function_map = {
        '1': 'wave',
        '2': 'ripple',
        '3': 'interference',
        '4': 'gaussian',
        '5': 'linear_gradient',
        '6': 'circular_gradient',
        '7': 'radial_gradient',
        '8': 'spiral_wave',
        '9': 'checkerboard',
        '10': 'noise_field',
        '11': 'polynomial_surface',
        '12': 'wedge_pattern'
    }
    function_type = function_map.get(choice, 'wave')

    # 计算并显示结果
    print("\n计算中...")
    Z, points = grid.calculate_z_values(t=0, function_type=function_type)

    # 显示统计信息
    print(f"\n统计信息:")
    print(f"总点数: {len(points)}")
    print(f"最大z值: {np.max(Z):.3f}")
    print(f"最小z值: {np.min(Z):.3f}")
    print(f"平均z值: {np.mean(Z):.3f}")

    # 绘制表面图
    fig, ax = grid.plot_surface(Z, f'{function_type} 表面 (t=0)')
    plt.show()

    # 询问是否要生成时间序列数据
    answer = input("\n是否要生成特定点的时间序列数据? (y/n): ")
    if answer.lower() == 'y':
        x_idx = int(input(f"输入x轴索引 (0-{divisions-1}): "))
        y_idx = int(input(f"输入y轴索引 (0-{divisions-1}): "))
        duration = float(input("输入持续时间(秒): "))
        steps = int(input("输入时间步数: "))

        time_points = np.linspace(0, duration, steps)
        z_series = grid.get_point_time_series(x_idx, y_idx, time_points, function_type=function_type)

        x_pos = grid.x[x_idx]
        y_pos = grid.y[y_idx]

        print(f"\n点({x_idx},{y_idx})在({x_pos:.3f},{y_pos:.3f})处的z值变化:")
        print(f"时间范围: 0 - {duration}秒")
        print(f"最大z值: {max(z_series):.3f}")
        print(f"最小z值: {min(z_series):.3f}")

        # 绘制时间序列图
        plt.figure(figsize=(10, 6))
        plt.plot(time_points, z_series)
        plt.xlabel('时间 (秒)')
        plt.ylabel('Z值')
        plt.title(f'点({x_pos:.2f},{y_pos:.2f})的z值时间序列')
        plt.grid(True)
        plt.show()

    # 询问是否要导出数据
    answer = input("\n是否要导出所有点的数据到文件? (y/n): ")
    if answer.lower() == 'y':
        filename = input("输入文件名 (例如 grid_data.csv): ")
        export_data(grid, points, filename)

def export_data(grid, points, filename):
    """导出网格数据到CSV文件"""
    import csv

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Point', 'X', 'Y', 'Z'])

        for i, (x, y, z) in enumerate(points):
            writer.writerow([i+1, f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"])

    print(f"数据已导出到 {filename}")

if __name__ == "__main__":
    main()