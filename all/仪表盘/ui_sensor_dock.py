# -*- coding: utf-8 -*-
"""
传感器数据采集和查看 Dock
集成数据采集和数据查看功能到仪表盘
使用与其他dock相同的DraggableFrame风格
包含三个标签页：数据采集、数据查看、MongoDB查看
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget
)
from PySide6.QtCore import Qt
import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui_custom_widgets import DraggableFrame
from ui_sensor_collection import (
    SensorDataCollectionTab,
    SensorDataViewTab,
    MongoDataViewTab
)


def create_sensor_data_dock(main_window):
    """
    创建传感器数据采集和查看Dock
    使用与其他dock相同的DraggableFrame风格
    包含三个标签页：数据采集、数据查看、MongoDB查看

    Args:
        main_window: 主窗口实例，用于回调

    Returns:
        DraggableFrame: 传感器数据Dock
    """
    # 创建中央widget（dock的内容）
    central_widget = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # 创建标签页
    tab_widget = QTabWidget()

    # 数据采集标签页
    collection_tab = SensorDataCollectionTab(main_window)
    tab_widget.addTab(collection_tab, "📊 数据采集")

    # 数据查看标签页
    view_tab = SensorDataViewTab()
    tab_widget.addTab(view_tab, "📁 数据查看")

    # MongoDB 数据查看标签页
    mongo_tab = MongoDataViewTab()
    tab_widget.addTab(mongo_tab, "🗄️ MongoDB")

    # 将view_tab保存到main_window，方便collection_tab回调
    main_window.sensor_data_view_tab = view_tab

    layout.addWidget(tab_widget)
    central_widget.setLayout(layout)

    # 使用与其他dock相同的DraggableFrame创建风格
    frame = DraggableFrame("传感器数据", main_window, is_independent_window=False)
    frame.setContentWidget(central_widget)
    frame.setMinimumSizeFromContent()

    # 设置默认大小和位置
    frame.resize(500, 600)
    frame.move(main_window.width() - 550, main_window.height() - 650)

    # 设置可见性标记
    frame._visible_before_hide = False

    return frame
