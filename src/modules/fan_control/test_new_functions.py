from dynamic_surface_grid import DynamicSurfaceGrid
import numpy as np

# 创建一个小型网格进行测试
grid = DynamicSurfaceGrid(x_range=(-5, 5), y_range=(-5, 5), divisions=10)

# 测试所有新函数
test_cases = [
    ('linear_gradient', {}, '线性渐变'),
    ('circular_gradient', {}, '圆形渐变'),
    ('radial_gradient', {}, '径向渐变'),
    ('spiral_wave', {}, '螺旋波'),
    ('checkerboard', {}, '棋盘模式'),
    ('noise_field', {}, '噪声场'),
    ('polynomial_surface', {}, '多项式表面'),
    ('wedge_pattern', {}, '楔形模式')
]

print("测试新增的动态表面函数:")
print("=" * 60)

for func_name, params, desc in test_cases:
    try:
        # 计算t=0时刻的z值
        Z, points = grid.calculate_z_values(t=0, function_type=func_name, **params)

        # 显示统计信息
        print(f"\n{desc} ({func_name}):")
        print(f"  最大z值: {np.max(Z):.4f}")
        print(f"  最小z值: {np.min(Z):.4f}")
        print(f"  平均z值: {np.mean(Z):.4f}")
        print(f"  总点数: {len(points)}")
        print(f"  状态: [成功]")

    except Exception as e:
        print(f"\n{desc} ({func_name}):")
        print(f"  状态: [错误] - {str(e)}")

print("\n" + "=" * 60)
print("测试完成！")

# 特别测试线性渐变的不同方向
print("\n测试线性渐变的不同方向:")
print("-" * 40)

directions = ['x', 'y', 'xy']
for direction in directions:
    Z, _ = grid.calculate_z_values(t=0,
                                 function_type='linear_gradient',
                                 direction=direction)
    print(f"{direction}方向: min={np.min(Z):.3f}, max={np.max(Z):.3f}")

# 测试多项式不同阶数
print("\n测试多项式不同阶数:")
print("-" * 40)

orders = [1, 2, 3]
for order in orders:
    Z, _ = grid.calculate_z_values(t=0,
                                 function_type='polynomial_surface',
                                 order=order)
    print(f"{order}阶多项式: min={np.min(Z):.3f}, max={np.max(Z):.3f}")