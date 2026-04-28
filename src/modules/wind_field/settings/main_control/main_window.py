# wind_wall_simulator/main_window.py

import sys
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStatusBar, 
    QToolBar, QLabel, QFileDialog, QTextEdit, QMenu, QSplitter, QDialog,
    QGroupBox, QFormLayout, QDockWidget, QStackedWidget
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtGui import QUndoStack
from PySide6.QtCore import QObject, Signal, QSize
from .commands import EditCommand
import numpy as np

from . import config
from .canvas_widget import CanvasWidget
from .timeline_widget import TimelineWidget
from .floating_windows import (
    SelectionInfoWindow, BrushToolWindow, FanSettingsWindow,
    TimeSettingsWindow, TemplateLibraryWindow, InfoWindow,
    CircleToolWindow, LineToolWindow, FunctionToolWindow
)
from .enhanced_function_tool import EnhancedFunctionToolWindow
from .function_3d_view import Function3DView
from .data_analyzer_window import FeedbackPanel
from .udp_fan_sender import FanUDPSender, AsyncFanUDPSender, FanUDPListener


class _UDPListenerBridge(QObject):
    """线程安全的信号桥接：监听线程 -> UI线程"""
    data_received = Signal(bytes)


class MainWindow(QMainWindow):
    """重新设计的主窗口，包含右侧Dock面板和工具模式切换"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setGeometry(100, 100, 1200, 900)
        # 【新增】初始化撤销栈和状态暂存
        self.undo_stack = QUndoStack(self)
        self.data_before_edit = None

        # 调试模式标志
        self.debug_mode = True

        # 【新增】Web同步客户端（延迟初始化，在UI创建后）
        self.web_sync_client = None

        # 时间设置
        self.max_time = 10.0
        self.time_resolution = 0.1
        self.max_rpm = 15000

        # 【新增】UDP发送器初始化
        self.udp_sender = None
        self.udp_listener = None
        self._listener_bridge = _UDPListenerBridge()
        self.udp_enabled = True  # 【修改】默认启用UDP
        self.udp_async_mode = True  # 默认使用异步模式
        self.udp_send_on_change = True  # 【修改】数据变化时自动发送默认开启
        self.udp_send_timer = None
        self.udp_send_on_play = True  # 【新增】播放时自动发送UDP数据

        # 【新增】播放状态标志
        self.is_playing = False  # 当前播放状态
        
        # 运行时间计时器
        self.start_time = datetime.now()
        self.base_runtime = timedelta(hours=1234, minutes=56)
        self.runtime_timer = QTimer(self)
        self.runtime_timer.setInterval(1000) # 每秒更新一次
        self.runtime_timer.timeout.connect(self._update_runtime_display)
        # self.runtime_timer.start()

        # 函数动画相关参数（使用时间轴驱动）
        self.current_function_params = None  # 存储当前函数参数 (function_type, params)

        # 初始化工具面板
        self._init_tool_widgets()
        
        # 创建UI元素
        self._create_docks_and_central_widget()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        # 【新增】初始化UDP发送器
        self._init_udp_sender()

        # 【新增】初始化UDP返回数据监听器
        self._init_udp_listener()

        # 【新增】初始化Web同步客户端（必须在UI创建后调用）
        self._init_web_sync()

        self._connect_signals()

        # 【修改】由于默认启用UDP，手动触发一次初始化和日志
        if self.udp_enabled:
            self._add_info_message("UDP发送已启用（默认）")
            self._add_info_message("目标: 10个IP (192.168.1.100-109:6005), 每IP管10组风扇")

    def _init_tool_widgets(self):
        """初始化所有工具面板的QWidget"""
        # 这些现在是普通的QWidget，将被放入QStackedWidget
        self.selection_widget = SelectionInfoWindow(self)
        self.brush_widget = BrushToolWindow(self)
        self.circle_widget = CircleToolWindow(self)
        self.line_widget = LineToolWindow(self)

        # 【新增】使用增强版函数工具窗口
        self.function_widget = EnhancedFunctionToolWindow(self)

        # 这些仍然是独立的对话框
        self.fan_settings_window = FanSettingsWindow(self)
        self.time_settings_window = TimeSettingsWindow(self)
        self.template_window = TemplateLibraryWindow(self)

        # 3D函数视图
        self.function_3d_view = Function3DView(self)

        # 电驱板数据分析工具
        self.data_analyzer_window = None  # 已改为Dock内嵌面板，在_create_docks中初始化

        # 设置初始值
        self.fan_settings_window.set_max_rpm(self.max_rpm)
        self.time_settings_window.set_max_time(self.max_time)
        self.time_settings_window.set_time_resolution(self.time_resolution)

# main_window.py -> MainWindow

# main_window.py -> MainWindow

# main_window.py -> MainWindow

    def _create_docks_and_central_widget(self):
        """创建Dock面板和中央组件 (布局修复版)"""
        # --- 中央组件：使用QVBoxLayout并为时间轴设置固定高度 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(5, 5, 5, 5)
        central_layout.setSpacing(5)

        self.canvas_widget = CanvasWidget(self, self)
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.set_max_time(self.max_time)
        self.timeline_widget.set_time_resolution(self.time_resolution)

        # 【核心修复】将画布和时间条添加到布局中
        central_layout.addWidget(self.canvas_widget)
        central_layout.addWidget(self.timeline_widget)

        # 【核心修复】强制时间轴占据固定高度，让画布填充剩余空间
        central_layout.setStretch(0, 1) # 画布是可伸缩的
        central_layout.setStretch(1, 0) # 时间轴不可伸缩
        self.timeline_widget.setMaximumHeight(80) # 设置一个最大高度

        # --- 右侧Dock面板 ---
        right_dock = QDockWidget("工具与信息", self)
        right_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        right_dock.setMinimumWidth(400)  # 设置Dock最小宽度

        dock_container = QWidget()
        dock_container.setMinimumWidth(400)  # 设置容器最小宽度
        dock_layout = QVBoxLayout(dock_container)
        dock_layout.setContentsMargins(5, 5, 5, 5)
        dock_layout.setSpacing(5)
        
        # 1. 工具模式面板
        self.tool_mode_group = QGroupBox("点选模式")
        self.tool_stack = QStackedWidget()
        self.tool_stack.addWidget(self.selection_widget)
        self.tool_stack.addWidget(self.brush_widget)
        self.tool_stack.addWidget(self.circle_widget)
        self.tool_stack.addWidget(self.line_widget)
        self.tool_stack.addWidget(self.function_widget)
        
        tool_mode_layout = QVBoxLayout()
        tool_mode_layout.addWidget(self.tool_stack)
        self.tool_mode_group.setLayout(tool_mode_layout)

        # 2. 反馈信息面板（电驱板返回数据解析）
        self.feedback_panel = FeedbackPanel(self)

        # 3. 状态信息面板
        status_group = QGroupBox("状态信息")
        status_layout = QFormLayout()
        status_layout.setLabelAlignment(Qt.AlignRight)
        self.fan_id_label = QLabel("--")
        self.fan_position_label = QLabel("--")
        self.fan_speed1_label = QLabel("--")
        self.fan_speed2_label = QLabel("--")
        self.fan_pwm_label = QLabel("--")
        self.fan_power_label = QLabel("--")
        self.fan_runtime_label = QLabel("--")
        # 为值标签设置最小宽度，防止文字被截断
        min_w = 160
        for lbl in [self.fan_id_label, self.fan_position_label, self.fan_speed1_label,
                     self.fan_speed2_label, self.fan_pwm_label, self.fan_power_label,
                     self.fan_runtime_label]:
            lbl.setMinimumWidth(min_w)
        status_layout.addRow("风扇ID:", self.fan_id_label)
        status_layout.addRow("位置(行,列):", self.fan_position_label)
        status_layout.addRow("一级转速:", self.fan_speed1_label)
        status_layout.addRow("二级转速:", self.fan_speed2_label)
        status_layout.addRow("占空比:", self.fan_pwm_label)
        status_layout.addRow("电流电压功率:", self.fan_power_label)
        status_layout.addRow("运行时间:", self.fan_runtime_label)
        status_group.setLayout(status_layout)

        # 4. 系统信息面板（限制高度）
        info_group = QGroupBox("系统信息")
        info_group.setMaximumHeight(200)  # 限制最大高度
        info_layout = QVBoxLayout()
        self.info_output = QTextEdit()
        self.info_output.setReadOnly(True)
        self.info_output.append("系统就绪...")
        info_layout.addWidget(self.info_output)
        info_group.setLayout(info_layout)

        # 将四个部分添加到Dock容器中
        dock_layout.addWidget(self.tool_mode_group, 12)
        dock_layout.addWidget(self.feedback_panel, 10)
        dock_layout.addWidget(status_group, 8)
        dock_layout.addWidget(info_group, 5)

        # 设置stretch因子
        dock_layout.setStretch(0, 12)
        dock_layout.setStretch(1, 10)
        dock_layout.setStretch(2, 8)
        dock_layout.setStretch(3, 5)

        right_dock.setWidget(dock_container)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)




# main_window.py -> MainWindow
    def _create_actions(self):
        """创建所有菜单栏的动作"""
        # 文件菜单动作
        self.menu_open_action = QAction("打开", self)
        self.menu_save_action = QAction("保存", self)
        self.menu_save_as_action = QAction("另存为", self)
        self.menu_exit_action = QAction("退出", self)
        
        # 工具菜单动作
        self.menu_selection_action = QAction("选择", self)
        self.menu_brush_tool_action = QAction("笔刷工具", self)
        self.menu_circle_tool_action = QAction("圆形工具", self)
        self.menu_line_tool_action = QAction("直线工具", self)
        self.menu_function_generator_action = QAction("函数生成器", self)
        self.menu_run_sim_action = QAction("进入仿真", self)
        
        # 设置菜单动作
        self.menu_fan_settings_action = QAction("风机设置", self)
        self.menu_time_settings_action = QAction("时间设置", self)
        self.menu_template_library_action = QAction("模版库", self)
        self.menu_debug_mode_action = QAction("调试模式", self)
        self.menu_debug_mode_action.setCheckable(True)
        self.menu_debug_mode_action.setChecked(self.debug_mode)

        # 【新增】UDP控制菜单动作
        self.menu_udp_enable_action = QAction("启用UDP发送", self)
        self.menu_udp_enable_action.setCheckable(True)
        self.menu_udp_enable_action.setChecked(True)  # 【修改】默认勾选
        self.menu_udp_auto_send_action = QAction("数据变化时自动发送", self)
        self.menu_udp_auto_send_action.setCheckable(True)
        self.menu_udp_auto_send_action.setChecked(True)  # 【修改】默认勾选
        self.menu_udp_send_all_action = QAction("立即发送所有数据", self)
        self.menu_udp_send_selected_action = QAction("发送选中数据", self)
        self.menu_udp_stats_action = QAction("UDP统计信息", self)
        self.menu_udp_auto_parse_action = QAction("启用自动解析", self)
        self.menu_udp_auto_parse_action.setCheckable(True)
        self.menu_udp_auto_parse_action.setChecked(True)

        # 【新增】播放时自动发送UDP数据
        self.udp_send_on_play = True  # 默认开启播放时发送

# main_window.py -> MainWindow

    def _create_menus(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        file_menu.addAction(self.menu_open_action)
        file_menu.addAction(self.menu_save_action)
        file_menu.addAction(self.menu_save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.menu_exit_action)
        
        # 工具菜单
        tools_menu = menu_bar.addMenu("工具")
        tools_menu.addAction(self.menu_selection_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.menu_brush_tool_action)
        tools_menu.addAction(self.menu_circle_tool_action)
        tools_menu.addAction(self.menu_line_tool_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.menu_function_generator_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.menu_run_sim_action)
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        settings_menu.addAction(self.menu_fan_settings_action)
        settings_menu.addAction(self.menu_time_settings_action)
        settings_menu.addAction(self.menu_template_library_action)
        settings_menu.addSeparator()
        settings_menu.addAction(self.menu_debug_mode_action)

        # 【新增】UDP控制菜单
        udp_menu = menu_bar.addMenu("UDP控制")
        udp_menu.addAction(self.menu_udp_enable_action)
        udp_menu.addAction(self.menu_udp_auto_send_action)
        udp_menu.addSeparator()
        udp_menu.addAction(self.menu_udp_send_all_action)
        udp_menu.addAction(self.menu_udp_send_selected_action)
        udp_menu.addSeparator()
        udp_menu.addAction(self.menu_udp_stats_action)
        udp_menu.addAction(self.menu_udp_auto_parse_action)


# main_window.py -> MainWindow

# main_window.py -> MainWindow

# main_window.py -> MainWindow

# main_window.py -> MainWindow

# main_window.py -> MainWindow._create_toolbar
    def _create_toolbar(self):
        """创建带图标和文字的工具栏 (带撤销/重做)"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32, 32))
        
        current_dir = os.path.dirname(__file__)
        # 图标文件位于风场设置/icon目录下
        icon_path = os.path.join(current_dir, '..', 'icon')

        # 【新增】创建回退和前进按钮
        self.undo_action = self.undo_stack.createUndoAction(self, "回退")
        self.redo_action = self.undo_stack.createRedoAction(self, "前进")
        self.undo_action.setShortcut("Ctrl+Z")
        self.redo_action.setShortcut("Ctrl+Y")
        
        # 设置固定文本，不显示具体命令
        self.undo_action.setText("回退")
        self.redo_action.setText("前进")
        
        # 连接信号以保持固定文本
        self.undo_stack.indexChanged.connect(self._update_undo_redo_text)
        
        # 假设 icon 文件夹中有 undo.png 和 redo.png
        # self.undo_action.setIcon(QIcon(os.path.join(icon_path, "undo.png")))
        # self.redo_action.setIcon(QIcon(os.path.join(icon_path, "redo.png")))

        self.tool_open_action = QAction(QIcon(os.path.join(icon_path, "打开.png")), "打开", self)
        self.tool_save_action = QAction(QIcon(os.path.join(icon_path, "保存.png")), "保存", self)
        self.tool_save_as_action = QAction(QIcon(os.path.join(icon_path, "另存为1.png")), "另存为", self)
        self.undo_action = QAction(QIcon(os.path.join(icon_path, "undo.png")), "undo", self)
        self.redo_action = QAction(QIcon(os.path.join(icon_path, "redo.png")), "redo", self)
        self.tool_select_action = QAction(QIcon(os.path.join(icon_path, "选择.png")), "点选", self)
        self.tool_brush_action = QAction(QIcon(os.path.join(icon_path, "笔刷工具.png")), "笔刷", self)
        self.tool_circle_action = QAction(QIcon(os.path.join(icon_path, "圆形工具.png")), "圆形", self)
        self.tool_line_action = QAction(QIcon(os.path.join(icon_path, "直线工具.png")), "直线", self)
        self.tool_func_action = QAction(QIcon(os.path.join(icon_path, "fx.png")), "函数", self)
        self.tool_fan_action = QAction(QIcon(os.path.join(icon_path, "风扇设置.png")), "风机", self)
        self.tool_time_action = QAction(QIcon(os.path.join(icon_path, "时间设置.png")), "时间", self)
        self.tool_template_action = QAction(QIcon(os.path.join(icon_path, "模板库.png")), "模板", self)
        self.tool_sim_action = QAction(QIcon(os.path.join(icon_path, "仿真分析1.png")), "仿真", self)
        self.tool_3d_view_action = QAction(QIcon(os.path.join(icon_path, "fx.png")), "3D视图", self)  # 暂时使用fx图标

        toolbar.addAction(self.tool_open_action)
        toolbar.addAction(self.tool_save_action)
        toolbar.addAction(self.tool_save_as_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.tool_select_action)
        toolbar.addAction(self.tool_brush_action)
        toolbar.addAction(self.tool_circle_action)
        toolbar.addAction(self.tool_line_action)
        toolbar.addAction(self.tool_func_action)
        toolbar.addSeparator()
        toolbar.addAction(self.tool_fan_action)
        toolbar.addAction(self.tool_time_action)
        toolbar.addAction(self.tool_template_action)
        toolbar.addSeparator()
        toolbar.addAction(self.tool_sim_action)
        toolbar.addSeparator()
        toolbar.addAction(self.tool_3d_view_action)

    @Slot(float)
    def _apply_speed_to_selected_fans(self, speed):
        """将速度应用到选中的风扇，并根据设置应用羽化 (最终修复版)"""
        self.data_before_edit = np.copy(self.canvas_widget.grid_data)

        # 决定从哪个工具窗口获取羽化设置
        current_tool_widget = self.tool_stack.currentWidget()
        feather_enabled = False
        feather_value = 0
        if hasattr(current_tool_widget, 'is_feathering_enabled'):
            feather_enabled = current_tool_widget.is_feathering_enabled()
            feather_value = current_tool_widget.get_feather_value()
        affected_count = self.canvas_widget.apply_speed_and_feather_to_selection(
            speed, feather_enabled, feather_value
        )
        if affected_count > 0:
            description = f"设置 {affected_count} 个风扇速度为 {speed}%"
            if feather_enabled:
                description += f" (羽化: {feather_value})"
            self._push_edit_command(description)

            self._add_info_message(f"已将 {affected_count} 个风扇单元的速度设置为 {speed}%")
            if feather_enabled:
                self._add_info_message(f"并应用了 {feather_value} 层的羽化")

            # 【新增】如果启用了UDP自动发送，则发送数据
            if self.udp_send_on_change:
                self._send_pwm_data_via_udp(selected_only=True)

            # 【新增】数据变化后立即同步到Web端（事件驱动）
            self._sync_to_web()
        else:
            self._add_info_message("没有选中的风扇单元")
    
    def _push_edit_command(self, description):
        """推送编辑命令到撤销栈"""
        if self.data_before_edit is not None:
            command = EditCommand(
                self.canvas_widget,
                self.data_before_edit,
                self.canvas_widget.grid_data,
                description
            )
            self.undo_stack.push(command)
            self.data_before_edit = None

    def _create_statusbar(self):
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪。")

    # ==================== UDP发送相关方法 ====================

    def _init_udp_sender(self):
        """初始化UDP发送器"""
        try:
            if self.udp_async_mode:
                self.udp_sender = AsyncFanUDPSender(enable_logging=True)
                self.udp_sender.start()  # 【修复】启动后台发送线程
                self._add_info_message("UDP发送器已初始化 (异步模式)")
                self._add_info_message("UDP后台发送线程已启动")
            else:
                self.udp_sender = FanUDPSender(enable_logging=True)
                self._add_info_message("UDP发送器已初始化 (同步模式)")
        except Exception as e:
            self._add_info_message(f"UDP发送器初始化失败: {e}")
            self.udp_sender = None

    def toggle_udp_sender(self, enabled: bool):
        """切换UDP发送器状态"""
        self.udp_enabled = enabled
        if enabled:
            if self.udp_sender is None:
                self._init_udp_sender()
            # 【新增】确保异步发送器已启动
            elif self.udp_async_mode and hasattr(self.udp_sender, 'running'):
                if not self.udp_sender.running:
                    self.udp_sender.start()
                    self._add_info_message("UDP后台发送线程已启动")
            self._add_info_message("UDP发送已启用")
            self._add_info_message("目标: 10个IP (192.168.1.100-109:6005), 每IP管10组风扇")
        else:
            self._add_info_message("UDP发送已禁用")

    def _init_udp_listener(self):
        """初始化UDP返回数据监听器"""
        try:
            self.udp_listener = FanUDPListener(
                callback=self._on_udp_raw_data
            )
            self.udp_listener.start()
            self._add_info_message("UDP返回数据监听已启动 (端口: 6001)")
        except Exception as e:
            self._add_info_message(f"UDP监听器初始化失败: {e}")
            self.udp_listener = None

    def _on_udp_raw_data(self, data: bytes, addr: tuple):
        """UDP监听回调（在后台线程中调用）- 通过信号桥接到UI线程"""
        self._listener_bridge.data_received.emit(data)

    @Slot(bytes)
    def _on_listener_data(self, data: bytes):
        """UI线程中处理电驱板返回数据"""
        if hasattr(self, 'feedback_panel') and self.feedback_panel:
            self.feedback_panel.display_raw_data(data)

    def toggle_udp_listener(self, enabled: bool):
        """切换UDP监听器状态"""
        if enabled:
            if self.udp_listener is None:
                self._init_udp_listener()
            elif not self.udp_listener.running:
                self.udp_listener.start()
                self._add_info_message("UDP返回数据监听已启动")
        else:
            if self.udp_listener:
                self.udp_listener.stop()
                self._add_info_message("UDP返回数据监听已停止")

    def _init_web_sync(self):
        """初始化Web同步客户端"""
        try:
            # 延迟导入，避免启动时失败
            from modules.core.data_sync.web_sync_client import get_web_sync_client
            self.web_sync_client = get_web_sync_client()
            self._add_info_message("Web同步客户端已初始化")
        except Exception as e:
            self.web_sync_client = None
            self._add_info_message(f"Web同步客户端初始化失败: {e}")

    def _sync_to_web(self):
        """同步风扇数据到Web端"""
        if not self.web_sync_client:
            self._add_info_message("Web同步未启用：同步客户端未初始化")
            return

        try:
            # 直接将numpy数组转换为Python list（0-100 → 0-1000 PWM值）
            # tolist() 比 Python 循环快得多，且直接产生原生Python类型
            fan_array = (self.canvas_widget.grid_data * 10).astype(int).tolist()
            self.web_sync_client.sync_fan_array(fan_array)
        except Exception as e:
            self._add_info_message(f"Web同步失败: {e}")

    def set_udp_send_on_change(self, enabled: bool):
        """设置数据变化时自动发送"""
        self.udp_send_on_change = enabled
        status = "启用" if enabled else "禁用"
        self._add_info_message(f"数据变化自动发送已{status}")

        # 同步更新菜单状态（避免循环信号）
        self.menu_udp_auto_send_action.blockSignals(True)
        self.menu_udp_auto_send_action.setChecked(enabled)
        self.menu_udp_auto_send_action.blockSignals(False)

    def _send_pwm_data_via_udp(self, selected_only: bool = False):
        """通过UDP发送PWM数据

        Args:
            selected_only: 是否只发送选中的风扇
        """
        if not self.udp_enabled or self.udp_sender is None:
            # 【修复】减少日志输出，避免刷屏
            # self._add_info_message("[UDP] 发送失败: UDP未启用或发送器未初始化")
            return

        grid_data = self.canvas_widget.get_grid_data()

        if selected_only:
            selected_cells = self.canvas_widget.get_selected_cells()
            if not selected_cells:
                return
            # 【修复】简化日志
            self.udp_sender.queue_send_selected(grid_data, selected_cells, self._udp_send_callback)
        else:
            # 【修复】统一使用80字节批量包模式
            if isinstance(self.udp_sender, AsyncFanUDPSender):
                # 异步模式：使用队列，不传callback（避免跨线程调用）
                self.udp_sender.queue_send_bulk(grid_data, callback=None)
            else:
                # 同步模式：直接发送
                self.udp_sender.send_grid_to_boards_bulk(grid_data, self._udp_send_callback)

    def _udp_send_callback(self, success_count: int, fail_count: int, elapsed_time: float):
        """UDP发送回调函数 - 批量回调"""
        if fail_count == 0:
            self._add_info_message(f"[UDP] 发送完成: 100个板全部成功, 耗时{elapsed_time*1000:.0f}ms")
        else:
            self._add_info_message(f"[UDP] 发送完成: {success_count}成功/{fail_count}失败, 耗时{elapsed_time*1000:.0f}ms")

    def send_all_fans_udp(self):
        """手动触发发送所有风扇数据"""
        self._send_pwm_data_via_udp(selected_only=False)
        self._add_info_message("已发送所有风扇数据")

    def send_selected_fans_udp(self):
        """手动触发发送选中的风扇数据"""
        self._send_pwm_data_via_udp(selected_only=True)
        self._add_info_message("已发送选中风扇数据")

    def get_udp_statistics(self):
        """获取UDP发送统计信息"""
        if self.udp_sender:
            return self.udp_sender.get_statistics()
        return None

    def print_udp_statistics(self):
        """打印UDP发送统计信息"""
        if self.udp_sender:
            self.udp_sender.print_statistics()
        else:
            self._add_info_message("UDP发送器未初始化")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 关闭UDP监听器
        if self.udp_listener:
            self.udp_listener.stop()
        # 关闭UDP发送器
        if self.udp_sender:
            if isinstance(self.udp_sender, AsyncFanUDPSender):
                self.udp_sender.stop()
            self.udp_sender.close()
        event.accept()

