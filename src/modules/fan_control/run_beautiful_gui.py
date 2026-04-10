#!/usr/bin/env python
"""
运行美观版动态表面分析系统
现代化UI设计
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui_beautiful import BeautifulGUI

    print("=" * 60)
    print("动态表面分析系统 - 专业版")
    print("=" * 60)
    print("启动现代化美观界面...")
    print("特色功能:")
    print("   - 深色主题设计")
    print("   - 现代化图标")
    print("   - 平滑动画效果")
    print("   - 多种配色方案")
    print("-" * 60)

    # 创建并运行GUI
    app = BeautifulGUI()
    app.run()

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖模块已正确安装")
    input("按任意键退出...")
    sys.exit(1)

except Exception as e:
    print(f"运行错误: {e}")
    input("按任意键退出...")
    sys.exit(1)