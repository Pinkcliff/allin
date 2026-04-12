# -*- coding: utf-8 -*-
"""
独立3D视图窗口

使用matplotlib创建3D表面图来可视化风场函数
弹出式窗口，不占用主界面空间

创建时间: 2024-01-03
作者: Wind Field Editor Team
版本: 3.0.0 - 独立窗口版本
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QMainWindow,
    QPushButton, QHBoxLayout, QSpinBox, QDoubleSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QAction
import numpy as np

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib
    # 配置中文字体
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: matplotlib未安装，3D视图功能将不可用")


class Function3DWindow(QMainWindow):
    """
    独立的3D函数视图窗口

    显示风场函数的3D表面图
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D函数视图 - 风场动画")
        self.setGeometry(100, 100, 800, 700)

        self.current_function = 'gaussian'
        self.current_params = {'center': (20.0, 20.0), 'amplitude': 100.0}
        self.current_time = 0.0
        self.grid_data = np.zeros((40, 40))
        self.colorbar = None

        # 节流定时器 - 防止过于频繁的更新
        self._update_pending = False
        self._pending_data = None
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)  # 50ms节流，即最多20fps
        self._update_timer.timeout.connect(self._process_pending_update)

        # 播放状态标志 - 播放时禁止鼠标旋转3D视图
        self._playback_active = False

        # 窗口标志
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self._init_ui()
        self._init_3d_plot()

    def _init_ui(self):
        """初始化UI"""
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        if not MATPLOTLIB_AVAILABLE:
            label = QLabel("matplotlib未安装\n3D视图不可用")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: red; padding: 20px; font-size: 16px;")
            layout.addWidget(label)
            return

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("🎨 3D函数视图")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # matplotlib图形容器
        self.figure = None
        self.canvas = None
        self.ax = None

        # 控制面板
        control_layout = QHBoxLayout()

        # 视角控制
        elev_label = QLabel("仰角:")
        self.elev_spinbox = QSpinBox()
        self.elev_spinbox.setRange(0, 90)
        self.elev_spinbox.setValue(25)
        self.elev_spinbox.setSuffix("°")
        self.elev_spinbox.valueChanged.connect(self._update_view)

        azim_label = QLabel("方位角:")
        self.azim_spinbox = QSpinBox()
        self.azim_spinbox.setRange(0, 360)
        self.azim_spinbox.setValue(45)
        self.azim_spinbox.setSuffix("°")
        self.azim_spinbox.valueChanged.connect(self._update_view)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._update_plot)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-weight: bold;
                background: #4CAF50;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)

        control_layout.addWidget(elev_label)
        control_layout.addWidget(self.elev_spinbox)
        control_layout.addWidget(azim_label)
        control_layout.addWidget(self.azim_spinbox)
        control_layout.addStretch()
        control_layout.addWidget(self.refresh_btn)

        layout.addLayout(control_layout)

        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("padding: 5px; background: #e3f2fd; border-radius: 3px;")
        layout.addWidget(self.status_label)

        print("[3DWindow] 独立3D窗口初始化完成")

    def _init_3d_plot(self):
        """初始化3D图形"""
        try:
            # 创建matplotlib图形 - 固定大小
            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.figure.patch.set_facecolor('#f5f5f5')

            self.canvas = FigureCanvas(self.figure)
            self.canvas.setParent(self)
            # 设置canvas的大小策略，防止自动调整
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.canvas.setMinimumSize(600, 400)

            self.ax = self.figure.add_subplot(111, projection='3d')

            # 将canvas添加到布局（在控制面板之前）
            self.centralWidget().layout().insertWidget(1, self.canvas)

            # 安装事件过滤器 - 用于播放时拦截鼠标旋转事件
            self.canvas.installEventFilter(self)

            # 初始绘制一个测试图形
            self._draw_initial_plot()

            print("[3DWindow] 3D图形初始化成功")

        except Exception as e:
            print(f"[3DWindow] 3D图形初始化错误: {e}")
            import traceback
            traceback.print_exc()

    def set_playback_active(self, active: bool):
        """设置播放状态 - 播放时禁止3D视图鼠标旋转

        Args:
            active: True=正在播放，禁止旋转；False=已停止，允许旋转
        """
        self._playback_active = active
        if active:
            # 播放时：禁用鼠标交互，固定视角
            if self.canvas is not None:
                self.canvas.setMouseTracking(False)
                # 阻止matplotlib的3D交互鼠标事件
                self.canvas.mpl_disconnect_all = True
            if self.status_label:
                self.status_label.setText("播放中 - 3D视图已锁定（旋转已禁用）")
        else:
            # 停止时：恢复鼠标交互
            if self.canvas is not None:
                self.canvas.setMouseTracking(True)
                self.canvas.mpl_disconnect_all = False
            if self.status_label:
                self.status_label.setText("播放已停止 - 可自由旋转3D视图")

    def eventFilter(self, obj, event):
        """事件过滤器 - 播放时拦截3D视图的鼠标事件"""
        if self._playback_active and obj == self.canvas:
            # 播放时拦截鼠标按下和移动事件，阻止旋转
            from PySide6.QtCore import QEvent
            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseMove,
                                QEvent.MouseButtonDblClick):
                return True
        return super().eventFilter(obj, event)

    def _draw_initial_plot(self):
        """绘制初始图形 - 优化版本"""
        try:
            if self.ax is None:
                return

            # 创建一个测试数据 - 高斯函数
            x = np.arange(40)
            y = np.arange(40)
            X, Y = np.meshgrid(x, y)

            # 以(20,20)为中心的高斯函数
            center_x, center_y = 20, 20
            sigma = 5
            Z = 100 * np.exp(-((X - center_x)**2 + (Y - center_y)**2) / (2 * sigma**2))

            # 绘制3D表面 - 使用完整网格密度
            surf = self.ax.plot_surface(X, Y, Z,
                                       cmap='viridis',
                                       edgecolor='none',
                                       alpha=0.8,
                                       rcount=40,  # 完整分辨率
                                       ccount=40)  # 完整分辨率

            # 设置标签和标题
            self.ax.set_xlabel('X (列)', fontsize=10)
            self.ax.set_ylabel('Y (行)', fontsize=10)
            self.ax.set_zlabel('转速 (%)', fontsize=10)
            self.ax.set_title('3D函数视图\n点击"预览"激活函数',
                             fontsize=12, fontweight='bold')

            # 设置z轴范围
            self.ax.set_zlim(0, 100)

            # 设置视角
            elev = self.elev_spinbox.value()
            azim = self.azim_spinbox.value()
            self.ax.view_init(elev=elev, azim=azim)

            # 添加颜色条
            self.colorbar = self.figure.colorbar(surf, ax=self.ax, shrink=0.8, pad=0.1)
            self.colorbar.set_label('转速 (%)', fontsize=10)

            self.canvas.draw()
            self.status_label.setText("初始视图已加载 | 点击'预览'按钮激活函数")
            print("[3DWindow] 初始3D图形已绘制")

        except Exception as e:
            print(f"[3DWindow] 绘制初始图形错误: {e}")
            import traceback
            traceback.print_exc()

    def _update_plot(self):
        """更新3D图形 - 优化版本"""
        if not MATPLOTLIB_AVAILABLE or self.ax is None:
            return

        try:
            # 清除整个figure并重新创建axes
            self.figure.clear()

            # 重新创建3D axes
            self.ax = self.figure.add_subplot(111, projection='3d')

            # 创建坐标网格
            rows, cols = self.grid_data.shape
            x = np.arange(cols)
            y = np.arange(rows)
            X, Y = np.meshgrid(x, y)

            # 绘制3D表面 - 使用完整分辨率
            surf = self.ax.plot_surface(X, Y, self.grid_data,
                                       cmap='viridis',
                                       edgecolor='none',
                                       alpha=0.8,
                                       rcount=40,  # 完整分辨率
                                       ccount=40)  # 完整分辨率

            # 设置标签和标题
            self.ax.set_xlabel('X (列)', fontsize=10)
            self.ax.set_ylabel('Y (行)', fontsize=10)
            self.ax.set_zlabel('转速 (%)', fontsize=10)
            self.ax.set_title(f'{self.current_function}\nt={self.current_time:.2f}s',
                             fontsize=12, fontweight='bold')

            # 设置z轴范围
            self.ax.set_zlim(0, 100)

            # 设置视角
            elev = self.elev_spinbox.value()
            azim = self.azim_spinbox.value()
            self.ax.view_init(elev=elev, azim=azim)

            # 添加颜色条
            self.colorbar = self.figure.colorbar(surf, ax=self.ax, shrink=0.8, pad=0.1)
            self.colorbar.set_label('转速 (%)', fontsize=10)

            # 使用draw_idle进行异步绘制，避免阻塞
            self.canvas.draw_idle()

            max_val = self.grid_data.max()
            min_val = self.grid_data.min()
            mean_val = self.grid_data.mean()
            self.status_label.setText(f"函数: {self.current_function} | 时间: {self.current_time:.2f}s | 最大: {max_val:.1f}% | 平均: {mean_val:.1f}%")

            print(f"[3DWindow] 3D图形已更新: {self.current_function}, t={self.current_time:.2f}s")

        except Exception as e:
            print(f"[3DWindow] 绘图错误: {e}")
            import traceback
            traceback.print_exc()

    def _update_view(self):
        """更新视角"""
        if self.ax is not None:
            elev = self.elev_spinbox.value()
            azim = self.azim_spinbox.value()
            self.ax.view_init(elev=elev, azim=azim)
            self.canvas.draw_idle()  # 使用draw_idle避免过度绘制
            self.status_label.setText(f"视角已更新: 仰角{elev}°, 方位角{azim}°")

    @Slot(str, dict, float)
    def update_function_data(self, function_type: str, params: dict, time_value: float):
        """更新函数数据并重绘"""
        self.current_function = function_type
        self.current_params = params
        self.current_time = time_value

        # 如果grid_data被更新了，使用它；否则重新计算
        if hasattr(self, 'last_grid_data'):
            self.grid_data = self.last_grid_data

        # 使用节流更新
        self._schedule_update()

    def _process_pending_update(self):
        """处理待定的更新"""
        if self._pending_data is not None:
            self.grid_data = self._pending_data
            self._pending_data = None
        self._update_pending = False
        self._update_plot()

    def _schedule_update(self):
        """调度更新（带节流）"""
        self._update_pending = True
        if not self._update_timer.isActive():
            self._update_timer.start()

    def set_grid_data(self, grid_data: np.ndarray):
        """直接设置网格数据 - 使用节流机制"""
        self.last_grid_data = grid_data.copy()
        self._pending_data = grid_data
        self._schedule_update()

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 确保在显示时重新绘制
        if self.canvas is not None:
            self.canvas.draw()
            print("[3DWindow] 3D窗口已显示")


