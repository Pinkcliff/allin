# -*- coding: utf-8 -*-
"""
融合系统配置文件
整合 frist 和 setest 两个程序的配置
"""
import os

# ==================== 系统配置 ====================
SYSTEM_CONFIG = {
    'app_name': '微小型无人机智能风场测试评估系统 - 融合版',
    'version': '2.0.0',
    'company': '风洞实验室',
    'author': '融合开发团队'
}

# ==================== Redis 配置 (来自 setest) ====================
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True
}

# ==================== MongoDB 配置 (来自 setest) ====================
MONGO_CONFIG = {
    'uri': 'mongodb://localhost:27017/',
    'db_name': 'sensor_data',
    'collections': 'collections',
    'samples': 'samples'
}

# ==================== 传感器配置 (来自 setest) ====================
SENSOR_CONFIG = {
    'fans': {
        'count': 1600,
        'range': (0, 1000),
        'name': '风扇PWM',
        'unit': '',
        'rows': 40,
        'cols': 40
    },
    'temp_sensors': {
        'count': 100,
        'range': (-20, 80),
        'name': '温度传感器',
        'unit': '℃',
        'rows': 10,
        'cols': 10
    },
    'wind_speed_sensors': {
        'count': 100,
        'range': (0, 30),
        'name': '风速传感器',
        'unit': 'm/s',
        'rows': 10,
        'cols': 10
    },
    'temp_humidity_sensors': {
        'count': 4,
        'temp_range': (-20, 80),
        'humidity_range': (0, 100),
        'name': '温湿度传感器',
        'temp_unit': '℃',
        'humidity_unit': '%'
    },
    'pressure_sensor': {
        'temp_range': (-20, 80),
        'pressure_range': (0, 100),
        'name': '大气压力传感器',
        'temp_unit': '℃',
        'pressure_unit': 'KPa'
    }
}

# ==================== 采集配置 (来自 setest) ====================
SAMPLE_RATE = 10  # 每秒采集次数

# ==================== 通信协议配置 (来自 frist) ====================
COMM_PROTOCOLS = {
    "主控制器": "TCP/IP",
    "电驱": "EtherCAT",
    "风速传感": "EtherCAT",
    "温度传感": "EtherCAT",
    "湿度传感": "EtherCAT",
    "动捕": "API",
    "俯仰伺服": "Modbus",
    "造雨": "Modbus",
    "喷雾": "Modbus",
    "训练": "API",
    "仿真": "API",
    "电力": "Modbus"
}

# ==================== 风扇配置 (来自 frist) ====================
FAN_CONFIG = {
    'array_rows': 40,
    'array_cols': 40,
    'total_fans': 1600,
    'max_pwm': 1000,
    'min_pwm': 0,
    'default_pwm': 0,
    'fan_id_format': 'X{:03d}Y{:03d}'  # X000Y000 格式
}

# ==================== CFD 配置 (来自 frist) ====================
CFD_CONFIG = {
    'margin': {
        'x_min': 0.5,
        'x_max': 1.0,
        'y_min': 0.5,
        'y_max': 1.0,
        'z_min': 0.5,
        'z_max': 1.0
    },
    'inlet_length': 1.0,
    'outlet_length': 2.0,
    'grid_resolution': 0.05
}

# ==================== 路径配置 ====================
# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 模块路径
DASHBOARD_DIR = os.path.join(ROOT_DIR, '仪表盘')
WIND_CONFIG_DIR = os.path.join(ROOT_DIR, '风场设置')
PRE_PROCESSOR_DIR = os.path.join(ROOT_DIR, '前处理')
HARDWARE_DIR = os.path.join(ROOT_DIR, '硬件控制')
WIND_EDITOR_DIR = os.path.join(ROOT_DIR, '风场编辑器')
CORE_DIR = os.path.join(ROOT_DIR, '核心模块')
RESOURCE_DIR = os.path.join(ROOT_DIR, '资源')

# 资源文件路径
BACKGROUND_IMAGE = os.path.join(RESOURCE_DIR, '背景.png')
MOTION_IMAGE = os.path.join(RESOURCE_DIR, '动捕.png')
WIND_IMAGE = os.path.join(RESOURCE_DIR, '风场.png')

# ==================== UI 配置 ====================
UI_CONFIG = {
    'window_width': 1400,
    'window_height': 900,
    'theme': 'dark',  # dark 或 light
    'animation_enabled': True,
    'dock_tab_position': 'North'
}

# ==================== 日志配置 ====================
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.path.join(ROOT_DIR, 'system.log'),
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# ==================== 硬件控制配置 (来自 frist) ====================
HARDWARE_CONFIG = {
    'modbus': {
        'host': '192.168.1.100',
        'port': 502,
        'slave_id': 1
    },
    'ethercat': {
        'ifname': 'eth0',
        'cycle_time': 1000  # 微秒
    }
}

# ==================== 数据可视化配置 ====================
VISUALIZATION_CONFIG = {
    'color_map': {
        'fan': 'RdYlGn',      # 红-黄-绿 渐变
        'temp': 'coolwarm',   # 冷-暖 渐变
        'wind': 'viridis'     # 紫-黄 渐变
    },
    'update_interval': 100,  # 毫秒
    'max_data_points': 1000  # 图表最大数据点数
}

# ==================== 仿真配置 ====================
SIMULATION_CONFIG = {
    'enabled': True,
    'data_interval': 100,  # 毫秒
    'random_variation': 0.1  # 10% 随机变化
}

# ==================== 调试配置 ====================
DEBUG_CONFIG = {
    'enabled': False,
    'log_to_file': True,
    'verbose': False
}

# ==================== 导出配置字典 ====================
ALL_CONFIGS = {
    'system': SYSTEM_CONFIG,
    'redis': REDIS_CONFIG,
    'mongo': MONGO_CONFIG,
    'sensors': SENSOR_CONFIG,
    'sample_rate': SAMPLE_RATE,
    'comm_protocols': COMM_PROTOCOLS,
    'fan': FAN_CONFIG,
    'cfd': CFD_CONFIG,
    'ui': UI_CONFIG,
    'log': LOG_CONFIG,
    'hardware': HARDWARE_CONFIG,
    'visualization': VISUALIZATION_CONFIG,
    'simulation': SIMULATION_CONFIG,
    'debug': DEBUG_CONFIG
}


def get_config(config_name: str):
    """
    获取指定配置

    Args:
        config_name: 配置名称

    Returns:
        配置字典
    """
    return ALL_CONFIGS.get(config_name, {})


def print_all_configs():
    """打印所有配置（用于调试）"""
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(ALL_CONFIGS)


if __name__ == '__main__':
    print_all_configs()
