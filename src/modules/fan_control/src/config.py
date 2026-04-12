"""
配置文件
在这里定义您的动态曲面函数
"""

import numpy as np

# ==================== 基础波形 ====================

def simple_wave(x, y, t):
    """简单波动曲面 z = sin(x + t) * cos(y - t)"""
    return np.sin(x + t) * np.cos(y - t)

def radial_wave(x, y, t):
    """径向扩散波 z = sin(r - 2t) * exp(-0.1t)"""
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - 2*t) * np.exp(-0.1*t)

def standing_wave(x, y, t):
    """二维驻波"""
    return np.sin(x) * np.sin(y) * np.cos(2*t)

def spiral_wave(x, y, t):
    """螺旋波"""
    theta = np.arctan2(y, x)
    r = np.sqrt(x**2 + y**2)
    return np.sin(r - 2*theta - 3*t) * np.exp(-0.05*t)

def interference_pattern(x, y, t):
    """两个点源的干涉图样"""
    r1 = np.sqrt((x-2)**2 + y**2)
    r2 = np.sqrt((x+2)**2 + y**2)
    return np.sin(r1 - 2*t) + np.sin(r2 - 2*t)

# ==================== 高斯/脉冲 ====================

def gaussian_wave_packet(x, y, t):
    """高斯波包在平面上移动"""
    x0 = 2 * np.cos(0.5 * t)
    y0 = 2 * np.sin(0.5 * t)
    sigma = 1.0
    amplitude = 2.0
    return amplitude * np.exp(-((x - x0)**2 + (y - y0)**2) / (2 * sigma**2))

def soliton(x, y, t):
    """二维孤立子"""
    return 3 * np.exp(-np.sqrt((x - t)**2 + y**2)) / np.cosh(np.sqrt((x - t)**2 + y**2))

# ==================== 物理/流体 ====================

def vortex_field(x, y, t):
    """涡旋场 - Rankine涡旋"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    core_r = 1.5
    decay = 4.0
    tangential = (1 - np.exp(-r**2 / core_r**2)) * np.exp(-r / decay)
    return tangential * np.cos(theta + 2*t + r / decay)

def turbulence_field(x, y, t):
    """湍流场 - 多尺度涡旋"""
    Z = np.zeros_like(x)
    for i in range(1, 6):
        scale = 5.0 / i
        Z += (1.0/i) * np.sin(x/scale + t*i*0.3) * np.cos(y/scale + t*i*0.2)
    return Z

def convection_cell(x, y, t):
    """对流单体 - Rayleigh-Benard对流"""
    k = 2 * np.pi / 8
    return np.sin(k*x + t*0.3) * np.sin(k*y + t*0.2) + \
           0.5 * np.cos(2*k*x - t*0.1) * np.cos(2*k*y + t*0.15)

def doppler_wave(x, y, t):
    """多普勒效应波"""
    sx = 1.5 * t
    r = np.sqrt((x - sx)**2 + y**2)
    cos_a = (x - sx) / (r + 0.01)
    doppler = 1 - 0.5 * cos_a
    return np.sin(2 * r * doppler - 2*t) / (r * 0.1 + 1)

# ==================== 高级波动 ====================

def bessel_wave(x, y, t):
    """贝塞尔函数波"""
    r = np.sqrt(x**2 + y**2)
    try:
        from scipy.special import jv
        return jv(0, r - t)
    except ImportError:
        return np.cos(r - t - np.pi/4) / np.sqrt(r * 0.3 + 1)

def chladni_pattern(x, y, t):
    """克拉德尼振动图案"""
    return np.cos(3*np.pi*x/5) * np.cos(2*np.pi*y/5) + \
           np.cos(2*np.pi*x/5) * np.cos(3*np.pi*y/5)

def superharmonic(x, y, t):
    """超谐函数 - 多频叠加"""
    Z = np.zeros_like(x)
    for n in range(1, 6):
        freq = 0.5 * n
        Z += (1.0/n) * np.sin(freq*x + n*np.pi/4 + t*n*0.3) * \
             np.cos(freq*y + n*np.pi/6 + t*n*0.2)
    return Z

def solitary_wave(x, y, t):
    """KdV孤波解"""
    A = 2.0
    k = np.sqrt(A / 12)
    sech = 1.0 / np.cosh(k * (x - 2*t))
    return A * sech**2 * np.exp(-y**2 / 100)

# ==================== 运动/流场 ====================

def rotation_field(x, y, t):
    """旋转场"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return np.cos(4 * (theta - t)) * np.exp(-r / 10)

