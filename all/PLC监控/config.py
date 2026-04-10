# PLC监控模块配置

# PLC连接配置
PLC_CONFIG = {
    'ip_address': '192.168.0.1',
    'rack': 0,
    'slot': 1,
    'timeout': 10
}

# 编码器配置
ENCODER_CONFIG = {
    'db_number': 5,
    'offset': 124,
    'data_type': 'REAL',
    'min_value': -1000.0,
    'max_value': 1000.0
}

# 点位表配置
POINT_TABLE_CONFIG = {
    'file': '点位表.xlsx',
    'refresh_interval': 1000,  # 毫秒
    'batch_by_db': True
}