# 保留原有的嵌入式组件，但添加打开独立窗口的方法
class Function3DView(QWidget):
    """
    3D函数视图组件（嵌入式版本）

    现在用于显示一个按钮，点击打开独立的3D窗口
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 提示标签
        label = QLabel("💡 点击下方按钮打开3D视图窗口")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #2196F3; font-size: 14px; padding: 10px;")
        layout.addWidget(label)

        # 打开3D窗口按钮
        self.open_3d_btn = QPushButton("🎨 打开3D函数视图")
        self.open_3d_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #4CAF50;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66BB6A, stop:1 #43A047);
                border: 2px solid #66BB6A;
            }
            QPushButton:pressed {
                background: #43A047;
            }
        """)

        layout.addWidget(self.open_3d_btn)

        # 创建3D窗口（但不显示）
        self.d3d_window = Function3DWindow(self.parent())

        # 连接按钮
        self.open_3d_btn.clicked.connect(self.open_3d_window)

        print("[3DView] 嵌入式3D视图初始化完成")

    def open_3d_window(self):
        """打开独立3D窗口"""
        self.d3d_window.show()
        self.d3d_window.raise_()
        self.d3d_window.activateWindow()
        print("[3DView] 独立3D窗口已打开")

    def set_grid_data(self, grid_data: np.ndarray):
        """设置网格数据并更新3D窗口"""
        self.d3d_window.set_grid_data(grid_data)
        self.d3d_window.current_function = self.d3d_window.current_function
        self.d3d_window.current_time = self.d3d_window.current_time

    def update_function_data(self, function_type: str, params: dict, time_value: float):
        """更新函数数据并重绘"""
        self.d3d_window.update_function_data(function_type, params, time_value)
        self.d3d_window.current_function = function_type
        self.d3d_window.current_time = time_value


# 导出
__all__ = ['Function3DView', 'Function3DWindow']