def convergence_field(x, y, t):
    """收敛场 - 向中心汇聚"""
    r = np.sqrt(x**2 + y**2)
    max_r = 10.0
    front = max_r - t * 3
    front = front % (max_r * 2)
    return np.exp(-((r - front)**2) / 8)

def jet_stream(x, y, t):
    """急流模式"""
    jet_y = 5 * np.sin(x * 0.1 + t * 0.3)
    return np.exp(-((y - jet_y)**2) / 50) * (1 + 0.2 * np.sin(x * 0.2 - t))

# ==================== 脉冲/瞬态 ====================

def explosion(x, y, t):
    """爆炸扩散"""
    r = np.sqrt(x**2 + y**2)
    front = 3 * t
    Z = np.exp(-((r - front)**2) / 18) * np.exp(-0.3*t)
    if front > 5:
        Z += 0.5 * np.exp(-((r - front*0.7)**2) / 18) * np.exp(-0.3*t)
    return Z

def traveling_pulse(x, y, t):
    """行进脉冲"""
    proj = x * np.cos(0) + y * np.sin(0)
    perp = -x * np.sin(0) + y * np.cos(0)
    return np.exp(-((proj - 2*t)**2) / 18) * np.exp(-perp**2 / 50)

def seismic_wave(x, y, t):
    """地震波 - P波+S波"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    p = 0.6 * np.exp(-((r - 4*t)**2) / 8) * np.exp(-0.3*t)
    s = 0.4 * np.exp(-((r - 2.5*t)**2) / 5) * np.exp(-0.3*t) * np.sin(3*theta)
    return p + s

# ==================== 几何图案 ====================

def star_pattern(x, y, t):
    """星形图案"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    star_r = 1 + 0.4 * np.cos(5 * (theta - t*0.5))
    return np.exp(-((r/5 - star_r)**2) / 0.5)

def hexagonal_pattern(x, y, t):
    """六边形蜂窝图案"""
    s = 2.0
    q = (2.0/3 * x) / s
    r_h = (-1.0/3 * x + np.sqrt(3)/3 * y) / s
    fq = np.abs(q - np.floor(q))
    fr = np.abs(r_h - np.floor(r_h))
    return np.minimum(np.minimum(fq, fr), np.abs(fq + fr - 1)) * (1 + 0.3*np.sin(t))

def stripe_wave(x, y, t):
    """条纹波"""
    proj = x * np.cos(0) + y * np.sin(0)
    return np.sin(2 * np.pi * proj / 5 - t)

def diamond_grid(x, y, t):
    """钻石网格"""
    s = 3.0
    u = (x + y) / np.sqrt(2)
    v = (x - y) / np.sqrt(2)
    du = np.abs(np.mod(u + t*0.5, s) - s/2)
    dv = np.abs(np.mod(v + t*0.35, s) - s/2)
    return 1 - np.maximum(du, dv) / (s/2)

# ==================== 特殊效果 ====================

def breathing(x, y, t):
    """呼吸效果"""
    r = np.sqrt(x**2 + y**2)
    breath = 0.5 + 0.5 * np.sin(2 * np.pi * t / 4)
    current_r = 7.5 * breath
    return np.exp(-(r**2) / (2 * current_r**2))

def wave_collision(x, y, t):
    """波浪碰撞"""
    Z = np.zeros_like(x)
    for i in range(3):
        angle = 2 * np.pi * i / 3
        kx = np.cos(angle)
        ky = np.sin(angle)
        Z += np.sin(kx*x + ky*y - 2*t) / 3
    collision = np.exp(-(x**2 + y**2) / 100)
    return Z * (1 + 0.5 * collision)

