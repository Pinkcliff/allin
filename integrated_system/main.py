# -*- coding: utf-8 -*-
"""
整合系统主入口 - 同时启动桌面客户端和Web服务
"""
import sys
import os
import subprocess
import threading
import time

# 修复Qt平台插件路径问题
if sys.platform == 'win32':
    # 尝试多个可能的插件路径
    possible_paths = [
        # my_env 环境
        r'D:\ProgramData\Anaconda3\envs\my_env\Lib\site-packages\PySide6\plugins\platforms',
        # 基于Python执行路径
        os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms'),
        # 基于site-packages
        os.path.join(sys.prefix, 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms'),
    ]

    for plugin_path in possible_paths:
        if os.path.exists(plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
            print(f"Qt插件路径: {plugin_path}")
            break

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStyleFactory, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QIcon, QAction

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class WebServerThread(QThread):
    """Web服务器线程"""
    started = Signal()
    stopped = Signal()
    error = Signal(str)

    def __init__(self, host='0.0.0.0', port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self.process = None
        self.running = False

    def run(self):
        """启动Web服务器"""
        try:
            backend_dir = os.path.join(ROOT_DIR, 'web', 'backend')
            main_file = os.path.join(backend_dir, 'main.py')

            print(f"[INFO] 正在启动Web后端服务器...")
            print(f"[INFO] 后端目录: {backend_dir}")
            print(f"[INFO] 主文件: {main_file}")
            print(f"[INFO] Python路径: {sys.executable}")

            # 检查文件是否存在
            if not os.path.exists(main_file):
                raise FileNotFoundError(f"后端主文件不存在: {main_file}")

            self.running = True
            self.started.emit()

            # 启动FastAPI服务器 - 不隐藏输出以便调试
            self.process = subprocess.Popen(
                [sys.executable, main_file],
                cwd=backend_dir,
                text=True
            )

            print(f"[INFO] Web后端服务器已启动 (PID: {self.process.pid})")

            # 等待进程结束
            self.process.wait()
            print(f"[INFO] Web后端服务器已停止")

        except Exception as e:
            print(f"[ERROR] Web服务器启动失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error.emit(f"Web服务器启动失败: {str(e)}")
        finally:
            self.running = False
            self.stopped.emit()

    def stop(self):
        """停止Web服务器"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()


class IntegratedMainWindow(QMainWindow):
    """整合系统主窗口"""

    def __init__(self):
        super().__init__()
        self.dashboard_window = None
        self.web_thread = None
        self.web_server_running = False
        self.frontend_started = False  # 防止前端重复启动
        self.init_ui()
        self.start_web_server()

        # 延迟1秒后自动启动桌面客户端
        QTimer.singleShot(1000, self.auto_launch)

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("微小型无人机智能风场测试评估系统 - 整合平台")
        self.setMinimumSize(900, 700)
        self.resize(900, 700)

        # 窗口居中显示
        self.center_window()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        # 标题
        title = QLabel("微小型无人机智能风场测试评估系统")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("整合平台 v2.0 - 桌面客户端 + Web数字孪生")
        subtitle.setFont(QFont("Microsoft YaHei", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        # Web服务器状态
        self.web_status_label = QLabel("Web服务状态: 启动中...")
        self.web_status_label.setFont(QFont("Microsoft YaHei", 12))
        self.web_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.web_status_label.setStyleSheet("color: #FF9800; padding: 10px; background: #FFF3E0; border-radius: 5px;")
        layout.addWidget(self.web_status_label)

        # Web地址显示
        self.web_url_label = QLabel("")
        self.web_url_label.setFont(QFont("Microsoft YaHei", 11))
        self.web_url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.web_url_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(self.web_url_label)

        layout.addSpacing(30)

        # 模块选择区域
        modules_label = QLabel("请选择要启动的模块：")
        modules_label.setFont(QFont("Microsoft YaHei", 14))
        layout.addWidget(modules_label)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        # 桌面客户端按钮
        self.desktop_btn = QPushButton("桌面客户端\n(PySide6)")
        self.desktop_btn.setFixedSize(200, 120)
        self.desktop_btn.setFont(QFont("Microsoft YaHei", 12))
        self.desktop_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.desktop_btn.clicked.connect(self.launch_desktop)
        btn_layout.addWidget(self.desktop_btn)

        # Web浏览器按钮
        self.web_btn = QPushButton("Web数字孪生\n(浏览器)")
        self.web_btn.setFixedSize(200, 120)
        self.web_btn.setFont(QFont("Microsoft YaHei", 12))
        self.web_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.web_btn.clicked.connect(self.open_web_browser)
        btn_layout.addWidget(self.web_btn)

        # 同时启动按钮
        self.both_btn = QPushButton("同时启动\n(桌面+Web)")
        self.both_btn.setFixedSize(200, 120)
        self.both_btn.setFont(QFont("Microsoft YaHei", 12))
        self.both_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        self.both_btn.clicked.connect(self.launch_both)
        btn_layout.addWidget(self.both_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addSpacing(30)

        # 功能说明区域
        info_label = QLabel("系统说明：")
        info_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(info_label)

        info_text = QLabel(
            "• 桌面客户端：PySide6原生界面，包含仪表盘、传感器、PLC等所有功能\n"
            "• Web数字孪生：基于浏览器的前端界面，支持多终端访问\n"
            "• 数据同步：桌面客户端与Web端实时同步，操作即时反映\n"
            "• Web地址: http://localhost:5174/ (自动启动前端开发服务器)"
        )
        info_text.setFont(QFont("Microsoft YaHei", 10))
        info_text.setStyleSheet("color: #555; padding-left: 20px;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        layout.addStretch()

        # 底部信息
        footer = QLabel("© 2026 微小型无人机智能风场测试评估系统 | 整合平台 v2.0")
        footer.setFont(QFont("Microsoft YaHei", 9))
        footer.setStyleSheet("color: #999;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        central_widget.setLayout(layout)

    def center_window(self):
        """窗口居中显示"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def auto_launch(self):
        """自动启动桌面客户端"""
        print(f"[INFO] 延迟1秒后启动桌面客户端...")
        self.launch_desktop()

    def start_web_server(self):
        """启动Web后端服务器"""
        self.web_thread = WebServerThread(host='0.0.0.0', port=8000)
        self.web_thread.started.connect(self.on_web_started)
        self.web_thread.error.connect(self.on_web_error)
        self.web_thread.start()

    def on_web_started(self):
        """Web服务器启动成功"""
        self.web_server_running = True
        self.web_status_label.setText("Web服务状态: ✓ 运行中")
        self.web_status_label.setStyleSheet("color: #4CAF50; padding: 10px; background: #E8F5E9; border-radius: 5px;")
        self.web_url_label.setText("后端API: http://localhost:8000 | 前端: http://localhost:5174")

        # 自动启动前端开发服务器
        self.start_frontend_server()

    def on_web_error(self, error_msg):
        """Web服务器启动失败"""
        self.web_status_label.setText(f"Web服务状态: ✗ {error_msg}")
        self.web_status_label.setStyleSheet("color: #F44336; padding: 10px; background: #FFEBEE; border-radius: 5px;")

    def start_frontend_server(self):
        """启动前端开发服务器"""
        # 防止重复启动
        if self.frontend_started:
            print(f"[INFO] 前端已经启动，跳过重复启动")
            return

        self.frontend_started = True

        try:
            frontend_dir = os.path.join(ROOT_DIR, 'web', 'frontend')
            print(f"[INFO] 正在启动前端开发服务器...")
            print(f"[INFO] 前端目录: {frontend_dir}")

            # 检查npm是否可用
            try:
                result = subprocess.run(['npm', '--version'], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    print(f"[INFO] npm 已就绪 (version: {result.stdout.strip()})")
                else:
                    print(f"[ERROR] npm 返回错误: {result.stderr}")
                    return
            except Exception as e:
                print(f"[ERROR] npm 检查失败: {e}")
                return

            # 检查package.json是否存在
            package_json = os.path.join(frontend_dir, 'package.json')
            if not os.path.exists(package_json):
                print(f"[ERROR] package.json 不存在: {package_json}")
                print(f"[INFO] 请先在前端目录运行 'npm install' 安装依赖")
                return

            # 检查node_modules是否存在
            node_modules = os.path.join(frontend_dir, 'node_modules')
            if not os.path.exists(node_modules):
                print(f"[WARN] node_modules 不存在，可能需要运行 'npm install'")

            # 在Windows上使用shell=True来确保npm能被找到
            if sys.platform == 'win32':
                print(f"[INFO] 使用 Windows shell 启动前端...")
                process = subprocess.Popen(
                    'npm run dev',
                    cwd=frontend_dir,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            else:
                process = subprocess.Popen(
                    ['npm', 'run', 'dev'],
                    cwd=frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            print(f"[INFO] 前端开发服务器已启动 (PID: {process.pid})")
            print(f"[INFO] 前端地址: http://localhost:5174")

        except Exception as e:
            print(f"[ERROR] 前端启动失败: {e}")
            import traceback
            traceback.print_exc()

    def launch_desktop(self):
        """启动桌面客户端"""
        try:
            print(f"[INFO] 正在启动桌面客户端...")
            print(f"[INFO] ROOT_DIR: {ROOT_DIR}")
            print(f"[INFO] SRC_DIR: {SRC_DIR}")
            print(f"[INFO] sys.path: {sys.path[:3]}...")

            # 检查 dashboard 目录是否存在
            dashboard_dir = os.path.join(SRC_DIR, 'dashboard')
            if not os.path.exists(dashboard_dir):
                print(f"[ERROR] dashboard 目录不存在: {dashboard_dir}")
                QMessageBox.critical(self, "错误", f"dashboard 目录不存在:\n{dashboard_dir}")
                return

            print(f"[INFO] 正在导入 dashboard.ui_main_window...")
            from dashboard.ui_main_window import GlobalDashboardWindow

            print(f"[INFO] 正在创建主窗口...")
            self.dashboard_window = GlobalDashboardWindow()
            self.dashboard_window.show()

            print(f"[INFO] 桌面客户端已启动")
            self.hide()

        except ImportError as e:
            print(f"[ERROR] 导入错误: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "导入错误", f"无法导入桌面客户端模块：\n{str(e)}\n\n请检查是否安装了所有依赖包。")
        except Exception as e:
            print(f"[ERROR] 启动桌面客户端失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"启动桌面客户端失败：\n{str(e)}")

    def open_web_browser(self):
        """在浏览器中打开Web界面"""
        import webbrowser
        webbrowser.open('http://localhost:5174')

    def launch_both(self):
        """同时启动桌面客户端和Web界面"""
        self.launch_desktop()
        # 延迟一下再打开浏览器，让桌面客户端先加载
        QTimer.singleShot(1000, self.open_web_browser)

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出整合系统吗？\n这将同时关闭桌面客户端和Web服务。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 停止Web服务器
            if self.web_thread:
                self.web_thread.stop()

            # 关闭桌面窗口
            if self.dashboard_window:
                self.dashboard_window.close()

            event.accept()
        else:
            event.ignore()


from PySide6.QtCore import QTimer


def main():
    """主函数"""
    # 设置应用程序样式
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setApplicationName("微小型无人机智能风场测试评估系统 - 整合平台")

    # 设置中文字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建并显示主窗口
    main_window = IntegratedMainWindow()
    main_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
