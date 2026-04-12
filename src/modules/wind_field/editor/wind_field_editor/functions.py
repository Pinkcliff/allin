# -*- coding: utf-8 -*-
"""
风场编辑 - 函数模板模块

提供12种数学函数模板用于风场生成

创建时间: 2024-01-03
作者: Wind Field Editor Team
版本: 1.0.0

修改历史:
    2024-01-03 [v1.0.0] 初始版本
        - 从fan_con项目移植12种函数模板
        - 实现高斯、径向波、渐变等函数
        - 添加函数参数验证

依赖:
    - numpy >= 1.19.0
"""

import numpy as np
from typing import Tuple, Optional, Callable
from dataclasses import dataclass


@dataclass
class FunctionParams:
    """函数参数基类"""
    center: Tuple[float, float] = (20.0, 20.0)  # 函数中心 (行, 列) - 默认在第20行第20列风扇
    amplitude: float = 100.0                      # 幅度
    time: float = 0.0                              # 时间参数


class WindFieldFunction:
    """风场函数基类"""

    @staticmethod
    def validate_grid(grid_data: np.ndarray) -> None:
        """验证网格数据"""
        if grid_data.ndim != 2:
            raise ValueError("网格数据必须是2维数组")
        if grid_data.shape[0] != grid_data.shape[1]:
            raise ValueError("网格必须是正方形")

    @staticmethod
    def normalize(value: np.ndarray, min_val: float = 0.0,
                  max_val: float = 100.0) -> np.ndarray:
        """归一化到指定范围"""
        return np.clip(value, min_val, max_val)


# ==================== 基础波形函数 ====================

class SimpleWaveFunction(WindFieldFunction):
    """简单波动函数

    公式: z = sin(x) * cos(y + t)
    适用场景: 基础波浪分布
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用简单波动"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        # 归一化坐标到 [-5, 5]
        x = np.linspace(-5, 5, cols)
        y = np.linspace(-5, 5, rows)
        X, Y = np.meshgrid(x, y)  # 使用默认的indexing='xy'

        # 计算波浪
        Z = np.sin(X) * np.cos(Y + time)

        # 归一化到 [0, 100] 并应用幅度
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class RadialWaveFunction(WindFieldFunction):
    """径向波动函数

    公式: z = sin(r - t) * exp(-0.1 * r)
    适用场景: 从中心向外扩散的波浪
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0,
              decay: float = 0.1) -> np.ndarray:
        """应用径向波动

        坐标系统：
        - 函数中心在(20.5, 20.5)，对应风扇(20,20),(20,21),(21,20),(21,21)的中心
        - 每个风扇的坐标：x = col - 20 + 0.5, y = row - 20 + 0.5
        """
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        row_center, col_center = self.params.center

        # 创建坐标网格
        x = np.arange(cols) - 20 + 0.5  # 列坐标
        y = np.arange(rows) - 20 + 0.5  # 行坐标
        X, Y = np.meshgrid(x, y)

        # 如果中心不是(20,20)，需要调整偏移
        offset_col = 20 - col_center
        offset_row = 20 - row_center
        X = X + offset_col
        Y = Y + offset_row

        # 计算到中心的距离
        R = np.sqrt(X ** 2 + Y ** 2)

        # 归一化距离
        R_norm = R / np.max(R) * 5

        # 计算径向波
        Z = np.sin(R_norm - time) * np.exp(-decay * R_norm)

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


# ==================== 高斯函数 ====================

