#!/usr/bin/env python
"""
运行专业版动态表面分析系统
高分辨率自适应、60FPS动画、精美字体
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    try:
        print("=" * 60)
        print("动态表面分析系统 - 专业版 Pro")
        print("=" * 60)
        print("功能特性:")
        print("  - DPI自适应 - 不受分辨率影响")
        print("  - 60FPS高帧率动画")
        print("  - 精美字体渲染")
        print("  - 现代化UI设计")
        print("  - 优化内存使用")
        print("-" * 60)
        print("正在启动系统...")

        from gui_pro import ProGUI

        # 创建并运行GUI
        app = ProGUI()
        app.run()

    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖模块已正确安装:")
        print("  pip install numpy matplotlib tkinter")
        input("按回车键退出...")
        sys.exit(1)

    except Exception as e:
        print(f"运行错误: {e}")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()