#!/usr/bin/env python
"""
动态表面分析系统 - GUI启动脚本
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui_main import DynamicSurfaceGUI

    print("=" * 50)
    print("动态表面分析系统")
    print("=" * 50)
    print("正在启动图形界面...")

    # 创建并运行GUI
    app = DynamicSurfaceGUI()
    app.run()

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖模块已正确安装")
    sys.exit(1)

except Exception as e:
    print(f"运行错误: {e}")
    sys.exit(1)