#!/usr/bin/env python
"""
运行简化版GUI
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui_simple import SimpleGUI

if __name__ == "__main__":
    print("启动简化版动态表面分析系统...")
    app = SimpleGUI()
    app.run()