def cross_wave(x, y, t):
    """交叉波"""
    Zx = np.exp(-y**2 / 50) * np.sin(0.5*x - 2*t)
    Zy = np.exp(-x**2 / 50) * np.sin(0.5*y - 2*t)
    return 0.5 * Zx + 0.5 * Zy

def fractal_noise(x, y, t):
    """分形噪声"""
    Z = np.zeros_like(x)
    amplitude = 1.0
    frequency = 0.3
    for i in range(5):
        px = i * 1.7
        py = i * 2.3
        Z += amplitude * (
            np.sin(frequency*x + px + t*(0.1+i*0.05)) * np.cos(frequency*y + py + t*(0.08+i*0.03)) +
            0.5 * np.sin(frequency*1.7*x + py + t*0.15) * np.cos(frequency*1.3*y + px + t*0.12)
        )
        amplitude *= 0.5
        frequency *= 2.0
    return Z

def schrodinger_wave(x, y, t):
    """薛定谔波函数概率密度"""
    sigma_t = 3.0 * np.sqrt(1 + (t*0.1)**2)
    envelope = np.exp(-(x**2 + y**2) / (2 * sigma_t**2))
    psi_r = envelope * np.cos(1.5*x + 1.5*y - t)
    psi_i = envelope * np.sin(1.5*x + 1.5*y - t)
    return psi_r**2 + psi_i**2

def tidal_wave(x, y, t):
    """潮汐波"""
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    Z = 0.6 * np.cos(2*theta - 2*np.pi*t/8) * np.exp(-r/15)
    Z += 0.3 * np.cos(2*theta - 2*np.pi*t/8.56) * np.exp(-r/12.5)
    Z += 0.2 * np.cos(theta - 2*np.pi*t/16) * np.exp(-r/17.5)
    return Z

def plasma_wave(x, y, t):
    """等离子体波"""
    Z = np.zeros_like(x)
    for i in range(4):
        k = i + 1
        phase = i * np.pi / 3
        Z += np.sin(k*x + phase + t*(0.5+i*0.1)) * np.cos(k*y + phase + t*(0.3+i*0.15))
    return np.sin(Z*2 + t) * 0.5 + np.cos(Z*1.5 - t*0.7) * 0.5

# 自定义函数占位
def your_function(x, y, t):
    """自定义函数模板"""
    pass

# 函数字典，便于选择
SURFACE_FUNCTIONS = {
    # 基础波形
    'simple_wave': simple_wave,
    'radial_wave': radial_wave,
    'standing_wave': standing_wave,
    'spiral_wave': spiral_wave,
    'interference': interference_pattern,
    # 高斯/脉冲
    'gaussian_packet': gaussian_wave_packet,
    'soliton': soliton,
    # 物理/流体
    'vortex_field': vortex_field,
    'turbulence_field': turbulence_field,
    'convection_cell': convection_cell,
    'doppler_wave': doppler_wave,
    # 高级波
    'bessel_wave': bessel_wave,
    'chladni_pattern': chladni_pattern,
    'superharmonic': superharmonic,
    'solitary_wave': solitary_wave,
    # 运动/流场
    'rotation_field': rotation_field,
    'convergence_field': convergence_field,
    'jet_stream': jet_stream,
    # 脉冲/瞬态
    'explosion': explosion,
    'traveling_pulse': traveling_pulse,
    'seismic_wave': seismic_wave,
    # 几何图案
    'star_pattern': star_pattern,
    'hexagonal_pattern': hexagonal_pattern,
    'stripe_wave': stripe_wave,
    'diamond_grid': diamond_grid,
    # 特殊效果
    'breathing': breathing,
    'wave_collision': wave_collision,
    'cross_wave': cross_wave,
    'fractal_noise': fractal_noise,
    'schrodinger_wave': schrodinger_wave,
    'tidal_wave': tidal_wave,
    'plasma_wave': plasma_wave,
    # 自定义
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