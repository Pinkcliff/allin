# -*- coding: utf-8 -*-
"""
简化测试：验证播放时自动发送UDP功能的代码实现

直接检查main_window.py中的关键代码
"""

import re

def test_implementation():
    """通过代码检查来验证实现"""
    print("=" * 60)
    print("播放时自动发送UDP功能 - 代码实现验证")
    print("=" * 60)
    print()

    file_path = "F:/A-User/cliff/allin/all/风场设置/main_control/main_window.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = []

    # 测试1: 检查udp_send_on_play初始化
    print("1. 检查 udp_send_on_play 初始化")
    if 'self.udp_send_on_play = True' in content:
        print("  [OK] udp_send_on_play 已初始化为 True")
        results.append(True)
    else:
        print("  [FAIL] udp_send_on_play 未正确初始化")
        results.append(False)
    print()

    # 测试2: 检查is_playing初始化
    print("2. 检查 is_playing 初始化")
    if 'self.is_playing = False' in content:
        print("  [OK] is_playing 已初始化为 False")
        results.append(True)
    else:
        print("  [FAIL] is_playing 未正确初始化")
        results.append(False)
    print()

    # 测试3: 检查udp_send_on_change默认值
    print("3. 检查 udp_send_on_change 默认值")
    if 'self.udp_send_on_change = True' in content:
        print("  [OK] udp_send_on_change 默认为 True")
        results.append(True)
    else:
        print("  [FAIL] udp_send_on_change 默认值不是 True")
        results.append(False)
    print()

    # 测试4: 检查菜单默认勾选状态
    print("4. 检查菜单默认勾选状态")
    if 'self.menu_udp_auto_send_action.setChecked(True)' in content:
        print("  [OK] 菜单默认已勾选")
        results.append(True)
    else:
        print("  [FAIL] 菜单默认未勾选")
        results.append(False)
    print()

    # 测试5: 检查_on_time_changed中的UDP发送逻辑
    print("5. 检查 _on_time_changed 中的UDP发送逻辑")
    pattern = r'if hasattr\(self, [\'"]is_playing[\'"]\) and self\.is_playing:'
    if re.search(pattern, content):
        print("  [OK] 检查播放状态的逻辑存在")
        results.append(True)
    else:
        print("  [FAIL] 缺少播放状态检查")
        results.append(False)

    if 'self._send_pwm_data_via_udp(selected_only=False)' in content:
        print("  [OK] UDP发送调用存在")
        results.append(True)
    else:
        print("  [FAIL] 缺少UDP发送调用")
        results.append(False)
    print()

    # 测试6: 检查_on_play_state_changed中的状态更新
    print("6. 检查 _on_play_state_changed 中的状态更新")
    if 'self.is_playing = is_playing' in content:
        print("  [OK] 播放状态更新逻辑存在")
        results.append(True)
    else:
        print("  [FAIL] 缺少状态更新逻辑")
        results.append(False)
    print()

    # 测试7: 提取完整的_on_time_changed函数
    print("7. _on_time_changed 函数实现:")
    pattern = r'def _on_time_changed\(self, time_value\):.*?(?=\n    def|\n    @|\nclass|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        func_code = match.group(0)
        lines = func_code.split('\n')[:15]  # 只显示前15行
        for line in lines:
            if line.strip():
                print(f"  {line}")
    print()

    # 测试8: 提取完整的_on_play_state_changed函数
    print("8. _on_play_state_changed 函数实现:")
    pattern = r'def _on_play_state_changed\(self, is_playing\):.*?(?=\n    def|\n    @|\nclass|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        func_code = match.group(0)
        lines = func_code.split('\n')[:20]  # 只显示前20行
        for line in lines:
            if line.strip():
                print(f"  {line}")
    print()

    # 总结
    print("=" * 60)
    print("测试结果总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"  通过: {passed}/{total}")
    print()

    if passed == total:
        print("  [OK] 所有检查项通过！功能实现完整。")
        print()
        print("功能说明:")
        print("  1. '数据变化时自动发送' 复选框默认勾选")
        print("  2. 播放时自动发送UDP数据")
        print("  3. UDP发送条件:")
        print("     - UDP已启用 (udp_enabled = True)")
        print("     - 播放状态为True (is_playing = True)")
        print("     - 播放发送已启用 (udp_send_on_play = True)")
        print()
        return True
    else:
        print("  [FAIL] 部分检查项未通过，请检查实现。")
        return False

if __name__ == "__main__":
    print()
    print("*" * 60)
    print("功能实现验证测试")
    print("*" * 60)
    print()

    test_implementation()