# main_window.py -> MainWindow

# main_window.py -> MainWindow

    def _connect_signals(self):
        """连接所有信号和槽"""
        # 画布相关信号
        self.canvas_widget.selection_changed.connect(self.selection_widget.update_selection_info)
        self.canvas_widget.selection_changed.connect(self.circle_widget.update_selection_info) # 新增
        self.canvas_widget.selection_changed.connect(self._update_info_output)
        self.canvas_widget.fan_hover.connect(self._update_fan_hover_info)
        self.canvas_widget.fan_hover_exit.connect(self._clear_fan_hover_info)
        
        # 选择工具widget信号
        self.selection_widget.apply_speed_signal.connect(self._apply_speed_to_selected_fans)
        self.selection_widget.invert_selection_signal.connect(self.canvas_widget.invert_selection)
        self.selection_widget.reset_button.clicked.connect(self._reset_all_fans_to_zero)
        self.selection_widget.select_all_button.clicked.connect(self.canvas_widget.select_all_cells)
        self.selection_widget.set_all_speed_signal.connect(self._set_all_fans_to_speed)

        # 【新增】圆形工具信号
        self.circle_widget.apply_speed_signal.connect(self._apply_speed_to_selected_fans)
        
        # 【新增】所有工具窗口的全部清零信号
        self.brush_widget.clear_all_signal.connect(self._reset_all_fans_to_zero)
        self.circle_widget.clear_all_signal.connect(self._reset_all_fans_to_zero)
        self.line_widget.clear_all_signal.connect(self._reset_all_fans_to_zero)
        self.function_widget.clear_all_signal.connect(self._reset_all_fans_to_zero)

        # 【新增】函数工具应用信号
        self.function_widget.apply_function_signal.connect(self._apply_function_to_grid)
        self.function_widget.preview_animation_signal.connect(self._preview_function_animation)

        # 时间条信号
        self.timeline_widget.time_changed.connect(self._on_time_changed)
        self.timeline_widget.play_state_changed.connect(self._on_play_state_changed)
        
        # 文件操作连接
        self.menu_open_action.triggered.connect(self._open_file)
        self.tool_open_action.triggered.connect(self._open_file)

        self.menu_save_action.triggered.connect(self._save_file)
        self.tool_save_action.triggered.connect(self._save_file)
        self.menu_save_as_action.triggered.connect(self._save_as_file)
        self.tool_save_as_action.triggered.connect(self._save_as_file)
        self.menu_exit_action.triggered.connect(self.close)

        # 【新增】模版库窗口信号连接
        self.template_window.load_template_signal.connect(self._load_template)
        self.template_window.delete_template_signal.connect(self._delete_template)
        
        # 工具模式连接
        self.menu_selection_action.triggered.connect(self._show_selection_tool)
        self.tool_select_action.triggered.connect(self._show_selection_tool)
        self.menu_brush_tool_action.triggered.connect(self._show_brush_tool)
        self.tool_brush_action.triggered.connect(self._show_brush_tool)
        self.menu_circle_tool_action.triggered.connect(self._show_circle_tool)
        self.tool_circle_action.triggered.connect(self._show_circle_tool)
        self.menu_line_tool_action.triggered.connect(self._show_line_tool)
        self.tool_line_action.triggered.connect(self._show_line_tool)
        self.menu_function_generator_action.triggered.connect(self._show_function_tool)
        self.tool_func_action.triggered.connect(self._show_function_tool)
        self.menu_run_sim_action.triggered.connect(self.launch_cfd_interface)
        self.tool_sim_action.triggered.connect(self.launch_cfd_interface)
        
        # 设置连接
        self.menu_fan_settings_action.triggered.connect(self._show_fan_settings)
        self.tool_fan_action.triggered.connect(self._show_fan_settings)
        self.menu_time_settings_action.triggered.connect(self._show_time_settings)
        self.tool_time_action.triggered.connect(self._show_time_settings)
        self.menu_template_library_action.triggered.connect(self._show_template_library)
        self.tool_template_action.triggered.connect(self._show_template_library)
        self.menu_debug_mode_action.toggled.connect(self._toggle_debug_mode)
        self.tool_3d_view_action.triggered.connect(self._show_3d_view)

        # 【新增】UDP控制菜单连接
        self.menu_udp_enable_action.toggled.connect(self.toggle_udp_sender)
        self.menu_udp_auto_send_action.toggled.connect(self.set_udp_send_on_change)
        self.menu_udp_send_all_action.triggered.connect(self.send_all_fans_udp)
        self.menu_udp_send_selected_action.triggered.connect(self.send_selected_fans_udp)
        self.menu_udp_stats_action.triggered.connect(self.print_udp_statistics)
        self.menu_udp_auto_parse_action.toggled.connect(self.toggle_udp_listener)

        # 【新增】UDP监听器信号连接
        self._listener_bridge.data_received.connect(self._on_listener_data)

        # 笔刷widget参数变化信号
        self.brush_widget.brush_size_spinbox.valueChanged.connect(self.canvas_widget.update_brush_preview)
        self.brush_widget.brush_value_input.textChanged.connect(self.canvas_widget.update_brush_preview)




    def set_cfd_launch_function(self, func):
        self.launch_cfd_function = func
        print("[MainControl] CFD launch function has been injected.")

    @Slot()
    def _open_file(self):
        self._add_info_message("打开文件功能暂未实现")
            
    @Slot()
    def _save_file(self):
        self._add_info_message("保存文件功能暂未实现")
        
    @Slot()
    def _save_as_file(self):
        self._add_info_message("另存为功能暂未实现")
            
    @Slot()
    def _show_selection_tool(self):
        self.tool_stack.setCurrentWidget(self.selection_widget)
        self.tool_mode_group.setTitle("点选模式")
        self.canvas_widget.update_brush_preview()
        self._add_info_message("切换到 [选择模式]")

    @Slot()
    def _show_brush_tool(self):
        self.tool_stack.setCurrentWidget(self.brush_widget)
        self.tool_mode_group.setTitle("笔刷模式")
        self.canvas_widget.update_brush_preview()
        self._add_info_message("切换到 [笔刷模式]")
        
    @Slot()
    def _show_circle_tool(self):
        self.tool_stack.setCurrentWidget(self.circle_widget)
        self.tool_mode_group.setTitle("圆形工具模式")
        self.canvas_widget.update_brush_preview()
        self._add_info_message("切换到 [圆形工具模式]")
        
    @Slot()
    def _show_line_tool(self):
        self.tool_stack.setCurrentWidget(self.line_widget)
        self.tool_mode_group.setTitle("直线工具模式")
        self.canvas_widget.update_brush_preview()
        self._add_info_message("切换到 [直线工具模式]")
    @Slot()
    def _show_function_tool(self):
        """切换到函数工具"""
        self.tool_stack.setCurrentWidget(self.function_widget)
        self.tool_mode_group.setTitle("函数模式")
        self.canvas_widget.update_brush_preview()
        self._add_info_message("切换到 [函数模式]")

    @Slot()
    def _show_fan_settings(self):
        if self.fan_settings_window.exec() == QDialog.Accepted:
            self._apply_fan_settings()
            
    @Slot()
    def _show_time_settings(self):
        if self.time_settings_window.exec() == QDialog.Accepted:
            self._apply_time_settings()
            
    @Slot()
    def _show_template_library(self):
        self.template_window.show()
        self.template_window.raise_()

    @Slot(str)
    def _load_template(self, template_name: str):
        """
        加载模版

        Args:
            template_name: 模版名称
        """
        # TODO: 实现从文件加载模版的逻辑
        # 这里先提供几个预设模版的实现
        import numpy as np

        # 保存当前状态用于撤销
        self.data_before_edit = self.canvas_widget.grid_data.copy()

        if template_name == "中心高斯喷流_v1":
            # 高斯分布模版
            self._apply_gaussian_template()
        elif template_name == "左右扫描风_初始":
            # 左右扫描风模版
            self._apply_scan_template()
        elif template_name == "城市峡谷风":
            # 城市峡谷风模版
            self._apply_canyon_template()
        else:
            self._add_info_message(f"未知模版: {template_name}")
            return

        # 推送撤销命令
        self._push_edit_command(f"加载模版: {template_name}")

        # 更新画布
        self.canvas_widget.update()

        # 【关键】同步到Web端
        self._sync_to_web()

        # 【新增】如果启用了UDP自动发送，则发送数据
        if self.udp_send_on_change:
            self._send_pwm_data_via_udp(selected_only=False)

        self._add_info_message(f"已加载模版: {template_name}")

    @Slot(str)
    def _delete_template(self, template_name: str):
        """
        删除模版

        Args:
            template_name: 模版名称
        """
        # TODO: 实现删除模版文件的逻辑
        self._add_info_message(f"已删除模版: {template_name}")

    def _apply_gaussian_template(self):
        """应用高斯分布模版"""
        import numpy as np
        center = (20, 20)
        sigma = 5.0
        amplitude = 100.0

        y_indices, x_indices = np.indices((40, 40))
        distance_sq = (x_indices - center[1])**2 + (y_indices - center[0])**2
        gaussian = amplitude * np.exp(-distance_sq / (2 * sigma**2))

        self.canvas_widget.grid_data[:, :] = gaussian

    def _apply_scan_template(self):
        """应用左右扫描风模版"""
        import numpy as np
        # 创建一个从左到右的渐变
        x_gradient = np.linspace(0, 100, 40)
        grid = np.tile(x_gradient, (40, 1))
        self.canvas_widget.grid_data[:, :] = grid

    def _apply_canyon_template(self):
        """应用城市峡谷风模版"""
        import numpy as np
        # 创建中间高、两边低的分布
        center = 20
        width = 10
        x = np.arange(40)
        canyon = 100 * np.exp(-((x - center)**2) / (2 * width**2))
        grid = np.tile(canyon, (40, 1))
        self.canvas_widget.grid_data[:, :] = grid

    @Slot()
    def _show_3d_view(self):
        """打开3D视图窗口"""
        self.function_3d_view.open_3d_window()
        self._add_info_message("已打开3D函数视图窗口")

    @Slot()
    def _function_generator_placeholder(self):
        self._add_info_message("函数生成器功能暂未实现")

    @Slot(str, dict, float)
    def _apply_function_to_grid(self, function_type: str, params: dict, time_value: float):
        """
        应用数学函数到风场网格

        Args:
            function_type: 函数类型
            params: 函数参数
            time_value: 时间参数
        """
        try:
            # 使用导入辅助模块获取函数类
            from . import import_helper

            WindFieldFunctionFactory = import_helper.get_function_factory()
            if WindFieldFunctionFactory is None:
                self._add_info_message("错误: 无法导入函数模块")
                return

            FunctionParams = import_helper.get_function_classes().get('FunctionParams')
            CustomExpressionFunction = import_helper.get_function_classes().get('CustomExpressionFunction')

            if FunctionParams is None:
                self._add_info_message("错误: 无法导入FunctionParams")
                return

            # 保存当前状态
            self.data_before_edit = np.copy(self.canvas_widget.grid_data)

            # 创建参数
            function_params = FunctionParams()

            # 解析中心位置
            if 'center' in params and len(params['center']) == 2:
                # 直接使用行列坐标
                row_center, col_center = params['center']
                function_params.center = (row_center, col_center)
                # 显示为1-based索引
                display_x = int(col_center) + 1
                display_y = int(row_center) + 1
                self._add_info_message(f"中心位置: x{display_x:03d}y{display_y:03d}")

            if 'amplitude' in params:
                function_params.amplitude = params['amplitude']

            # 创建函数
            func = WindFieldFunctionFactory.create(function_type, function_params)

            # 对于自定义表达式，需要设置表达式
            if function_type == 'custom_expression' and 'expression' in params:
                if isinstance(func, CustomExpressionFunction):
                    func.set_expression(params['expression'])
                    self._add_info_message(f"自定义表达式: {params['expression']}")

            # 创建临时网格用于函数计算
            grid_shape = self.canvas_widget.grid_data.shape
            temp_grid = np.zeros(grid_shape)

            # 应用函数
            result_grid = func.apply(temp_grid, time=time_value)

            # 更新画布数据
            self.canvas_widget.grid_data = result_grid

            # 推送撤销命令（redo() 会调用 update_all_cells_from_data，不要重复调用）
            description = f"应用函数: {function_type}"
            if time_value > 0:
                description += f" (t={time_value:.2f}s)"
            self._push_edit_command(description)

            # 输出信息
            stats = self.canvas_widget.grid_data
            self._add_info_message(f"已应用 [{function_type}] 函数")
            self._add_info_message(f"  最大值: {stats.max():.2f}%, 最小值: {stats.min():.2f}%")
            self._add_info_message(f"  平均值: {stats.mean():.2f}%")

            # 更新3D视图
            self.function_3d_view.set_grid_data(result_grid)
            self.function_3d_view.current_function = function_type
            self.function_3d_view.current_time = time_value

            # 保存当前函数参数供时间轴使用
            self.current_function_params = (function_type, params)

            # 【新增】如果启用了UDP自动发送，则发送数据
            if self.udp_send_on_change:
                self._send_pwm_data_via_udp(selected_only=False)

            # 同步到Web端
            self._sync_to_web()

        except ImportError as e:
            self._add_info_message(f"错误: 无法导入wind_field_editor模块: {e}")
            self._add_info_message("请确保wind_field_editor模块在项目根目录")

        except Exception as e:
            self._add_info_message(f"应用函数失败: {e}")
            import traceback
            traceback.print_exc()

    @Slot(str, dict)
    def _preview_function_animation(self, function_type: str, params: dict):
        """
        预览函数动画 - 使用时间轴的时间

        Args:
            function_type: 函数类型
            params: 函数参数
        """
        try:
            # 保存当前函数参数供时间轴使用
            self.current_function_params = (function_type, params)

            # 重置时间轴到开始位置
            self.timeline_widget.set_current_time(0.0)

            # 使用时间轴的当前时间应用函数
            current_time = self.timeline_widget.get_current_time()
            result_grid = self._apply_function_without_undo(function_type, params, current_time)

            # 更新3D视图
            if result_grid is not None:
                self.function_3d_view.set_grid_data(result_grid)
                self.function_3d_view.current_function = function_type
                self.function_3d_view.current_time = current_time

            self._add_info_message(f"函数已激活: {function_type}")
            self._add_info_message(f"拖动时间轴可查看动画效果")
            self._add_info_message(f"时间范围: 0 - {self.max_time:.1f}秒")

        except Exception as e:
            self._add_info_message(f"启动函数失败: {e}")
            import traceback
            traceback.print_exc()

    def _apply_function_without_undo(self, function_type: str, params: dict, time_value: float):
        """应用函数但不保存到撤销栈（用于动画预览）"""
        try:
            # 使用导入辅助模块获取函数类
            from . import import_helper

            WindFieldFunctionFactory = import_helper.get_function_factory()
            if WindFieldFunctionFactory is None:
                self._add_info_message("错误: 无法导入函数模块")
                return None

            FunctionParams = import_helper.get_function_classes().get('FunctionParams')
            CustomExpressionFunction = import_helper.get_function_classes().get('CustomExpressionFunction')

            if FunctionParams is None:
                self._add_info_message("错误: 无法导入FunctionParams")
                return None

            # 创建参数
            function_params = FunctionParams()

            # 解析中心位置
            if 'center' in params and len(params['center']) == 2:
                row_center, col_center = params['center']
                function_params.center = (row_center, col_center)

            if 'amplitude' in params:
                function_params.amplitude = params['amplitude']

            # 创建函数
            func = WindFieldFunctionFactory.create(function_type, function_params)

            # 对于自定义表达式，需要设置表达式
            if function_type == 'custom_expression' and 'expression' in params:
                if isinstance(func, CustomExpressionFunction):
                    func.set_expression(params['expression'])

            # 创建临时网格用于函数计算
            grid_shape = self.canvas_widget.grid_data.shape
            temp_grid = np.zeros(grid_shape)

            # 应用函数
            result_grid = func.apply(temp_grid, time=time_value)

            # 更新画布
            self.canvas_widget.grid_data = result_grid
            self.canvas_widget.update_all_cells_from_data()
            self.canvas_widget.update()

            # 返回结果网格供3D视图使用
            return result_grid

        except Exception as e:
            self._add_info_message(f"应用函数失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    @Slot()
    def _apply_fan_settings(self):
        max_rpm = self.fan_settings_window.get_max_rpm()
        self.max_rpm = max_rpm
        self._add_info_message(f"风机最大转速设置为: {max_rpm} RPM")
        
    @Slot()
    def _apply_time_settings(self):
        max_time = self.time_settings_window.get_max_time()
        resolution = self.time_settings_window.get_time_resolution()
        self.max_time = max_time
        self.time_resolution = resolution
        self.timeline_widget.set_max_time(max_time)
        self.timeline_widget.set_time_resolution(resolution)
        self._add_info_message(f"时间设置更新: 最大时间={max_time}s, 分辨率={resolution}s")
        
    @Slot(bool)
    def _toggle_debug_mode(self, enabled):
        self.debug_mode = enabled
        status = "开启" if enabled else "关闭"
        self._add_info_message(f"调试模式已{status}")
        
    @Slot(float)
    def _on_time_changed(self, time_value):
        """时间轴时间变化时更新函数动画"""
        # 如果有当前的函数参数，根据时间更新函数
        if hasattr(self, 'current_function_params') and self.current_function_params:
            function_type, params = self.current_function_params

            # 应用函数并获取网格数据
            result_grid = self._apply_function_without_undo(function_type, params, time_value)

            # 更新3D视图
            if result_grid is not None:
                self.function_3d_view.set_grid_data(result_grid)
                self.function_3d_view.current_time = time_value

            # 【修复】播放时自动发送UDP数据 - 减少日志输出
            if hasattr(self, 'is_playing') and self.is_playing:
                if self.udp_enabled and self.udp_send_on_play:
                    # 使用80字节批量模式
                    self._send_pwm_data_via_udp(selected_only=False)

                # 同步到Web端
                self._sync_to_web()

        # 【修复】减少调试日志输出频率，避免UI卡顿
        # if self.debug_mode:
        #     self._add_info_message(f"时间设置为: {time_value:.2f}s")

    @Slot(bool)
    def _on_play_state_changed(self, is_playing):
        """播放状态变化时的处理"""
        self.is_playing = is_playing  # 记录播放状态

        # 【关键优化】设置UDP发送器的播放模式标志
        # 播放时跳过磁盘日志记录，大幅提升发送速度
        if self.udp_sender is not None:
            self.udp_sender.playback_mode = is_playing

        # 【新增】3D视图播放时禁止旋转
        if hasattr(self, 'function_3d_view') and self.function_3d_view:
            d3d_window = self.function_3d_view.d3d_window
            if d3d_window:
                d3d_window.set_playback_active(is_playing)

        status = "播放" if is_playing else "暂停"
        self._add_info_message(f"时间条{status}")

        if is_playing:
            self._add_info_message("=== 播放开始 ===")
            if self.udp_enabled and self.udp_send_on_play:
                self._add_info_message("播放时自动发送UDP数据: 已启用（高速模式）")
                self._add_info_message(f"将每隔 {self.time_resolution}s 发送一次数据（跳过日志记录）")
                if hasattr(self, 'current_function_params') and self.current_function_params:
                    self._send_pwm_data_via_udp(selected_only=False)
            else:
                if self.udp_enabled:
                    self._add_info_message("播放时自动发送UDP数据: 未启用")
                else:
                    self._add_info_message("UDP发送未启用 - 请在UDP控制菜单中启用")
        else:
            self._add_info_message("=== 播放停止 ===")
        
    def _add_info_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.info_output.append(formatted_message)
        if self.debug_mode:
            print(f"[Info] {formatted_message}")
        
    @Slot()
    def _update_info_output(self):
        selected_count = len(self.canvas_widget.get_selected_cells())
        if selected_count > 0:
            self._add_info_message(f"选中了 {selected_count} 个风扇单元")
            
    @Slot()
    def launch_cfd_interface(self):
        """启动前处理程序"""
        import subprocess
        import sys

        self._add_info_message("正在启动前处理程序...")

        # 获取前处理 main.py 的路径
        pre_processor_main = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            '前处理', 'main.py'
        )

        try:
            # 使用当前 Python 解释器启动前处理程序
            subprocess.Popen([sys.executable, pre_processor_main])
            self._add_info_message("前处理程序已启动")
        except Exception as e:
            self._add_info_message(f"启动前处理程序失败: {e}")

    def generate_time_series_data(self):
        """生成时间序列数据"""
        import numpy as np

        # 计算时间点数量
        num_time_points = int(self.max_time / self.time_resolution) + 1

        # 生成时间点数组
        time_points = np.linspace(0, self.max_time, num_time_points)

        # 获取当前网格数据（风扇转速百分比）
        grid_data_percent = self.canvas_widget.get_grid_data()

        # 转换为实际转速 (RPM)
        grid_data_rpm = (grid_data_percent / 100.0 * self.max_rpm).astype(int)

        # 生成每个时间点的风扇转速数据
        # 假设所有时间点使用相同的转速设置（可根据需要修改）
        time_series_rpm = np.tile(grid_data_rpm, (num_time_points, 1, 1))

        # 构建数据字典
        time_series_data = {
            'time_points': time_points,
            'time_resolution': self.time_resolution,
            'max_time': self.max_time,
            'max_rpm': self.max_rpm,
            'grid_shape': grid_data_rpm.shape,
            'rpm_data': time_series_rpm,  # shape: (time, rows, cols)
            'metadata': {
                'generated_by': 'Wind Wall Settings',
                'description': 'Time series fan RPM data for CFD simulation'
            }
        }

        return time_series_data

