# -*- coding: utf-8 -*-
"""
函数导入辅助模块

统一处理函数模块的导入，支持多个路径
"""

def get_functions_module():
    """
    获取风场函数模块

    尝试从多个可能的路径导入，返回成功导入的模块

    Returns:
        module: 包含WindFieldFunctionFactory的模块
        或 None: 如果所有路径都失败
    """
    import sys
    import os

    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))

    # 确保根目录在sys.path中
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # 可能的模块路径
    module_paths = [
        'wind_field_editor_code.functions',   # 复制的英文路径（优先）
        'wind_field_editor.functions',         # 原来的英文路径
        '风场编辑器.wind_field_editor.functions',  # 中文路径
    ]

    last_error = None
    for module_path in module_paths:
        try:
            parts = module_path.split('.')
            module = __import__(module_path)
            for part in parts[1:]:
                module = getattr(module, part)

            # 验证是否有WindFieldFunctionFactory
            if hasattr(module, 'WindFieldFunctionFactory'):
                print(f"[ImportHelper] 成功从 {module_path} 导入函数模块")
                return module
        except (ImportError, AttributeError) as e:
            last_error = e
            continue

    print(f"[ImportHelper] 警告: 无法从任何路径导入函数模块")
    if last_error:
        print(f"[ImportHelper] 最后的错误: {last_error}")
    return None


def get_function_factory():
    """
    获取WindFieldFunctionFactory类

    Returns:
        WindFieldFunctionFactory类，或None
    """
    module = get_functions_module()
    if module is not None:
        return module.WindFieldFunctionFactory
    return None


def get_function_classes():
    """
    获取所有函数类

    Returns:
        dict: 包含所有函数类的字典
    """
    module = get_functions_module()
    if module is not None:
        return {
            'WindFieldFunctionFactory': module.WindFieldFunctionFactory,
            'WindFieldFunction': module.WindFieldFunction,
            'FunctionParams': module.FunctionParams,
            'SimpleWaveFunction': module.SimpleWaveFunction,
            'RadialWaveFunction': module.RadialWaveFunction,
            'GaussianFunction': module.GaussianFunction,
            'GaussianWavePacketFunction': module.GaussianWavePacketFunction,
            'StandingWaveFunction': module.StandingWaveFunction,
            'LinearGradientFunction': module.LinearGradientFunction,
            'RadialGradientFunction': module.RadialGradientFunction,
            'CircularGradientFunction': module.CircularGradientFunction,
            'SpiralWaveFunction': module.SpiralWaveFunction,
            'InterferencePatternFunction': module.InterferencePatternFunction,
            'CheckerboardFunction': module.CheckerboardFunction,
            'NoiseFieldFunction': module.NoiseFieldFunction,
            'PolynomialSurfaceFunction': module.PolynomialSurfaceFunction,
            'SaddlePointFunction': module.SaddlePointFunction,
            'HyperbolicParaboloidFunction': module.HyperbolicParaboloidFunction,
            'EllipticParaboloidFunction': module.EllipticParaboloidFunction,
            'RippleFunction': module.RippleFunction,
            'RoseCurveFunction': module.RoseCurveFunction,
            'LissajousFunction': module.LissajousFunction,
            'HeartShapeFunction': module.HeartShapeFunction,
            'ButterflyCurveFunction': module.ButterflyCurveFunction,
            'ArchimedeanSpiralFunction': module.ArchimedeanSpiralFunction,
            'TorusFunction': module.TorusFunction,
            'SombreroFunction': module.SombreroFunction,
            'CustomExpressionFunction': module.CustomExpressionFunction,
        }
    return {}


# 导出
__all__ = [
    'get_functions_module',
    'get_function_factory',
    'get_function_classes',
]


# 便捷导入
_functions_module = get_functions_module()
if _functions_module is not None:
    WindFieldFunctionFactory = _functions_module.WindFieldFunctionFactory
    WindFieldFunction = _functions_module.WindFieldFunction
    FunctionParams = _functions_module.FunctionParams
    CustomExpressionFunction = _functions_module.CustomExpressionFunction
else:
    # 如果导入失败，设置为None，使用时会报错
    WindFieldFunctionFactory = None
    WindFieldFunction = None
    FunctionParams = None
    CustomExpressionFunction = None
