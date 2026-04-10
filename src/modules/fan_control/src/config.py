"""
配置文件
在这里定义您的动态曲面函数
"""

import numpy as np

# 示例函数1：简单波动
def simple_wave(x, y, t):
    """
    简单波动曲面
    z = sin(x + t) * cos(y - t)
    """
    return np.sin(x + t) * np.cos(y - t)

# 示例函数2：径向波动
def radial_wave(x, y, t):
    """
    径向扩散波
    z = sin(√(x² + y²) - 2t) * exp(-0.1t)
    """
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - 2*t) * np.exp(-0.1*t)

# 示例函数3：高斯波包
def gaussian_wave_packet(x, y, t):
    """
    高斯波包在平面上移动
    """
    x0 = 2 * np.cos(0.5 * t)  # 波包中心x坐标
    y0 = 2 * np.sin(0.5 * t)  # 波包中心y坐标
    sigma = 1.0  # 波包宽度
    amplitude = 2.0  # 振幅

    return amplitude * np.exp(-((x - x0)**2 + (y - y0)**2) / (2 * sigma**2))

# 示例函数4：驻波
def standing_wave(x, y, t):
    """
    二维驻波
    """
    return np.sin(x) * np.sin(y) * np.cos(2*t)

# 示例函数5：螺旋波
def spiral_wave(x, y, t):
    """
    螺旋波
    """
    theta = np.arctan2(y, x)
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - 2*theta - 3*t) * np.exp(-0.05*t)

# 示例函数6：干涉波
def interference_pattern(x, y, t):
    """
    两个点源的干涉图样
    """
    r1 = np.sqrt((x-2)**2 + y**2)
    r2 = np.sqrt((x+2)**2 + y**2)
    return np.sin(r1 - 2*t) + np.sin(r2 - 2*t)

# 示例函数7：孤立子
def soliton(x, y, t):
    """
    二维孤立子
    """
    return 3 * np.exp(-np.sqrt((x - t)**2 + y**2)) / np.cosh(np.sqrt((x - t)**2 + y**2))

# 在这里定义您自己的函数
def your_function(x, y, t):
    """
    在这里定义您的动态曲面函数
    x, y, t 可以是标量或numpy数组
    返回 z 值
    """
    # 示例：自定义函数
    # return np.sin(x*t) * np.cos(y*t) * np.exp(-0.1*t)
    pass

# 函数字典，便于选择
SURFACE_FUNCTIONS = {
    'simple_wave': simple_wave,
    'radial_wave': radial_wave,
    'gaussian_packet': gaussian_wave_packet,
    'standing_wave': standing_wave,
    'spiral_wave': spiral_wave,
    'interference': interference_pattern,
    'soliton': soliton,
    'custom': your_function
}

# 默认参数配置
DEFAULT_CONFIG = {
    'x_range': (-5, 5),
    'y_range': (-5, 5),
    't_range': (0, 10),
    'resolution': 50,
    'num_time_points': 100
}