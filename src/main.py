# -*- coding: utf-8 -*-
"""
融合系统主入口 - 整合仪表盘和传感器数据采集系统
提供菜单或按钮来启动各个子模块
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStyleFactory
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 添加src目录到路径
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class LauncherWindow(QMainWindow):
    """融合系统启动器窗口"""

    def __init__(self):
        super().__init__()
        self.dashboard_window = None
        self.sensor_window = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("微小型无人机智能风场测试评估系统 - 融合平台")
        self.setMinimumSize(800, 600)

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

        subtitle = QLabel("融合平台 v1.0")
        subtitle.setFont(QFont("Microsoft YaHei", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(50)

        # 模块选择区域
        modules_label = QLabel("请选择要启动的模块：")
        modules_label.setFont(QFont("Microsoft YaHei", 14))
        layout.addWidget(modules_label)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        # 全局仪表盘按钮
        self.dashboard_btn = QPushButton("全局监控仪表盘")
        self.dashboard_btn.setFixedSize(200, 100)
        self.dashboard_btn.setFont(QFont("Microsoft YaHei", 12))
        self.dashboard_btn.setStyleSheet("""
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
        self.dashboard_btn.clicked.connect(self.launch_dashboard)
        btn_layout.addWidget(self.dashboard_btn)

        # 融合系统按钮（仪表盘+传感器数据）
        self.fusion_btn = QPushButton("融合系统\n(仪表盘+传感器)")
        self.fusion_btn.setFixedSize(200, 100)
        self.fusion_btn.setFont(QFont("Microsoft YaHei", 12))
        self.fusion_btn.setStyleSheet("""
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
        self.fusion_btn.clicked.connect(self.launch_fusion)
        btn_layout.addWidget(self.fusion_btn)

        # 传感器数据采集按钮
        self.sensor_btn = QPushButton("传感器数据采集")
        self.sensor_btn.setFixedSize(200, 100)
        self.sensor_btn.setFont(QFont("Microsoft YaHei", 12))
        self.sensor_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.sensor_btn.clicked.connect(self.launch_sensor)
        btn_layout.addWidget(self.sensor_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addSpacing(30)

        # 功能说明区域
        info_label = QLabel("功能说明：")
        info_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(info_label)

        info_text = QLabel(
            "• 全局监控仪表盘：包含系统监控、通讯、环境、日志、动捕、风机等所有功能模块\n"
            "• 融合系统：集成全局仪表盘 + 传感器数据采集和查看功能\n"
            "• 传感器数据采集：独立的传感器数据采集、查看和MongoDB同步功能"
        )
        info_text.setFont(QFont("Microsoft YaHei", 10))
        info_text.setStyleSheet("color: #555; padding-left: 20px;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        layout.addStretch()

        # 底部信息
        footer = QLabel("© 2026 微小型无人机智能风场测试评估系统 | 融合平台")
        footer.setFont(QFont("Microsoft YaHei", 9))
        footer.setStyleSheet("color: #999;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        central_widget.setLayout(layout)

    def launch_dashboard(self):
        """启动全局监控仪表盘"""
        try:
            from dashboard.ui_main_window import GlobalDashboardWindow

            self.dashboard_window = GlobalDashboardWindow()
            self.dashboard_window.show()

            self.hide()  # 隐藏启动器

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动仪表盘失败：\n{str(e)}")

    def launch_fusion(self):
        """启动融合系统（仪表盘 + 传感器数据）"""
        try:
            from dashboard.ui_main_window import GlobalDashboardWindow

            # 创建仪表盘窗口
            self.dashboard_window = GlobalDashboardWindow()
            self.dashboard_window.show()

            # 自动显示传感器数据dock
            if hasattr(self.dashboard_window, 'docks') and '传感器数据' in self.dashboard_window.docks:
                self.dashboard_window.docks['传感器数据'].show()
                # 将传感器数据dock移动到合适的位置
                self.dashboard_window.docks['传感器数据'].move(400, 350)
                self.dashboard_window.docks['传感器数据'].raise_()

            self.hide()  # 隐藏启动器

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动融合系统失败：\n{str(e)}")

    def launch_sensor(self):
        """启动传感器数据采集系统"""
        try:
            # 检查是否要启动独立的传感器采集窗口还是使用仪表盘中的传感器数据模块
            reply = QMessageBox.question(
                self, "选择启动方式",
                "请选择传感器数据采集系统的启动方式：\n\n"
                "• Yes: 在仪表盘中启动（推荐）\n"
                "• No: 启动独立的传感器采集窗口",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 在仪表盘中启动
                self.launch_fusion()
            else:
                # 启动独立的传感器采集窗口（这里我们仍然使用仪表盘，但只显示传感器数据dock）
                from dashboard.ui_main_window import GlobalDashboardWindow

                self.sensor_window = GlobalDashboardWindow()
                self.sensor_window.show()

                # 隐藏所有dock，只显示传感器数据
                if hasattr(self.sensor_window, 'docks'):
                    for name, dock in self.sensor_window.docks.items():
                        if name != '传感器数据':
                            dock.hide()
                        else:
                            dock.show()
                            dock.move(100, 100)
                            dock.resize(800, 600)

                self.hide()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动传感器数据采集失败：\n{str(e)}")


def main():
    """主函数"""
    # 设置应用程序样式
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setApplicationName("微小型无人机智能风场测试评估系统")

    # 设置中文字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建并显示启动器窗口
    launcher = LauncherWindow()
    launcher.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