class GaussianFunction(WindFieldFunction):
    """高斯函数

    公式: z = A * exp(-(r²) / (2σ²))
    适用场景: 中心高斯分布
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.sigma = 5.0  # 标准差

    def set_sigma(self, sigma: float) -> None:
        """设置标准差"""
        self.sigma = max(0.1, sigma)

    def apply(self, grid_data: np.ndarray, sigma: Optional[float] = None,
              time: float = 0.0) -> np.ndarray:
        """应用高斯分布

        坐标系统：
        - 每个风扇使用其整数坐标(row, col)进行计算
        - 函数中心在(20, 20)时，周围4个风扇(20,20),(20,21),(21,20),(21,21)对称
        """
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        if sigma is not None:
            self.set_sigma(sigma)

        row_center, col_center = self.params.center

        # 创建坐标网格，每个风扇使用其整数坐标
        x = np.arange(cols)  # 列坐标：0, 1, 2, ..., 39
        y = np.arange(rows)  # 行坐标：0, 1, 2, ..., 39
        X, Y = np.meshgrid(x, y)

        # 计算到中心的距离平方
        dist_sq = (X - col_center) ** 2 + (Y - row_center) ** 2

        # 高斯函数
        Z = self.params.amplitude * np.exp(-dist_sq / (2 * self.sigma ** 2))

        # 添加时间动态：中心移动
        if time > 0:
            offset_x = 3 * np.cos(time * 0.5)  # 列方向偏移
            offset_y = 3 * np.sin(time * 0.5)  # 行方向偏移
            dist_sq = (X - col_center - offset_x) ** 2 + (Y - row_center - offset_y) ** 2
            Z = self.params.amplitude * np.exp(-dist_sq / (2 * self.sigma ** 2))

        return self.normalize(Z)


class GaussianWavePacketFunction(WindFieldFunction):
    """高斯波包函数

    公式: z = exp(-((x-x0)² + (y-y0)²) / (2σ²)) * sin(kx*x + ky*y + ωt)
    适用场景: 移动的高斯波包
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.sigma = 2.0
        self.k_x = 2.0  # x方向波数
        self.k_y = 2.0  # y方向波数
        self.omega = 1.0  # 角频率

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用高斯波包

        坐标系统：
        - 函数中心在(20.5, 20.5)，对应风扇(20,20),(20,21),(21,20),(21,21)的中心
        - 每个风扇的坐标：x = col - 20 + 0.5, y = row - 20 + 0.5
        """
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        row_center, col_center = self.params.center

        # 波包中心随时间移动（在新的坐标系统中）
        x0 = 5 * np.cos(time * 0.3)  # 相对于中心的x偏移
        y0 = 5 * np.sin(time * 0.3)  # 相对于中心的y偏移

        # 创建坐标网格
        x = np.arange(cols) - 20 + 0.5  # 列坐标
        y = np.arange(rows) - 20 + 0.5  # 行坐标
        X, Y = np.meshgrid(x, y)

        # 如果中心不是(20,20)，需要调整偏移
        offset_col = 20 - col_center
        offset_row = 20 - row_center
        X = X + offset_col
        Y = Y + offset_row

        # 高斯包络
        envelope = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * self.sigma ** 2))

        # 载波
        carrier = np.sin(self.k_x * X + self.k_y * Y + self.omega * time)

        Z = self.params.amplitude * envelope * carrier

        # 归一化到 [0, 100]
        Z = (Z + self.params.amplitude) / (2 * self.params.amplitude) * 100

        return self.normalize(Z)


# ==================== 渐变函数 ====================

class LinearGradientFunction(WindFieldFunction):
    """线性渐变函数

    公式: z = 0.5 * (x + y) * sin(t)
    适用场景: 对角线方向渐变
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.direction = 'diagonal'  # 'x', 'y', 'diagonal'

    def set_direction(self, direction: str) -> None:
        """设置渐变方向"""
        if direction not in ['x', 'y', 'diagonal']:
            raise ValueError("方向必须是 'x', 'y', 或 'diagonal'")
        self.direction = direction

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用线性渐变"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-1, 1, cols)
        y = np.linspace(-1, 1, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        if self.direction == 'x':
            Z = X * np.sin(time) if time > 0 else X
        elif self.direction == 'y':
            Z = Y * np.sin(time) if time > 0 else Y
        else:  # diagonal
            Z = 0.5 * (X + Y) * np.sin(time) if time > 0 else 0.5 * (X + Y)

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class RadialGradientFunction(WindFieldFunction):
    """径向渐变函数

    公式: z = (r / 5) * cos(t + r)
    适用场景: 同心圆渐变
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0,
              num_bands: int = 3) -> np.ndarray:
        """应用径向渐变"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 计算到中心的距离
        R = np.sqrt((X - cc) ** 2 + (Y - cr) ** 2)

        # 归一化距离
        max_r = np.sqrt(cr ** 2 + cc ** 2)
        r_norm = R / (max_r + 1) * 5

        # 径向渐变
        Z = (r_norm / 5) * np.cos(time + r_norm) if time > 0 else r_norm / 5

        # 添加同心圆条纹
        if num_bands > 0:
            Z = (np.sin(2 * np.pi * num_bands * r_norm / 5 - time) + 1) / 2

        # 归一化到 [0, 100]
        Z = Z * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class CircularGradientFunction(WindFieldFunction):
    """圆形渐变函数

    公式: z = clip((r - r_inner) / (r_outer - r_inner), 0, 1)
    适用场景: 从中心向外扩散的圆形渐变
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.inner_radius = 0.0
        self.outer_radius = 10.0

    def set_radii(self, inner: float, outer: float) -> None:
        """设置内外半径"""
        self.inner_radius = max(0, inner)
        self.outer_radius = max(inner + 0.1, outer)

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用圆形渐变"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 计算到中心的距离
        R = np.sqrt((X - cc) ** 2 + (Y - cr) ** 2)

        # 扩展的外圆半径
        current_outer = self.outer_radius + time * 2 if time > 0 else self.outer_radius

        # 圆形渐变
        Z = np.clip((R - self.inner_radius) / (current_outer - self.inner_radius), 0, 1)

        # 归一化到 [0, 100]
        Z = Z * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


# ==================== 复杂波形函数 ====================

class SpiralWaveFunction(WindFieldFunction):
    """螺旋波函数

    公式: z = sin(n*θ + r - t) * exp(-0.1*r)
    适用场景: 多臂螺旋波
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.arms = 3  # 螺旋臂数量
        self.decay = 0.05

    def set_arms(self, arms: int) -> None:
        """设置螺旋臂数量"""
        self.arms = max(1, min(10, arms))

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用螺旋波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 转换到极坐标
        R = np.sqrt((X - cc) ** 2 + (Y - cr) ** 2)
        Theta = np.arctan2(Y - cr, X - cc)

        # 归一化
        max_r = np.sqrt(cr ** 2 + cc ** 2)
        r_norm = R / (max_r + 1)

        # 螺旋波
        Z = np.sin(self.arms * Theta + r_norm - 2 * np.pi * time) * np.exp(-self.decay * r_norm)

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class InterferencePatternFunction(WindFieldFunction):
    """干涉图样函数

    公式: z = sin(r1 - t) + sin(r2 - t)
    适用场景: 双波源干涉
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        # 两个波源的位置（相对于中心的偏移）
        self.source1_offset = (-5, 0)
        self.source2_offset = (5, 0)

    def set_sources(self, offset1: Tuple[float, float],
                    offset2: Tuple[float, float]) -> None:
        """设置两个波源的位置"""
        self.source1_offset = offset1
        self.source2_offset = offset2

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用干涉图样"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 第一个波源
        s1x, s1y = self.source1_offset
        R1 = np.sqrt((X - cc - s1x) ** 2 + (Y - cr - s1y) ** 2)

        # 第二个波源
        s2x, s2y = self.source2_offset
        R2 = np.sqrt((X - cc - s2x) ** 2 + (Y - cr - s2y) ** 2)

        # 归一化距离
        max_r = np.sqrt(cr ** 2 + cc ** 2)
        R1_norm = R1 / max_r * 5
        R2_norm = R2 / max_r * 5

        # 干涉
        Z1 = np.sin(R1_norm - time)
        Z2 = np.sin(R2_norm - time)
        Z = (Z1 + Z2) / 2

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class StandingWaveFunction(WindFieldFunction):
    """驻波函数

    公式: z = sin(x) * sin(y) * cos(t)
    适用场景: 二维驻波
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用驻波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        # 归一化坐标到 [-π, π]
        x = np.linspace(-np.pi, np.pi, cols)
        y = np.linspace(-np.pi, np.pi, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 驻波
        Z = np.sin(X) * np.sin(Y) * np.cos(time)

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


# ==================== 其他函数 ====================

class CheckerboardFunction(WindFieldFunction):
    """棋盘格函数

    公式: z = sin(x*size + t) * sin(y*size + t)
    适用场景: 周期性网格图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.size = 2.0  # 格子大小

    def set_size(self, size: float) -> None:
        """设置格子大小"""
        self.size = max(0.5, size)

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用棋盘格"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        # 归一化坐标
        x = np.linspace(-2 * np.pi, 2 * np.pi, cols)
        y = np.linspace(-2 * np.pi, 2 * np.pi, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 棋盘格
        Z = np.sin(X * self.size + time) * np.sin(Y * self.size + time)

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class NoiseFieldFunction(WindFieldFunction):
    """噪声场函数

    使用简化的Perlin噪声模拟
    适用场景: 添加随机扰动
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.scale = 0.5
        self.octaves = 3

    def set_scale(self, scale: float) -> None:
        """设置噪声尺度"""
        self.scale = max(0.1, min(2.0, scale))

    def apply(self, grid_data: np.ndarray, time: float = 0.0,
              seed: Optional[int] = None) -> np.ndarray:
        """应用噪声场"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        if seed is not None:
            np.random.seed(seed)
        else:
            np.random.seed(int(time * 100) if time > 0 else 42)

        x = np.linspace(-5, 5, cols)
        y = np.linspace(-5, 5, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 简化的噪声函数（多层正弦叠加）
        Z = np.zeros_like(X)
        for i in range(self.octaves):
            freq = self.scale * (2 ** i)
            amplitude = 1.0 / (2 ** i)
            phase = time * (i + 1) * 0.5 if time > 0 else 0
            Z += amplitude * np.sin(freq * X + phase) * np.cos(freq * Y)

        # 添加随机噪声
        noise = np.random.randn(*X.shape) * 0.1
        Z += noise

        # 归一化到 [0, 100]
        Z_min, Z_max = Z.min(), Z.max()
        if Z_max > Z_min:
            Z = (Z - Z_min) / (Z_max - Z_min) * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class PolynomialSurfaceFunction(WindFieldFunction):
    """多项式曲面函数

    公式: z = (x³ - 3xy²) / 10 (猴鞍面)
    适用场景: 数学曲面
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.order = 3  # 多项式阶数

    def set_order(self, order: int) -> None:
        """设置多项式阶数"""
        self.order = max(1, min(3, order))

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用多项式曲面"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        # 归一化坐标到 [-2, 2]
        x = np.linspace(-2, 2, cols)
        y = np.linspace(-2, 2, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        if self.order == 1:
            # 线性函数
            Z = 0.5 * (X + Y) * np.cos(time) if time > 0 else 0.5 * (X + Y)
        elif self.order == 2:
            # 二次函数（抛物面）
            R2 = X ** 2 + Y ** 2
            Z = (R2 / 8 - 1) * np.sin(time) if time > 0 else (R2 / 8 - 1)
        else:
            # 三次函数（猴鞍面）
            Z = (X ** 3 - 3 * X * Y ** 2) / 10 * np.sin(time) if time > 0 else (X ** 3 - 3 * X * Y ** 2) / 10

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


class SaddlePointFunction(WindFieldFunction):
    """鞍点函数

    公式: z = (x² - y²) / 5
    适用场景: 鞍形点分布
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用鞍点分布"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        # 归一化坐标到 [-3, 3]
        x = np.linspace(-3, 3, cols)
        y = np.linspace(-3, 3, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 鞍点
        Z = (X ** 2 - Y ** 2) / 5 * np.cos(time) if time > 0 else (X ** 2 - Y ** 2) / 5

        # 归一化到 [0, 100]
        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)

        return self.normalize(Z)


# ==================== 新增函数 ====================

class HyperbolicParaboloidFunction(WindFieldFunction):
    """双曲抛物面函数（马鞍面）

    公式: z = (x² - y²) / 4
    适用场景: 经典马鞍面
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用双曲抛物面"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-3, 3, cols)
        y = np.linspace(-3, 3, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = (X ** 2 - Y ** 2) / 4 * np.cos(time * 0.5) if time > 0 else (X ** 2 - Y ** 2) / 4

        Z = (Z + 2) / 4 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class EllipticParaboloidFunction(WindFieldFunction):
    """椭圆抛物面函数

    公式: z = (x² + y²) / 8
    适用场景: 抛物碗
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用椭圆抛物面"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-4, 4, cols)
        y = np.linspace(-4, 4, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = (X ** 2 + Y ** 2) / 8 * np.sin(time * 0.3) if time > 0 else (X ** 2 + Y ** 2) / 8

        Z = Z * 20 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class RippleFunction(WindFieldFunction):
    """涟漪函数

    公式: z = sin(r * frequency - time) / (r + 1)
    适用场景: 水波涟漪
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.frequency = 3.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用涟漪效果"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt((X - cc) ** 2 + (Y - cr) ** 2)

        Z = np.sin(R * 0.5 - time * 2) / (R * 0.2 + 1)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class RoseCurveFunction(WindFieldFunction):
    """玫瑰曲线函数

    公式: z = cos(k * θ) * exp(-r²/20)
    适用场景: 玫瑰花瓣图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.petals = 5  # 花瓣数

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用玫瑰曲线"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols)
        y = np.arange(rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt((X - cc) ** 2 + (Y - cr) ** 2)
        Theta = np.arctan2(Y - cr, X - cc)

        Z = np.cos(self.petals * Theta + time) * np.exp(-R * R / 200)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class LissajousFunction(WindFieldFunction):
    """利萨如图形函数

    公式: z = sin(a*x + t) * sin(b*y + t)
    适用场景: 利萨如图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.a = 3  # x方向频率
        self.b = 2  # y方向频率

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用利萨如图形"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-np.pi, np.pi, cols)
        y = np.linspace(-np.pi, np.pi, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.sin(self.a * X + time) * np.sin(self.b * Y + time * 0.7)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class HeartShapeFunction(WindFieldFunction):
    """心形线函数

    公式: (x² + y² - 1)³ - x²*y³ = 0
    适用场景: 心形图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用心形图案"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 缩放坐标
        scale = 0.15
        X = X * scale
        Y = Y * scale

        # 心形方程
        a = X ** 2 + Y ** 2 - 1
        Z = -(a ** 3 - X ** 2 * Y ** 3) * 5

        if time > 0:
            pulse = 1 + 0.2 * np.sin(time * 2)
            Z = Z * pulse

        Z = np.clip(Z, -50, 50)
        Z = (Z + 50) * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class ButterflyCurveFunction(WindFieldFunction):
    """蝴蝶曲线函数

    公式: r = exp(cos(θ)) - 2*cos(4θ) + sin(θ/12)⁵
    适用场景: 蝴蝶图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用蝴蝶曲线"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        scale = 0.1
        X = X * scale
        Y = Y * scale

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        # 蝴蝶曲线
        r = np.exp(np.cos(Theta + time * 0.2)) - 2 * np.cos(4 * Theta + time) + np.sin((Theta + time) / 12) ** 5
        Z = r * 10 * np.exp(-R)

        Z = (Z + 20) / 40 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class ArchimedeanSpiralFunction(WindFieldFunction):
    """阿基米德螺旋线函数

    公式: r = a + b*θ
    适用场景: 螺旋图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.a = 0.5
        self.b = 0.3

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用阿基米德螺旋"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        # 阿基米德螺旋线
        spiral_r = self.a + self.b * (Theta + time)
        Z = np.cos(10 * (R - spiral_r)) * np.exp(-R * 0.1)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class TorusFunction(WindFieldFunction):
    """环面函数

    公式: z = (R - sqrt(x² + y²))² + z²
    适用场景: 环形图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.R = 8  # 大半径
        self.r = 3  # 小半径

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用环面图案"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)

        # 环面距离函数
        dist = (R - self.R) ** 2
        Z = np.exp(-dist / (2 * self.r ** 2))

        if time > 0:
            Z = Z * (1 + 0.3 * np.sin(time))

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class SombreroFunction(WindFieldFunction):
    """墨西哥草帽函数

    公式: z = sinc(r) = sin(r)/r
    适用场景: 墨西哥草帽曲面
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用墨西哥草帽"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        R_scaled = R / 3.0

        # sinc函数，避免除零
        with np.errstate(divide='ignore', invalid='ignore'):
            Z = np.where(R_scaled > 0, np.sin(R_scaled) / R_scaled, 1.0)

        if time > 0:
            Z = Z * (1 + 0.2 * np.cos(R_scaled - time))

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class CustomExpressionFunction(WindFieldFunction):
    """自定义表达式函数

    允许用户输入数学表达式来定义曲面
    支持的变量: x, y, t (时间)
    支持的函数: sin, cos, tan, exp, log, sqrt, abs, power等
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.expression = "sin(x) * cos(y + t)"  # 默认表达式
        self._compiled_expr = None

    def set_expression(self, expression: str) -> None:
        """设置数学表达式"""
        # 自动处理 z = 前缀
        expression = expression.strip()
        if expression.lower().startswith('z ='):
            expression = expression[3:].strip()
        elif expression.lower().startswith('z='):
            expression = expression[2:].strip()

        self.expression = expression
        self._compile_expression()

    def _compile_expression(self):
        """编译表达式"""
        try:
            # 创建安全的命名空间
            safe_dict = {
                'x': None, 'y': None, 't': None,
                'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                'exp': np.exp, 'log': np.log, 'log10': np.log10,
                'sqrt': np.sqrt, 'abs': np.abs, 'power': np.power,
                'pi': np.pi, 'e': np.e,
                'arcsin': np.arcsin, 'arccos': np.arccos, 'arctan': np.arctan,
                'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
                'floor': np.floor, 'ceil': np.ceil, 'round': np.round,
            }
            # 编译表达式
            self._compiled_expr = compile(self.expression, '<string>', 'eval')
            self._safe_dict = safe_dict
        except Exception as e:
            raise ValueError(f"表达式编译错误: {e}")

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用自定义表达式"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        if self._compiled_expr is None:
            self._compile_expression()

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 更新命名空间
        self._safe_dict['x'] = X
        self._safe_dict['y'] = Y
        self._safe_dict['t'] = time

        try:
            # 计算表达式
            Z = eval(self._compiled_expr, {'__builtins__': {}}, self._safe_dict)

            # 归一化到 [0, 100]
            Z_min, Z_max = Z.min(), Z.max()
            if Z_max > Z_min:
                Z = (Z - Z_min) / (Z_max - Z_min) * 100 * (self.params.amplitude / 100.0)
            else:
                Z = np.zeros_like(Z)

            return self.normalize(Z)
        except Exception as e:
            print(f"表达式计算错误: {e}")
            return np.zeros_like(grid_data)


# ==================== 物理/流体函数 ====================

class VortexFieldFunction(WindFieldFunction):
    """涡旋场函数

    模拟流体涡旋，中心旋转速度最快，向外衰减
    公式: z = exp(-r/λ) * (1 - exp(-r²/σ²)) * cos(θ + ωt + r/λ)
    适用场景: 龙卷风、漩涡、旋转流场
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.decay_length = 8.0   # 衰减长度
        self.core_radius = 3.0    # 涡核半径
        self.omega = 2.0          # 旋转角速度

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用涡旋场"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        # 涡旋速度剖面（Rankine涡旋简化）
        tangential = (1 - np.exp(-R ** 2 / self.core_radius ** 2)) * np.exp(-R / self.decay_length)
        Z = tangential * np.cos(Theta + self.omega * time + R / self.decay_length)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class TurbulenceFieldFunction(WindFieldFunction):
    """湍流场函数

    多尺度涡旋叠加模拟湍流
    适用场景: 大气湍流、复杂风场
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.num_vortices = 5   # 涡旋数量
        self.base_scale = 5.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用湍流场"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.linspace(-5, 5, cols)
        y = np.linspace(-5, 5, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.zeros_like(X)
        np.random.seed(42)

        for i in range(self.num_vortices):
            scale = self.base_scale / (i + 1)
            vx = np.random.uniform(-3, 3)
            vy = np.random.uniform(-3, 3)
            phase = np.random.uniform(0, 2 * np.pi)

            cx = vx + 0.5 * np.sin(time * 0.3 + phase)
            cy = vy + 0.5 * np.cos(time * 0.3 + phase)

            dx = X - cx
            dy = Y - cy
            r = np.sqrt(dx ** 2 + dy ** 2)
            theta = np.arctan2(dy, dx)

            vortex = (1 - np.exp(-r ** 2 / scale ** 2)) * np.exp(-r / (scale * 2))
            Z += vortex * np.cos(theta + time * (i + 1) * 0.5 + phase) / (i + 1)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class ConvectionCellFunction(WindFieldFunction):
    """对流单体函数

    模拟大气对流单体（Rayleigh-Benard对流）
    适用场景: 热对流、大气环流
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.cell_size = 8.0    # 对流单元大小
        self.strength = 1.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用对流单体"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(0, 4 * np.pi, cols)
        y = np.linspace(0, 4 * np.pi, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        k = 2 * np.pi / self.cell_size
        # 对流单元：上升气流和下沉气流交替
        Z = self.strength * (
            np.sin(k * X + time * 0.3) * np.sin(k * Y + time * 0.2) +
            0.5 * np.cos(2 * k * X - time * 0.1) * np.cos(2 * k * Y + time * 0.15)
        )

        Z = (Z + 1.5) / 3 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class DopplerWaveFunction(WindFieldFunction):
    """多普勒效应波函数

    模拟运动波源产生的多普勒效应
    适用场景: 运动源波场、声学风场
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.source_speed = 1.5  # 波源运动速度
        self.wave_speed = 3.0    # 波传播速度
        self.frequency = 2.0     # 波源频率

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用多普勒效应波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 波源沿x轴运动
        sx = self.source_speed * time
        sy = 0.0

        R = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)

        # 多普勒效应：前方波长压缩，后方波长拉伸
        cos_angle = (X - sx) / (R + 0.01)
        doppler_factor = 1 - (self.source_speed / self.wave_speed) * cos_angle

        Z = np.sin(self.frequency * R * doppler_factor - self.frequency * time) / (R * 0.1 + 1)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 高级波动函数 ====================

class BesselWaveFunction(WindFieldFunction):
    """贝塞尔函数波

    使用贝塞尔函数J0模拟圆对称波动
    适用场景: 圆形波导、振动膜片
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.order = 0       # 贝塞尔函数阶数
        self.frequency = 1.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用贝塞尔函数波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)

        try:
            from scipy.special import jv
            Z = jv(self.order, self.frequency * R - time)
        except ImportError:
            # scipy不可用时使用近似
            Z = np.cos(self.frequency * R - time - np.pi / 4) / np.sqrt(R * 0.3 + 1)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class ChladniPatternFunction(WindFieldFunction):
    """克拉德尼图案函数

    模拟振动板上的沙粒图案（Chladni figures）
    公式: z = cos(nπx) * cos(mπy) ± cos(mπx) * cos(nπy)
    适用场景: 振动模式分析、声学图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.n = 3   # x方向模态数
        self.m = 2   # y方向模态数

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用克拉德尼图案"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-1, 1, cols)
        y = np.linspace(-1, 1, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        n, m = self.n, self.m
        # 经典克拉德尼图案公式
        Z = np.cos(n * np.pi * X) * np.cos(m * np.pi * Y) + \
            np.cos(m * np.pi * X) * np.cos(n * np.pi * Y)

        # 添加时间演化
        if time > 0:
            Z *= np.cos(time * 0.5)

        Z = (Z + 2) / 4 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class SuperharmonicFunction(WindFieldFunction):
    """超谐函数（多频叠加）

    多个不同频率的谐波叠加，产生复杂的干涉图案
    适用场景: 复杂波场模拟、频域分析
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.num_harmonics = 5
        self.base_freq = 0.5

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用超谐函数"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.zeros_like(X)
        for n in range(1, self.num_harmonics + 1):
            freq = self.base_freq * n
            amplitude = 1.0 / n  # 高次谐波振幅递减
            phase_x = n * np.pi / 4
            phase_y = n * np.pi / 6

            Z += amplitude * np.sin(freq * X + phase_x + time * n * 0.3) * \
                 np.cos(freq * Y + phase_y + time * n * 0.2)

        Z = (Z + 2) / 4 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 运动/流场函数 ====================

class RotationFieldFunction(WindFieldFunction):
    """旋转场函数

    整体旋转的风场模式
    适用场景: 旋转风场、旋风
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.rotation_speed = 1.0
        self.num_blades = 4    # 旋转叶片数

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用旋转场"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        # 旋转叶片
        Z = np.cos(self.num_blades * (Theta - self.rotation_speed * time))
        # 径向衰减
        Z *= np.exp(-R / 20)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class ConvergenceFieldFunction(WindFieldFunction):
    """收敛场函数

    从四方向中心汇聚的流场
    适用场景: 气流汇聚、进气口模拟
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.convergence_rate = 1.0
        self.pulse_freq = 0.5

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用收敛场"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        max_r = np.max(R) + 1

        # 从外向内传播的波前
        wave_front = max_r - self.convergence_rate * time * 5
        wave_front = wave_front % (max_r * 2)

        # 高斯波包在波前处
        Z = np.exp(-((R - wave_front) ** 2) / 8)

        # 脉动效果
        Z *= (1 + 0.3 * np.sin(self.pulse_freq * time * 2 * np.pi))

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class JetStreamFunction(WindFieldFunction):
    """急流模式函数

    模拟大气急流的带状强风区域
    适用场景: 高空急流、带状风流
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.jet_width = 5.0      # 急流宽度
        self.jet_position = 0.0   # 急流中心位置
        self.speed = 1.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用急流模式"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 急流沿y方向振荡
        jet_y = self.jet_position + 5 * np.sin(X * 0.1 + time * self.speed * 0.3)

        # 急流中心高斯分布
        Z = np.exp(-((Y - jet_y) ** 2) / (2 * self.jet_width ** 2))

        # 添加波动
        Z *= (1 + 0.2 * np.sin(X * 0.2 - time))

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 脉冲/瞬态函数 ====================

class ExplosionFunction(WindFieldFunction):
    """爆炸扩散函数

    模拟从中心点向外扩散的爆炸波
    适用场景: 爆炸波前、脉冲扩散
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.speed = 3.0         # 扩散速度
        self.decay_rate = 0.5    # 衰减率
        self.ring_width = 3.0    # 波环宽度

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用爆炸扩散"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        front = self.speed * time

        # 扩散的环形波
        Z = np.exp(-((R - front) ** 2) / (2 * self.ring_width ** 2))
        # 衰减
        Z *= np.exp(-self.decay_rate * time)

        # 多层波纹
        if front > 5:
            Z += 0.5 * np.exp(-((R - front * 0.7) ** 2) / (2 * self.ring_width ** 2)) * np.exp(-self.decay_rate * time)
        if front > 10:
            Z += 0.3 * np.exp(-((R - front * 0.4) ** 2) / (2 * self.ring_width ** 2)) * np.exp(-self.decay_rate * time)

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class TravelingPulseFunction(WindFieldFunction):
    """行进脉冲函数

    沿指定方向行进的脉冲波
    适用场景: 定向风脉冲、扫描式送风
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.direction = 0.0     # 行进方向(弧度)
        self.speed = 2.0         # 行进速度
        self.pulse_width = 3.0   # 脉冲宽度

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用行进脉冲"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 沿方向的投影距离
        proj = X * np.cos(self.direction) + Y * np.sin(self.direction)
        center = self.speed * time

        # 高斯脉冲
        Z = np.exp(-((proj - center) ** 2) / (2 * self.pulse_width ** 2))

        # 垂直方向限制宽度
        perp = -X * np.sin(self.direction) + Y * np.cos(self.direction)
        Z *= np.exp(-perp ** 2 / 50)

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 几何图案函数 ====================

class StarPatternFunction(WindFieldFunction):
    """星形图案函数

    多角星形辐射图案
    适用场景: 星形风场分布、装饰图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.num_points = 5      # 星角数量
        self.inner_ratio = 0.4   # 内外半径比

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用星形图案"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        # 星形边界函数
        n = self.num_points
        star_radius = 1 + self.inner_ratio * np.cos(n * (Theta - time * 0.5))

        # 归一化
        Z = np.exp(-((R / 10 - star_radius) ** 2) / 0.5)

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class HexagonalPatternFunction(WindFieldFunction):
    """六边形蜂窝图案函数

    模拟蜂窝状六边形网格
    适用场景: 蜂窝分布、周期性六角图案
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.cell_size = 5.0     # 单元格大小

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用六边形蜂窝图案"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        s = self.cell_size
        x = np.arange(cols, dtype=float)
        y = np.arange(rows, dtype=float)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 六边形网格坐标变换
        q = (2.0 / 3 * X) / s
        r = (-1.0 / 3 * X + np.sqrt(3) / 3 * Y) / s

        # 取小数部分（六边形重复单元）
        fq = q - np.floor(q)
        fr = r - np.floor(r)

        # 六边形距离函数
        Z = np.minimum(np.minimum(np.abs(fq), np.abs(fr)), np.abs(fq + fr - 1))

        # 时间动画
        if time > 0:
            Z = Z * (1 + 0.3 * np.sin(time))

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class StripeWaveFunction(WindFieldFunction):
    """条纹波函数

    可变角度的条纹波图案
    适用场景: 平行条纹风场、栅格扫描
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.angle = 0.0         # 条纹角度(弧度)
        self.wavelength = 5.0    # 波长
        self.speed = 1.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用条纹波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.arange(cols, dtype=float)
        y = np.arange(rows, dtype=float)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 沿条纹方向的投影
        proj = X * np.cos(self.angle) + Y * np.sin(self.angle)

        # 条纹波
        Z = np.sin(2 * np.pi * proj / self.wavelength - self.speed * time)

        # 添加渐变包络
        envelope = np.exp(-((X - cols / 2) ** 2 + (Y - rows / 2) ** 2) / (cols * rows / 2))
        Z = Z * (0.7 + 0.3 * envelope)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 特殊效果函数 ====================

class BreathingFunction(WindFieldFunction):
    """呼吸效果函数

    中心区域周期性膨胀收缩，模拟呼吸节奏
    适用场景: 节律性风场、呼吸式送风
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.breath_period = 4.0   # 呼吸周期(秒)
        self.max_radius = 15.0     # 最大扩散半径

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用呼吸效果"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)

        # 呼吸周期: 吸气(扩张) -> 呼气(收缩)
        breath = 0.5 + 0.5 * np.sin(2 * np.pi * time / self.breath_period)
        current_radius = self.max_radius * breath

        # 平滑的径向分布
        Z = np.exp(-(R ** 2) / (2 * current_radius ** 2))

        # 添加微弱的波动
        Z += 0.1 * np.sin(R * 0.5 - time * 2) * np.exp(-R / 20)
        Z = np.clip(Z, 0, 1)

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class WaveCollisionFunction(WindFieldFunction):
    """波浪碰撞函数

    两组相反方向传播的波发生碰撞
    适用场景: 波浪交汇、对冲风场
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.num_sources = 3      # 碰撞波源数量
        self.frequency = 1.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用波浪碰撞"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.zeros_like(X)

        for i in range(self.num_sources):
            angle = 2 * np.pi * i / self.num_sources
            # 从不同方向来的平面波
            kx = np.cos(angle) * self.frequency
            ky = np.sin(angle) * self.frequency
            Z += np.sin(kx * X + ky * Y - time * 2) / self.num_sources

        # 碰撞区域的增强效果
        collision_area = np.exp(-(X ** 2 + Y ** 2) / 200)
        Z = Z * (1 + 0.5 * collision_area)

        Z = (Z + 1.5) / 3 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class SeismicWaveFunction(WindFieldFunction):
    """地震波扩散函数

    模拟地震波从震源向外扩散，包含P波和S波
    适用场景: 震动传播、脉冲扩散
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.p_wave_speed = 4.0     # P波速度
        self.s_wave_speed = 2.5     # S波速度
        self.decay = 0.3

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用地震波扩散"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)

        # P波（压缩波，速度快）
        p_front = self.p_wave_speed * time
        Z_p = 0.6 * np.exp(-((R - p_front) ** 2) / 8) * np.exp(-self.decay * time)

        # S波（剪切波，速度慢）
        s_front = self.s_wave_speed * time
        Z_s = 0.4 * np.exp(-((R - s_front) ** 2) / 5) * np.exp(-self.decay * time) * \
              np.sin(3 * np.arctan2(Y, X))

        Z = Z_p + Z_s

        # 震中附近残留振动
        Z += 0.2 * np.exp(-R / 5) * np.sin(5 * time) * np.exp(-time * 0.2)

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class FractalNoiseFunction(WindFieldFunction):
    """分形噪声函数

    多层八度噪声叠加模拟自然分形
    适用场景: 自然风场模拟、地形噪声
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.octaves = 5          # 噪声层数
        self.persistence = 0.5    # 持续度(每层振幅比)
        self.lacunarity = 2.0     # 空隙度(每层频率倍数)

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用分形噪声"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-5, 5, cols)
        y = np.linspace(-5, 5, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.zeros_like(X)
        amplitude = 1.0
        frequency = 0.3
        phase_seed = 0.0

        for i in range(self.octaves):
            # 使用不同频率和相位的正弦波模拟噪声
            phase_x = phase_seed + i * 1.7
            phase_y = phase_seed + i * 2.3
            Z += amplitude * (
                np.sin(frequency * X + phase_x + time * (0.1 + i * 0.05)) *
                np.cos(frequency * Y + phase_y + time * (0.08 + i * 0.03)) +
                0.5 * np.sin(frequency * 1.7 * X + phase_y + time * 0.15) *
                np.cos(frequency * 1.3 * Y + phase_x + time * 0.12)
            )

            amplitude *= self.persistence
            frequency *= self.lacunarity
            phase_seed += 3.14

        Z_min, Z_max = Z.min(), Z.max()
        if Z_max > Z_min:
            Z = (Z - Z_min) / (Z_max - Z_min) * 100 * (self.params.amplitude / 100.0)
        else:
            Z = np.zeros_like(Z)

        return self.normalize(Z)


class DiamondGridFunction(WindFieldFunction):
    """钻石网格函数

    45度旋转的菱形网格图案
    适用场景: 菱形风场分布、旋转网格
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.grid_size = 6.0      # 网格尺寸
        self.speed = 0.5

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用钻石网格"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.arange(cols, dtype=float)
        y = np.arange(rows, dtype=float)
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 45度旋转
        U = (X + Y) / np.sqrt(2)
        V = (X - Y) / np.sqrt(2)

        s = self.grid_size
        # 菱形距离函数
        du = np.abs(np.mod(U + time * self.speed, s) - s / 2)
        dv = np.abs(np.mod(V + time * self.speed * 0.7, s) - s / 2)

        Z = np.maximum(du, dv) / (s / 2)

        # 反转：网格线为高值
        Z = 1 - Z

        Z = Z * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class SolitaryWaveFunction(WindFieldFunction):
    """孤波函数（KdV方程解）

    模拟KdV方程的孤波解
    公式: z = A * sech²(k * (x - ct))
    适用场景: 孤波传播、非线性波
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.amplitude_soliton = 2.0
        self.speed = 2.0

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用孤波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 孤波参数
        A = self.amplitude_soliton
        k = np.sqrt(A / 12)
        c = self.speed

        # 主孤波（沿x方向传播）
        sech_main = 1.0 / np.cosh(k * (X - c * time))
        Z = A * sech_main ** 2 * np.exp(-Y ** 2 / 100)

        # 第二个较小的孤波（沿45度方向）
        k2 = np.sqrt(A * 0.5 / 12)
        proj2 = (X + Y) / np.sqrt(2)
        sech2 = 1.0 / np.cosh(k2 * (proj2 - c * 0.7 * time))
        Z += A * 0.5 * sech2 ** 2 * np.exp(-((-X + Y) / np.sqrt(2)) ** 2 / 80)

        Z = Z / (A * 1.5) * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class CrossWaveFunction(WindFieldFunction):
    """交叉波函数

    两个正交方向的波叠加形成十字交叉图案
    适用场景: 十字风场、正交波叠加
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.frequency = 0.5
        self.blend = 0.5     # 两个波的混合比例

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用交叉波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # x方向波
        Zx = np.exp(-Y ** 2 / 50) * np.sin(self.frequency * X - time * 2)
        # y方向波
        Zy = np.exp(-X ** 2 / 50) * np.sin(self.frequency * Y - time * 2)

        # 混合
        Z = (1 - self.blend) * Zx + self.blend * Zy

        # 交叉区域增强
        cross = np.exp(-(X ** 2 + Y ** 2) / 100)
        Z = Z * (1 + 0.5 * cross)

        Z = (Z + 1.5) / 3 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class SchrodingerWaveFunction(WindFieldFunction):
    """薛定谔波函数

    模拟量子力学中的波函数概率密度分布
    适用场景: 量子类比、波包演化
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.sigma = 3.0        # 波包宽度
        self.k = 1.5            # 波数

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用薛定谔波函数"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        # 波包色散
        sigma_t = self.sigma * np.sqrt(1 + (time * 0.1) ** 2)

        # 高斯包络
        envelope = np.exp(-(X ** 2 + Y ** 2) / (2 * sigma_t ** 2))

        # 概率密度 = |ψ|² = 波函数的模平方
        psi_real = envelope * np.cos(self.k * X + self.k * Y - time)
        psi_imag = envelope * np.sin(self.k * X + self.k * Y - time)
        Z = psi_real ** 2 + psi_imag ** 2

        Z = Z / Z.max() * 100 * (self.params.amplitude / 100.0) if Z.max() > 0 else Z
        return self.normalize(Z)


class TidalWaveFunction(WindFieldFunction):
    """潮汐波函数

    模拟潮汐的周期性涨落
    适用场景: 潮汐风场、周期性大幅变化
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.tidal_period = 8.0   # 潮汐周期
        self.num_components = 3   # 潮汐分量数

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用潮汐波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        cr, cc = self.params.center
        x = np.arange(cols) - cc
        y = np.arange(rows) - cr
        X, Y = np.meshgrid(x, y, indexing='xy')

        R = np.sqrt(X ** 2 + Y ** 2)
        Theta = np.arctan2(Y, X)

        Z = np.zeros_like(X)
        # M2 分潮（主要太阴半日潮）
        Z += 0.6 * np.cos(2 * Theta - 2 * np.pi * time / self.tidal_period) * np.exp(-R / 30)
        # S2 分潮（主要太阳半日潮）
        Z += 0.3 * np.cos(2 * Theta - 2 * np.pi * time / (self.tidal_period * 1.07)) * np.exp(-R / 25)
        # K1 分潮（日月合成日潮）
        Z += 0.2 * np.cos(Theta - 2 * np.pi * time / (self.tidal_period * 2)) * np.exp(-R / 35)

        Z = (Z + 1.1) / 2.2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


class PlasmaWaveFunction(WindFieldFunction):
    """等离子体波函数

    模拟等离子体波的复杂干涉图案
    适用场景: 等离子风场、科幻效果
    """

    def __init__(self, params: Optional[FunctionParams] = None):
        self.params = params or FunctionParams()
        self.num_modes = 4

    def apply(self, grid_data: np.ndarray, time: float = 0.0) -> np.ndarray:
        """应用等离子体波"""
        self.validate_grid(grid_data)
        rows, cols = grid_data.shape

        x = np.linspace(-np.pi, np.pi, cols)
        y = np.linspace(-np.pi, np.pi, rows)
        X, Y = np.meshgrid(x, y, indexing='xy')

        Z = np.zeros_like(X)
        for i in range(self.num_modes):
            k = i + 1
            phase = i * np.pi / 3
            Z += np.sin(k * X + phase + time * (0.5 + i * 0.1)) * \
                 np.cos(k * Y + phase + time * (0.3 + i * 0.15))

        # 非线性变换产生等离子效果
        Z = np.sin(Z * 2 + time) * 0.5 + np.cos(Z * 1.5 - time * 0.7) * 0.5

        Z = (Z + 1) / 2 * 100 * (self.params.amplitude / 100.0)
        return self.normalize(Z)


# ==================== 函数工厂 ====================

class WindFieldFunctionFactory:
    """风场函数工厂

    提供25种预定义函数模板的统一访问接口
    """

    # 函数类型映射
    FUNCTIONS = {
        'simple_wave': SimpleWaveFunction,
        'radial_wave': RadialWaveFunction,
        'gaussian': GaussianFunction,
        'gaussian_packet': GaussianWavePacketFunction,
        'standing_wave': StandingWaveFunction,
        'linear_gradient': LinearGradientFunction,
        'radial_gradient': RadialGradientFunction,
        'circular_gradient': CircularGradientFunction,
        'spiral_wave': SpiralWaveFunction,
        'interference': InterferencePatternFunction,
        'checkerboard': CheckerboardFunction,
        'noise_field': NoiseFieldFunction,
        'polynomial_surface': PolynomialSurfaceFunction,
        'saddle_point': SaddlePointFunction,
        # 数学曲面
        'hyperbolic_paraboloid': HyperbolicParaboloidFunction,
        'elliptic_paraboloid': EllipticParaboloidFunction,
        'ripple': RippleFunction,
        'rose_curve': RoseCurveFunction,
        'lissajous': LissajousFunction,
        'heart_shape': HeartShapeFunction,
        'butterfly_curve': ButterflyCurveFunction,
        'archimedean_spiral': ArchimedeanSpiralFunction,
        'torus': TorusFunction,
        'sombrero': SombreroFunction,
        'custom_expression': CustomExpressionFunction,
        # 物理/流体
        'vortex_field': VortexFieldFunction,
        'turbulence_field': TurbulenceFieldFunction,
        'convection_cell': ConvectionCellFunction,
        'doppler_wave': DopplerWaveFunction,
        # 高级波
        'bessel_wave': BesselWaveFunction,
        'chladni_pattern': ChladniPatternFunction,
        'superharmonic': SuperharmonicFunction,
        # 运动/流场
        'rotation_field': RotationFieldFunction,
        'convergence_field': ConvergenceFieldFunction,
        'jet_stream': JetStreamFunction,
        # 脉冲/瞬态
        'explosion': ExplosionFunction,
        'traveling_pulse': TravelingPulseFunction,
        # 几何图案
        'star_pattern': StarPatternFunction,
        'hexagonal_pattern': HexagonalPatternFunction,
        'stripe_wave': StripeWaveFunction,
        'diamond_grid': DiamondGridFunction,
        # 特殊效果
        'breathing': BreathingFunction,
        'wave_collision': WaveCollisionFunction,
        'seismic_wave': SeismicWaveFunction,
        'fractal_noise': FractalNoiseFunction,
        'solitary_wave': SolitaryWaveFunction,
        'cross_wave': CrossWaveFunction,
        'schrodinger_wave': SchrodingerWaveFunction,
        'tidal_wave': TidalWaveFunction,
        'plasma_wave': PlasmaWaveFunction,
    }

    # 函数分类
    CATEGORIES = {
        '基础波形': ['simple_wave', 'radial_wave', 'standing_wave', 'ripple'],
        '高斯函数': ['gaussian', 'gaussian_packet'],
        '渐变图案': ['linear_gradient', 'circular_gradient', 'radial_gradient'],
        '复杂波场': ['spiral_wave', 'interference', 'checkerboard', 'noise_field', 'lissajous'],
        '数学曲面': ['polynomial_surface', 'saddle_point', 'hyperbolic_paraboloid',
                     'elliptic_paraboloid', 'sombrero', 'torus'],
        '特殊曲线': ['rose_curve', 'heart_shape', 'butterfly_curve', 'archimedean_spiral'],
        '物理流体': ['vortex_field', 'turbulence_field', 'convection_cell', 'doppler_wave'],
        '高级波动': ['bessel_wave', 'chladni_pattern', 'superharmonic', 'solitary_wave'],
        '运动流场': ['rotation_field', 'convergence_field', 'jet_stream'],
        '脉冲瞬态': ['explosion', 'traveling_pulse', 'seismic_wave'],
        '几何图案': ['star_pattern', 'hexagonal_pattern', 'stripe_wave', 'diamond_grid'],
        '特殊效果': ['breathing', 'wave_collision', 'cross_wave', 'fractal_noise',
                     'schrodinger_wave', 'tidal_wave', 'plasma_wave'],
        '自定义': ['custom_expression'],
    }

    # 函数描述
    DESCRIPTIONS = {
        'simple_wave': '简单波动 - sin(x) * cos(y + t)',
        'radial_wave': '径向波 - 从中心向外扩散',
        'gaussian': '高斯分布 - 中心集中衰减',
        'gaussian_packet': '高斯波包 - 移动的波包',
        'standing_wave': '驻波 - 二维驻波振动',
        'linear_gradient': '线性渐变 - 对角线方向',
        'radial_gradient': '径向渐变 - 同心圆条纹',
        'circular_gradient': '圆形渐变 - 从中心向外扩散',
        'spiral_wave': '螺旋波 - 多臂螺旋图案',
        'interference': '干涉图样 - 双波源干涉',
        'checkerboard': '棋盘格 - 周期性网格',
        'noise_field': '噪声场 - 随机扰动',
        'polynomial_surface': '多项式曲面 - 数学曲面',
        'saddle_point': '鞍点 - 鞍形分布',
        'hyperbolic_paraboloid': '双曲抛物面 - 经典马鞍面',
        'elliptic_paraboloid': '椭圆抛物面 - 抛物碗',
        'ripple': '涟漪 - 水波涟漪效果',
        'rose_curve': '玫瑰曲线 - 花瓣图案',
        'lissajous': '利萨如图形 - 复杂波形',
        'heart_shape': '心形线 - 心形图案',
        'butterfly_curve': '蝴蝶曲线 - 蝴蝶图案',
        'archimedean_spiral': '阿基米德螺旋 - 螺旋图案',
        'torus': '环面 - 环形图案',
        'sombrero': '墨西哥草帽 - sinc曲面',
        'custom_expression': '自定义表达式 - 输入数学公式',
        # 物理/流体
        'vortex_field': '涡旋场 - Rankine涡旋旋转流场',
        'turbulence_field': '湍流场 - 多尺度涡旋叠加',
        'convection_cell': '对流单体 - Rayleigh-Benard对流',
        'doppler_wave': '多普勒波 - 运动波源频移效应',
        # 高级波
        'bessel_wave': '贝塞尔波 - 圆对称波动J0',
        'chladni_pattern': '克拉德尼图案 - 振动板沙粒图案',
        'superharmonic': '超谐函数 - 多频谐波叠加',
        'solitary_wave': '孤波 - KdV方程孤波解',
        # 运动/流场
        'rotation_field': '旋转场 - 整体旋转风场',
        'convergence_field': '收敛场 - 四方向中心汇聚',
        'jet_stream': '急流模式 - 带状强风区域',
        # 脉冲/瞬态
        'explosion': '爆炸扩散 - 中心向外扩散波',
        'traveling_pulse': '行进脉冲 - 定向行进脉冲波',
        'seismic_wave': '地震波 - P波S波复合扩散',
        # 几何图案
        'star_pattern': '星形图案 - 多角星形辐射',
        'hexagonal_pattern': '六边形蜂窝 - 蜂窝网格图案',
        'stripe_wave': '条纹波 - 可变角度平行条纹',
        'diamond_grid': '钻石网格 - 45度菱形网格',
        # 特殊效果
        'breathing': '呼吸效果 - 节律性膨胀收缩',
        'wave_collision': '波浪碰撞 - 多方向波交汇',
        'cross_wave': '交叉波 - 正交方向波叠加',
        'fractal_noise': '分形噪声 - 多层八度噪声',
        'schrodinger_wave': '薛定谔波 - 量子波函数概率密度',
        'tidal_wave': '潮汐波 - 周期性潮汐涨落',
        'plasma_wave': '等离子体波 - 非线性干涉图案',
    }

    @classmethod
    def create(cls, function_type: str, params: Optional[FunctionParams] = None) -> WindFieldFunction:
        """
        创建函数实例

        Args:
            function_type: 函数类型名称
            params: 函数参数

        Returns:
            函数实例

        Raises:
            ValueError: 未知函数类型
        """
        if function_type not in cls.FUNCTIONS:
            raise ValueError(
                f"未知函数类型: {function_type}. "
                f"可用类型: {list(cls.FUNCTIONS.keys())}"
            )

        return cls.FUNCTIONS[function_type](params)

    @classmethod
    def get_available_functions(cls) -> list:
        """获取所有可用函数列表"""
        return list(cls.FUNCTIONS.keys())

    @classmethod
    def get_functions_by_category(cls, category: str) -> list:
        """按分类获取函数列表"""
        return cls.CATEGORIES.get(category, [])

    @classmethod
    def get_all_categories(cls) -> list:
        """获取所有分类"""
        return list(cls.CATEGORIES.keys())

    @classmethod
    def get_description(cls, function_type: str) -> str:
        """获取函数描述"""
        return cls.DESCRIPTIONS.get(function_type, "无描述")


# ==================== 导出接口 ====================

# 导出所有函数类
__all__ = [
    # 原有函数类
    'SimpleWaveFunction',
    'RadialWaveFunction',
    'GaussianFunction',
    'GaussianWavePacketFunction',
    'StandingWaveFunction',
    'LinearGradientFunction',
    'RadialGradientFunction',
    'CircularGradientFunction',
    'SpiralWaveFunction',
    'InterferencePatternFunction',
    'CheckerboardFunction',
    'NoiseFieldFunction',
    'PolynomialSurfaceFunction',
    'SaddlePointFunction',
    # 数学曲面
    'HyperbolicParaboloidFunction',
    'EllipticParaboloidFunction',
    'RippleFunction',
    'RoseCurveFunction',
    'LissajousFunction',
    'HeartShapeFunction',
    'ButterflyCurveFunction',
    'ArchimedeanSpiralFunction',
    'TorusFunction',
    'SombreroFunction',
    'CustomExpressionFunction',
    # 物理/流体
    'VortexFieldFunction',
    'TurbulenceFieldFunction',
    'ConvectionCellFunction',
    'DopplerWaveFunction',
    # 高级波
    'BesselWaveFunction',
    'ChladniPatternFunction',
    'SuperharmonicFunction',
    'SolitaryWaveFunction',
    # 运动/流场
    'RotationFieldFunction',
    'ConvergenceFieldFunction',
    'JetStreamFunction',
    # 脉冲/瞬态
    'ExplosionFunction',
    'TravelingPulseFunction',
    'SeismicWaveFunction',
    # 几何图案
    'StarPatternFunction',
    'HexagonalPatternFunction',
    'StripeWaveFunction',
    'DiamondGridFunction',
    # 特殊效果
    'BreathingFunction',
    'WaveCollisionFunction',
    'CrossWaveFunction',
    'FractalNoiseFunction',
    'SchrodingerWaveFunction',
    'TidalWaveFunction',
    'PlasmaWaveFunction',
    # 工厂类
    'WindFieldFunctionFactory',
    # 参数类
    'FunctionParams',
]


if __name__ == "__main__":
    # 测试代码
    import matplotlib.pyplot as plt

    # 创建测试网格
    grid_data = np.zeros((40, 40))

    # 测试高斯函数
    gaussian = GaussianFunction()
    result = gaussian.apply(grid_data, sigma=5.0)

    # 可视化
    plt.figure(figsize=(10, 8))
    plt.imshow(result.T, cmap='jet', origin='lower', vmin=0, vmax=100)
    plt.colorbar(label='转速 %')
    plt.title('高斯分布示例')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()

    # 打印所有可用函数
    print("可用函数类型:")
    for func_type in WindFieldFunctionFactory.get_available_functions():
        desc = WindFieldFunctionFactory.get_description(func_type)
        print(f"  - {func_type}: {desc}")
