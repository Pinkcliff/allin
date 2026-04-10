#!/usr/bin/env python
"""
运行实时同步版动态表面分析系统
精确时间同步 + 预渲染缓存技术
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    try:
        print("=" * 70)
        print("动态表面分析系统 - 实时同步版")
        print("=" * 70)
        print("核心特性:")
        print("  - 精确时间同步: 软件时间与现实时间完全一致")
        print("  - 预渲染缓存: 提前计算所有帧，确保流畅播放")
        print("  - 双模式播放: 实时模式 + 预渲染模式")
        print("  - 性能监控: 实时FPS和时间偏差显示")
        print("  - 智能缓存: 自动管理动画帧缓存")
        print("-" * 70)
        print("正在启动实时同步系统...")

        from gui_realtime import RealtimeGUI

        # 创建并运行GUI
        app = RealtimeGUI()
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