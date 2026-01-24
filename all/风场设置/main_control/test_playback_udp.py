# -*- coding: utf-8 -*-
"""
测试播放时自动发送UDP功能

测试内容：
1. 验证"数据变化时自动发送"复选框默认状态
2. 验证播放时自动发送UDP数据功能
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 模拟运行环境
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

def test_checkbox_default_state():
    """测试1: 验证复选框默认状态"""
    print("=" * 60)
    print("测试1: 验证复选框默认状态")
    print("=" * 60)
    print()

    # 延迟导入以避免Qt应用初始化问题
    from PySide6.QtWidgets import QApplication

    # 创建Qt应用（如果还没有）
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    # 导入MainWindow
    from main_control.main_window import MainWindow

    # 创建主窗口（使用Mock来跳过实际的GUI初始化）
    with patch('main_control.main_window.CanvasWidget'), \
         patch('main_control.main_window.TimelineWidget'), \
         patch('main_control.main_window.EnhancedFunctionToolWindow'), \
         patch('main_control.main_window.Function3DView'), \
         patch('main_control.main_window.FanUDPSender'), \
         patch('main_control.main_window.AsyncFanUDPSender'):

        try:
            window = MainWindow()

            # 检查默认状态
            checks = {
                "udp_send_on_change": window.udp_send_on_change,
                "udp_send_on_play": window.udp_send_on_play,
                "is_playing": window.is_playing,
            }

            all_ok = True
            for name, value in checks.items():
                expected = True if name != "is_playing" else False
                status = "[OK]" if value == expected else "[FAIL]"
                print(f"  {status} {name}: {value} (期望: {expected})")
                if value != expected:
                    all_ok = False

            print()
            if all_ok:
                print("  [OK] 复选框默认状态测试通过")
            else:
                print("  [FAIL] 复选框默认状态测试失败")

        except Exception as e:
            print(f"  [FAIL] 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print()


def test_playback_udp_send():
    """测试2: 验证播放时自动发送功能"""
    print("=" * 60)
    print("测试2: 验证播放时自动发送功能")
    print("=" * 60)
    print()

    from PySide6.QtWidgets import QApplication

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    from main_control.main_window import MainWindow

    with patch('main_control.main_window.CanvasWidget'), \
         patch('main_control.main_window.TimelineWidget'), \
         patch('main_control.main_window.EnhancedFunctionToolWindow'), \
         patch('main_control.main_window.Function3DView'), \
         patch('main_control.main_window.FanUDPSender'), \
         patch('main_control.main_window.AsyncFanUDPSender'):

        try:
            window = MainWindow()

            # 启用UDP
            window.udp_enabled = True

            # Mock UDP发送方法
            window._send_pwm_data_via_udp = Mock()
            window._add_info_message = Mock()

            # 测试1: 播放状态为False时不发送
            print("  测试1: 非播放状态")
            window.is_playing = False
            window._on_time_changed(1.0)

            if window._send_pwm_data_via_udp.called:
                print("    [FAIL] 非播放状态下不应发送UDP数据")
            else:
                print("    [OK] 非播放状态正确（未发送）")

            window._send_pwm_data_via_udp.reset_mock()

            # 测试2: 播放状态为True时发送
            print("  测试2: 播放状态")
            window.is_playing = True
            window.current_function_params = ("GaussianFunction", {"center": (20, 20), "amplitude": 100})
            window._on_time_changed(1.0)

            if window._send_pwm_data_via_udp.called:
                print("    [OK] 播放状态下正确发送UDP数据")
                # 检查调用参数
                call_args = window._send_pwm_data_via_udp.call_args
                print(f"    [OK] 调用参数: selected_only={call_args[1]['selected_only']}")
            else:
                print("    [FAIL] 播放状态下应发送UDP数据")

            window._send_pwm_data_via_udp.reset_mock()

            # 测试3: UDP未启用时不发送
            print("  测试3: UDP未启用")
            window.udp_enabled = False
            window.is_playing = True
            window._on_time_changed(1.0)

            if window._send_pwm_data_via_udp.called:
                print("    [FAIL] UDP未启用时不应发送")
            else:
                print("    [OK] UDP未启用时正确（未发送）")

            window._send_pwm_data_via_udp.reset_mock()

            # 测试4: udp_send_on_play为False时不发送
            print("  测试4: udp_send_on_play关闭")
            window.udp_enabled = True
            window.udp_send_on_play = False
            window.is_playing = True
            window._on_time_changed(1.0)

            if window._send_pwm_data_via_udp.called:
                print("    [FAIL] udp_send_on_play关闭时不应发送")
            else:
                print("    [OK] udp_send_on_play关闭时正确（未发送）")

        except Exception as e:
            print(f"  [FAIL] 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print()


def test_play_state_changed():
    """测试3: 验证播放状态变化处理"""
    print("=" * 60)
    print("测试3: 验证播放状态变化处理")
    print("=" * 60)
    print()

    from PySide6.QtWidgets import QApplication

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    from main_control.main_window import MainWindow

    with patch('main_control.main_window.CanvasWidget'), \
         patch('main_control.main_window.TimelineWidget'), \
         patch('main_control.main_window.EnhancedFunctionToolWindow'), \
         patch('main_control.main_window.Function3DView'), \
         patch('main_control.main_window.FanUDPSender'), \
         patch('main_control.main_window.AsyncFanUDPSender'):

        try:
            window = MainWindow()

            # 启用UDP
            window.udp_enabled = True
            window._add_info_message = Mock()

            # 测试播放开始
            print("  测试1: 播放开始")
            window._on_play_state_changed(True)

            if window.is_playing:
                print("    [OK] is_playing状态正确")
            else:
                print("    [FAIL] is_playing应为True")

            # 检查信息输出
            info_calls = window._add_info_message.call_args_list
            print(f"    [INFO] 信息输出数量: {len(info_calls)}")

            window._add_info_message.reset_mock()

            # 测试播放停止
            print("  测试2: 播放停止")
            window._on_play_state_changed(False)

            if not window.is_playing:
                print("    [OK] is_playing状态正确")
            else:
                print("    [FAIL] is_playing应为False")

        except Exception as e:
            print(f"  [FAIL] 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print()


if __name__ == "__main__":
    print()
    print("*" * 60)
    print("播放时自动发送UDP功能测试")
    print("*" * 60)
    print()

    # 运行所有测试
    test_checkbox_default_state()
    test_playback_udp_send()
    test_play_state_changed()

    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)
    print()
    print("功能说明:")
    print("  1. '数据变化时自动发送'复选框默认勾选")
    print("  2. 播放动画时自动发送UDP数据")
    print("  3. 只有在UDP启用且udp_send_on_play启用时才发送")
    print()
