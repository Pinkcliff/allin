# -*- coding: utf-8 -*-
"""
测试板ID 9 (192.168.1.10) 的风扇数据映射
"""

import numpy as np

# 创建一个测试用的40x40网格，每个风扇都有不同的值
grid_data = np.zeros((40, 40))
for i in range(40):
    for j in range(40):
        grid_data[i, j] = i * 40 + j  # 每个风扇都有唯一的值

# 板ID 9的映射逻辑
global_board_id = 9
row_start = global_board_id // 10 * 4
row_end = row_start + 4
col_start = (global_board_id % 10) * 4
col_end = col_start + 4

print(f"板ID {global_board_id} (192.168.1.10) 的数据:")
print(f"行范围: {row_start}-{row_end-1}")
print(f"列范围: {col_start}-{col_end-1}")
print()

module_data = grid_data[row_start:row_end, col_start:col_end]
print("提取的4x4模块数据:")
print(module_data)
print()

# 构建PWM值列表
pwm_values = []
print("fan_id -> (row, col) -> grid_data值 -> PWM值")
print("-" * 50)
for fan_id in range(16):
    row = fan_id // 4
    col = fan_id % 4
    percent = module_data[row, col]
    pwm_value = int((percent / 100.0) * 999)
    pwm_values.append(pwm_value)
    print(f"fan_id {fan_id:2d} -> ({row},{col}) -> {percent:6.1f}% -> PWM {pwm_value:3d}")

print()
print("发送的16个PWM值:", pwm_values)

# 检查是否有重复值
unique_pwm = set(pwm_values)
if len(unique_pwm) < 16:
    print(f"\n警告: 16个风扇中有 {16 - len(unique_pwm)} 个重复值!")
else:
    print("\n所有16个风扇的PWM值都不同")