# main_window.py -> MainWindow



    @Slot(int, int, int, float)
    def _update_fan_hover_info(self, fan_id_temp, row, col, pwm_ratio):
        x_coord = col
        y_coord = row
        fan_id_str = f"X{x_coord:03}Y{y_coord:03}"
        
        self.fan_id_label.setText(fan_id_str)
        self.fan_position_label.setText(f"({row}, {col})")
        self.fan_pwm_label.setText(f"{pwm_ratio:.1f}%")

        speed1 = int(self.max_rpm * pwm_ratio / 100)
        speed2 = int(14600 * pwm_ratio / 100)
        self.fan_speed1_label.setText(f"{speed1} RPM")
        self.fan_speed2_label.setText(f"{speed2} RPM")

        current = 2.7 * (pwm_ratio / 100.0)
        power = 145.8 * (pwm_ratio / 100.0)
        self.fan_power_label.setText(f"{current:.2f}A, 54V, {power:.1f}W")
        
        # 【修改】只有在悬停时才启动/显示运行时间
        self.runtime_timer.start()
        self._update_runtime_display() # 立即更新一次


# main_window.py -> MainWindow

    @Slot()
    def _clear_fan_hover_info(self):
        self.fan_id_label.setText("--")
        self.fan_position_label.setText("--")
        self.fan_pwm_label.setText("--")
        self.fan_speed1_label.setText("--")
        self.fan_speed2_label.setText("--")
        self.fan_power_label.setText("--")
        # 【修改】鼠标移出时，停止计时器并清空显示
        self.runtime_timer.stop()
        self.fan_runtime_label.setText("--")


    @Slot()
    def _update_runtime_display(self):
        """槽函数：由QTimer调用，每秒更新运行时间"""
        elapsed = datetime.now() - self.start_time
        total_runtime = self.base_runtime + elapsed
        
        # 格式化为 HHHHh MMm SSs
        hours = total_runtime.days * 24 + total_runtime.seconds // 3600
        minutes = (total_runtime.seconds % 3600) // 60
        seconds = total_runtime.seconds % 60
        
        self.fan_runtime_label.setText(f"{hours:04d}h{minutes:02d}m{seconds:02d}s")

    @Slot()
    def _reset_all_fans_to_zero(self):
        """槽函数：将所有风扇的转速设置为0%并取消所有选择 (支持撤销)"""
        self.data_before_edit = np.copy(self.canvas_widget.grid_data)
        self.canvas_widget.grid_data.fill(0)
        # 取消所有选择
        self.canvas_widget.selected_cells.clear()
        # _push_edit_command 会触发 redo()，里面会调用 update_all_cells_from_data()
        # 不在这里重复调用，避免 3200 次格子更新导致卡顿
        self._push_edit_command("全部清零")
        self._add_info_message("所有风扇转速已清零，选择已取消")

        # 同步到Web端
        self._sync_to_web()

        # 如果启用了UDP自动发送，则发送数据
        if self.udp_send_on_change:
            self._send_pwm_data_via_udp(selected_only=False)

    @Slot(float)
    def _set_all_fans_to_speed(self, speed: float):
        """槽函数：将全部1600个风扇(100个模组)统一设置为同一转速 (支持撤销)"""
        self.data_before_edit = np.copy(self.canvas_widget.grid_data)
        self.canvas_widget.grid_data.fill(speed)
        self.canvas_widget.selected_cells.clear()
        self._push_edit_command(f"全部统一转速: {speed}%")
        self._add_info_message(f"已将全部1600个风扇转速统一设置为 {speed}%")

        # 同步到Web端
        self._sync_to_web()

        # 如果启用了UDP自动发送，则发送数据
        if self.udp_send_on_change:
            self._send_pwm_data_via_udp(selected_only=False)
    
    @Slot()
    def _update_undo_redo_text(self):
        """更新撤销/重做按钮文本，保持固定显示"""
        self.undo_action.setText("回退")
        self.redo_action.setText("前进")


