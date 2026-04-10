#!/usr/bin/env python
"""
运行优化版动态表面分析系统
解决时间同步问题 + 13种数学函数模板 + 性能优化
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    try:
        print("=" * 70)
        print("动态表面分析系统 - 优化版")
        print("=" * 70)
        print("核心改进:")
        print("  - 时间同步优化: 解决渲染延迟导致的时间不同步")
        print("  - 13种数学函数: 基础波形+渐变+复杂波场+数学曲面")
        print("  - 异步渲染: 切换函数不再卡顿")
        print("  - 性能优化: 三档渲染质量 + 帧跳跃模式")
        print("  - 智能缓存: 避免重复计算")
        print("-" * 70)
        print("函数库:")
        print("  基础波形: 简单波、径向波")
        print("  调制波形: 高斯波包、驻波")
        print("  渐变图案: 线性渐变、径向渐变、棋盘格")
        print("  复杂波场: 螺旋波、干涉图样、噪声场")
        print("  数学曲面: 多项式曲面、鞍形点")
        print("-" * 70)
        print("正在启动优化系统...")

        from gui_optimized import OptimizedGUI

        # 创建并运行GUI
        app = OptimizedGUI()
        app.run()

    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖模块已正确安装")
        input("按回车键退出...")
        sys.exit(1)

    except Exception as e:
        print(f"运行错误: {e}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()