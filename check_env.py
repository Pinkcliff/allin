# -*- coding: utf-8 -*-
"""环境检查脚本"""
import sys
import os

print("=" * 60)
print("环境检查工具")
print("=" * 60)

print(f"\nPython版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"当前目录: {os.getcwd()}")

# 检查PySide6
print("\n检查PySide6...")
try:
    import PySide6
    print(f"  [OK] PySide6 版本: {PySide6.__version__}")

    # 检查插件
    plugin_path = os.path.join(os.path.dirname(PySide6.__file__), 'plugins', 'platforms')
    if os.path.exists(plugin_path):
        print(f"  [OK] 插件路径: {plugin_path}")
        plugins = os.listdir(plugin_path)
        print(f"  [OK] 可用插件: {', '.join(plugins)}")
    else:
        print(f"  [WARN] 插件路径不存在: {plugin_path}")
except ImportError as e:
    print(f"  [ERROR] PySide6 导入失败: {e}")

# 检查项目路径
print("\n检查项目路径...")
src_dir = os.path.join(os.getcwd(), 'src')
if os.path.exists(src_dir):
    print(f"  [OK] src目录存在: {src_dir}")

    dashboard_file = os.path.join(src_dir, 'dashboard', 'ui_main_window.py')
    if os.path.exists(dashboard_file):
        print(f"  [OK] dashboard主文件存在")
    else:
        print(f"  [WARN] dashboard主文件不存在: {dashboard_file}")
else:
    print(f"  [WARN] src目录不存在: {src_dir}")

# 测试导入
print("\n测试模块导入...")
sys.path.insert(0, 'src')
try:
    from dashboard.ui_main_window import GlobalDashboardWindow
    print("  [OK] dashboard模块导入成功")
except Exception as e:
    print(f"  [ERROR] dashboard模块导入失败: {e}")

# 检查Web后端
print("\n检查Web后端...")
backend_dir = os.path.join(os.getcwd(), 'web', 'backend')
if os.path.exists(backend_dir):
    print(f"  [OK] 后端目录存在")

    requirements = os.path.join(backend_dir, 'requirements.txt')
    if os.path.exists(requirements):
        print(f"  [OK] requirements.txt存在")
    else:
        print(f"  [WARN] requirements.txt不存在")

    main_py = os.path.join(backend_dir, 'main.py')
    if os.path.exists(main_py):
        print(f"  [OK] main.py存在")
    else:
        print(f"  [WARN] main.py不存在")
else:
    print(f"  [WARN] 后端目录不存在: {backend_dir}")

# 检查Web前端
print("\n检查Web前端...")
frontend_dir = os.path.join(os.getcwd(), 'web', 'frontend')
if os.path.exists(frontend_dir):
    print(f"  [OK] 前端目录存在")

    package_json = os.path.join(frontend_dir, 'package.json')
    if os.path.exists(package_json):
        print(f"  [OK] package.json存在")
    else:
        print(f"  [WARN] package.json不存在")
else:
    print(f"  [WARN] 前端目录不存在: {frontend_dir}")

print("\n" + "=" * 60)
print("环境检查完成")
print("=" * 60)

input("\n按回车键退出...")
