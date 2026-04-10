"""
主程序
用于分析动态曲面 z = f(x, y, t)
"""

import numpy as np
import matplotlib.pyplot as plt
from dynamic_surface import DynamicSurface
from point_analyzer import PointAnalyzer
from config import SURFACE_FUNCTIONS, DEFAULT_CONFIG
import argparse

def analyze_your_function(func, points_to_analyze=None, config=None):
    """
    分析您的动态曲面函数

    Parameters:
    -----------
    func : callable
        您的曲面函数 f(x, y, t)
    points_to_analyze : list of tuples, optional
        要分析的点列表 [(x1, y1, label1), (x2, y2, label2), ...]
    config : dict, optional
        配置参数
    """
    if config is None:
        config = DEFAULT_CONFIG

    # 创建动态曲面实例
    ds = DynamicSurface(func)

    # 1. 显示不同时刻的曲面
    print("\n1. 显示不同时刻的曲面...")
    times = [config['t_range'][0],
             np.mean(config['t_range']),
             config['t_range'][1]]

    for t in times:
        print(f"   绘制 t = {t:.2f} 时刻的曲面")
        ds.plot_surface_at_time(
            config['x_range'],
            config['y_range'],
            t
        )

    # 2. 分析特定点的时间序列
    if points_to_analyze:
        print("\n2. 分析特定点的时间序列...")
        analyzer = PointAnalyzer(func)

        for x, y, label in points_to_analyze:
            analyzer.add_point(x, y, label)

        # 绘制时间序列
        analyzer.plot_multiple_points(config['t_range'])

        # 创建时空热力图
        analyzer.plot_heatmap(config['t_range'])

        # 创建复合图
        analyzer.create_composite_plot(config['t_range'])

        # 导出数据
        analyzer.export_data(config['t_range'])

    # 3. 创建动画（可选）
    print("\n3. 创建动画...")
    response = input("是否创建曲面动画？(y/n): ")
    if response.lower() == 'y':
        print("   生成动画中（可能需要一些时间）...")
        ds.create_animation(
            config['x_range'],
            config['y_range'],
            config['t_range'],
            frames=30
        )

def interactive_mode():
    """交互式模式"""
    print("\n=== 交互式动态曲面分析器 ===\n")

    # 选择函数
    print("可用的示例函数：")
    for i, name in enumerate(SURFACE_FUNCTIONS.keys()):
        if name != 'custom':
            print(f"{i+1}. {name}")
    print(f"{len(SURFACE_FUNCTIONS)}. 自定义函数")

    choice = input("\n选择函数（输入数字）: ")

    try:
        choice_idx = int(choice) - 1
        func_names = list(SURFACE_FUNCTIONS.keys())

        if 0 <= choice_idx < len(func_names):
            func_name = func_names[choice_idx]

            if func_name == 'custom':
                print("\n请在 config.py 中的 your_function 函数中定义您的函数")
                func = SURFACE_FUNCTIONS['custom']
            else:
                func = SURFACE_FUNCTIONS[func_name]
                print(f"\n选择了函数: {func_name}")
        else:
            print("无效选择，使用默认函数")
            func = SURFACE_FUNCTIONS['simple_wave']
    except:
        print("无效输入，使用默认函数")
        func = SURFACE_FUNCTIONS['simple_wave']

    # 输入参数范围
    print("\n输入参数范围（按Enter使用默认值）:")

    x_min = input("x 最小值（默认 -5）: ") or -5
    x_max = input("x 最大值（默认 5）: ") or 5
    y_min = input("y 最小值（默认 -5）: ") or -5
    y_max = input("y 最大值（默认 5）: ") or 5
    t_min = input("t 最小值（默认 0）: ") or 0
    t_max = input("t 最大值（默认 10）: ") or 10

    config = {
        'x_range': (float(x_min), float(x_max)),
        'y_range': (float(y_min), float(y_max)),
        't_range': (float(t_min), float(t_max)),
        'resolution': 50,
        'num_time_points': 100
    }

    # 输入要分析的点
    print("\n输入要分析的固定点（格式：x y 标签），输入空行结束：")
    points = []
    while True:
        point_input = input("点（例如：0 0 中心点）: ")
        if not point_input:
            break
        try:
            parts = point_input.split()
            if len(parts) >= 2:
                x = float(parts[0])
                y = float(parts[1])
                label = parts[2] if len(parts) > 2 else f"({x}, {y})"
                points.append((x, y, label))
        except:
            print("输入格式错误，请重试")

    # 开始分析
    analyze_your_function(func, points, config)

def demo_mode():
    """演示模式"""
    print("\n=== 演示模式 ===\n")

    # 使用干涉图样作为示例
    func = SURFACE_FUNCTIONS['interference']

    # 定义一些有趣的点
    points = [
        (0, 0, "原点"),
        (2, 0, "第一个波源"),
        (-2, 0, "第二个波源"),
        (0, 2, "中间点"),
        (3, 3, "远场点")
    ]

    config = {
        'x_range': (-8, 8),
        'y_range': (-8, 8),
        't_range': (0, 20),
        'resolution': 50,
        'num_time_points': 100
    }

    print("正在分析双波源干涉图样...")
    analyze_your_function(func, points, config)

def main():
    parser = argparse.ArgumentParser(description='动态曲面分析工具')
    parser.add_argument('--mode', choices=['interactive', 'demo'],
                       default='interactive',
                       help='运行模式')
    args = parser.parse_args()

    if args.mode == 'demo':
        demo_mode()
    else:
        interactive_mode()

if __name__ == "__main__":
    # 设置matplotlib中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    main()