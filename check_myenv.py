# -*- coding: utf-8 -*-
"""检查my_env环境"""
import sys
import os

print("=" * 60)
print("my_env 环境检查")
print("=" * 60)

print(f"\nPython路径: {sys.executable}")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")

# 检查是否在my_env环境中
if 'my_env' in sys.executable:
    print("\n[OK] 正在使用 my_env 环境")
else:
    print("\n[WARN] 可能不在 my_env 环境中")
    print(f"      预期路径: D:\\ProgramData\\Anaconda3\\envs\\my_env")

# 检查PySide6
print("\n检查PySide6...")
try:
    import PySide6
    print(f"[OK] PySide6 版本: {PySide6.__version__}")

    # 检查插件路径
    plugin_path = os.path.join(os.path.dirname(PySide6.__file__), 'plugins', 'platforms')
    print(f"[OK] 插件路径: {plugin_path}")

    if os.path.exists(plugin_path):
        plugins = os.listdir(plugin_path)
        print(f"[OK] 可用插件: {', '.join(plugins)}")

        # 设置环境变量
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
        print(f"[OK] 已设置 QT_QPA_PLATFORM_PLUGIN_PATH")
    else:
        print(f"[ERROR] 插件路径不存在!")

except ImportError as e:
    print(f"[ERROR] PySide6 导入失败: {e}")

# 检查项目路径
print("\n检查项目路径...")
src_dir = os.path.join(os.getcwd(), 'src')
if os.path.exists(src_dir):
    print(f"[OK] src目录存在")

    sys.path.insert(0, src_dir)

    try:
        from dashboard.ui_main_window import GlobalDashboardWindow
        print("[OK] dashboard模块导入成功")
    except Exception as e:
        print(f"[ERROR] dashboard模块导入失败: {e}")
else:
    print(f"[ERROR] src目录不存在: {src_dir}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
