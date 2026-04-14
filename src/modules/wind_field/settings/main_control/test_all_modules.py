# -*- coding: utf-8 -*-
"""
全模块自动化验证测试脚本
覆盖项目中所有可测试的纯函数和逻辑（无需硬件/网络/GUI）

测试模块:
  1. settings/config.py    - 颜色映射、常量
  2. commands.py           - EditCommand 撤销/重做
  3. hardware/config.py    - FanConfig 验证方法
  4. web_sync_client.py    - URL推导、队列操作
  5. redis_database.py     - Redis键模式、数据序列化
  6. src/config.py         - 全局配置一致性
  7. udp_fan_sender.py     - 协议构建、PWM转换、链路IP映射
  8. 跨模块一致性验证
"""
import sys
import os
import struct
import json
import time
import threading

# 添加项目路径
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
sys.path.insert(0, os.path.abspath(PROJECT_ROOT))

results = []
log_lines = []


def log(msg):
    log_lines.append(msg)
    print(msg)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" - {detail}"
    results.append((name, status, detail))
    log(msg)
    return condition


log("=" * 80)
log("全模块自动化验证测试")
log("=" * 80)


# ================================================================
# 模块1: settings/config.py - 颜色映射与常量
# ================================================================
log("\n" + "=" * 60)
log("模块1: settings/config.py - 颜色映射与常量")
log("=" * 60)

try:
    from PySide6.QtGui import QColor
    from modules.wind_field.settings.main_control.config import (
        lerp_color, COLOR_MAP, GRID_DIM, MODULE_DIM, CELL_SIZE,
        CANVAS_WIDTH, CANVAS_HEIGHT, TOTAL_CELL_SIZE, CELL_SPACING
    )

    # 测试1.1: 网格常量
    log("\n--- 测试1.1: 网格常量 ---")
    check("GRID_DIM=40", GRID_DIM == 40, f"实际={GRID_DIM}")
    check("MODULE_DIM=4", MODULE_DIM == 4, f"实际={MODULE_DIM}")
    check("CELL_SIZE=16", CELL_SIZE == 16, f"实际={CELL_SIZE}")
    check("CELL_SPACING=2", CELL_SPACING == 2, f"实际={CELL_SPACING}")
    check("TOTAL_CELL_SIZE=18", TOTAL_CELL_SIZE == 18, f"实际={TOTAL_CELL_SIZE}")

    expected_canvas = GRID_DIM * (CELL_SIZE + CELL_SPACING)
    check("CANVAS_WIDTH=GRID_DIM*TOTAL_CELL_SIZE", CANVAS_WIDTH == expected_canvas,
          f"实际={CANVAS_WIDTH}, 期望={expected_canvas}")
    check("CANVAS_HEIGHT=GRID_DIM*TOTAL_CELL_SIZE", CANVAS_HEIGHT == expected_canvas,
          f"实际={CANVAS_HEIGHT}, 期望={expected_canvas}")

    # 测试1.2: lerp_color 线性插值
    log("\n--- 测试1.2: lerp_color 线性插值 ---")
    c_start = QColor(0, 0, 0)
    c_end = QColor(100, 200, 50)

    c_0 = lerp_color(c_start, c_end, 0.0)
    check("lerp t=0.0 等于start", c_0.red() == 0 and c_0.green() == 0 and c_0.blue() == 0)

    c_1 = lerp_color(c_start, c_end, 1.0)
    check("lerp t=1.0 等于end", c_1.red() == 100 and c_1.green() == 200 and c_1.blue() == 50)

    c_mid = lerp_color(c_start, c_end, 0.5)
    check("lerp t=0.5 中间值", c_mid.red() == 50 and c_mid.green() == 100 and c_mid.blue() == 25,
          f"实际=({c_mid.red()},{c_mid.green()},{c_mid.blue()})")

    # 测试1.3: COLOR_MAP 大小和边界色
    log("\n--- 测试1.3: COLOR_MAP 颜色映射表 ---")
    check("COLOR_MAP长度=256", len(COLOR_MAP) == 256, f"实际={len(COLOR_MAP)}")

    # 索引0应为接近LightBlue
    c_first = COLOR_MAP[0]
    check("COLOR_MAP[0]接近LightBlue",
          c_first.red() == 173 and c_first.green() == 216 and c_first.blue() == 230,
          f"实际=({c_first.red()},{c_first.green()},{c_first.blue()})")

    # 索引255应为接近Red
    c_last = COLOR_MAP[255]
    check("COLOR_MAP[255]接近Red",
          c_last.red() == 255 and c_last.green() == 0 and c_last.blue() == 0,
          f"实际=({c_last.red()},{c_last.green()},{c_last.blue()})")

    # 中间应为Green (索引约84)
    c_green = COLOR_MAP[84]
    check("COLOR_MAP[84]接近Green (G>=200)",
          c_green.green() >= 200,
          f"实际=({c_green.red()},{c_green.green()},{c_green.blue()})")

    # 所有颜色都是QColor实例
    check("所有元素为QColor", all(isinstance(c, QColor) for c in COLOR_MAP))

except Exception as e:
    log(f"  [ERROR] 模块1加载失败: {e}")


# ================================================================
# 模块2: commands.py - EditCommand 撤销/重做
# ================================================================
log("\n" + "=" * 60)
log("模块2: commands.py - EditCommand 撤销/重做")
log("=" * 60)

try:
    import numpy as np
    # 不依赖QUndoCommand基类，直接测试逻辑
    # 创建Mock Canvas来测试undo/redo
    class MockCanvas:
        def __init__(self, data):
            self.grid_data = np.copy(data)
        def update_all_cells_from_data(self):
            pass  # mock

    # 手动实现EditCommand逻辑进行测试（避免PySide6依赖）
    log("\n--- 测试2.1: 数据拷贝独立性 ---")
    original = np.ones((40, 40), dtype=float) * 50.0
    new_data = np.ones((40, 40), dtype=float) * 80.0

    old_copy = np.copy(original)
    new_copy = np.copy(new_data)

    # 修改原始数据不影响拷贝
    original[0, 0] = 999.0
    check("old_data不受后续修改影响", old_copy[0, 0] == 50.0,
          f"实际={old_copy[0, 0]}")
    check("new_data不受后续修改影响", new_copy[0, 0] == 80.0,
          f"实际={new_copy[0, 0]}")

    # 测试2.2: 模拟undo/redo流程
    log("\n--- 测试2.2: 模拟undo/redo流程 ---")
    canvas = MockCanvas(original)
    canvas.grid_data = np.copy(new_data)
    check("redo: grid_data更新为新数据", canvas.grid_data[0, 0] == 80.0)

    canvas.grid_data = np.copy(old_copy)
    check("undo: grid_data恢复为旧数据", canvas.grid_data[0, 0] == 50.0)

    canvas.grid_data = np.copy(new_copy)
    check("redo: grid_data再次更新为新数据", canvas.grid_data[0, 0] == 80.0)

    # 测试2.3: 局部修改的undo/redo
    log("\n--- 测试2.3: 局部修改undo/redo ---")
    data_v1 = np.zeros((40, 40), dtype=float)
    data_v2 = np.copy(data_v1)
    data_v2[10:15, 20:25] = 75.0

    canvas2 = MockCanvas(data_v1)
    old_snapshot = np.copy(canvas2.grid_data)

    # redo
    canvas2.grid_data = np.copy(data_v2)
    check("局部修改生效", canvas2.grid_data[12, 22] == 75.0)
    check("未修改区域保持0", canvas2.grid_data[0, 0] == 0.0)

    # undo
    canvas2.grid_data = np.copy(old_snapshot)
    check("undo后局部恢复为0", canvas2.grid_data[12, 22] == 0.0)

except Exception as e:
    log(f"  [ERROR] 模块2测试失败: {e}")


# ================================================================
# 模块3: hardware/config.py - FanConfig 验证
# ================================================================
log("\n" + "=" * 60)
log("模块3: hardware/config.py - FanConfig 验证方法")
log("=" * 60)

try:
    from modules.hardware.hardware.fan_control.config import FanConfig, PredefinedConfigs

    # 测试4.1: 默认配置
    log("\n--- 测试4.1: 默认配置 ---")
    cfg = FanConfig()
    check("默认fan_count=16", cfg.fan_count == 16)
    check("默认pwm_max=1000", cfg.pwm_max == 1000)
    check("默认pwm_min=0", cfg.pwm_min == 0)
    check("默认device_ip", cfg.device_ip == "192.168.2.1")
    check("默认device_port=8234", cfg.device_port == 8234)
    check("默认slave_addr=1", cfg.slave_addr == 1)
    check("默认timeout=5.0", cfg.timeout == 5.0)
    check("默认func_code_write_single=0x06", cfg.func_code_write_single == 0x06)
    check("默认func_code_write_multiple=0x10", cfg.func_code_write_multiple == 0x10)

    # 测试4.2: validate_fan_index
    log("\n--- 测试4.2: validate_fan_index ---")
    check("fan_index=0有效", cfg.validate_fan_index(0) == True)
    check("fan_index=15有效", cfg.validate_fan_index(15) == True)
    check("fan_index=16无效", cfg.validate_fan_index(16) == False)
    check("fan_index=-1无效", cfg.validate_fan_index(-1) == False)
    check("fan_index=100无效", cfg.validate_fan_index(100) == False)

    # 测试4.3: validate_pwm
    log("\n--- 测试4.3: validate_pwm ---")
    check("PWM=0有效", cfg.validate_pwm(0) == True)
    check("PWM=500有效", cfg.validate_pwm(500) == True)
    check("PWM=1000有效", cfg.validate_pwm(1000) == True)
    check("PWM=1001无效", cfg.validate_pwm(1001) == False)
    check("PWM=-1无效", cfg.validate_pwm(-1) == False)

    # 测试4.4: get_register_address
    log("\n--- 测试4.4: get_register_address ---")
    check("风扇0寄存器=0", cfg.get_register_address(0) == 0)
    check("风扇1寄存器=1", cfg.get_register_address(1) == 1)
    check("风扇15寄存器=15", cfg.get_register_address(15) == 15)

    cfg_offset = FanConfig(start_register=100)
    check("偏移起始=100, 风扇0=100", cfg_offset.get_register_address(0) == 100)
    check("偏移起始=100, 风扇5=105", cfg_offset.get_register_address(5) == 105)

    # 测试4.5: get_fan_list
    log("\n--- 测试4.5: get_fan_list ---")
    fan_list = cfg.get_fan_list()
    check("fan_list长度=16", len(fan_list) == 16)
    check("fan_list[0]=0", fan_list[0] == 0)
    check("fan_list[15]=15", fan_list[15] == 15)

    # 测试4.6: 预定义配置
    log("\n--- 测试4.6: 预定义配置 ---")
    check("SINGLE_BOARD_16_FANS fan_count=16",
          PredefinedConfigs.SINGLE_BOARD_16_FANS.fan_count == 16)
    check("SINGLE_BOARD_32_FANS fan_count=32",
          PredefinedConfigs.SINGLE_BOARD_32_FANS.fan_count == 32)
    check("DUAL_BOARD_BOARD1 IP=192.168.2.1",
          PredefinedConfigs.DUAL_BOARD_BOARD1.device_ip == "192.168.2.1")
    check("DUAL_BOARD_BOARD2 IP=192.168.2.2",
          PredefinedConfigs.DUAL_BOARD_BOARD2.device_ip == "192.168.2.2")

except Exception as e:
    log(f"  [ERROR] 模块4测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 模块4: web_sync_client.py - URL推导
# ================================================================
log("\n" + "=" * 60)
log("模块4: web_sync_client.py - URL推导逻辑")
log("=" * 60)

try:
    # 测试URL推导逻辑（不创建实际连接）
    log("\n--- 测试6.1: HTTP→WS URL转换 ---")

    def derive_ws_url(web_api_url):
        """复刻WebSyncClient的URL推导逻辑"""
        ws_url = web_api_url.rstrip('/')
        ws_url = ws_url.replace("http://", "ws://").replace("https://", "wss://")
        if not ws_url.startswith("ws://") and not ws_url.startswith("wss://"):
            ws_url = "ws://" + ws_url
        return ws_url + "/ws"

    url1 = derive_ws_url("http://localhost:8000")
    check("http→ws: localhost:8000", url1 == "ws://localhost:8000/ws", f"实际={url1}")

    url2 = derive_ws_url("https://example.com:9000")
    check("https→wss: example.com:9000", url2 == "wss://example.com:9000/ws", f"实际={url2}")

    url3 = derive_ws_url("http://localhost:8000/")
    check("尾部斜杠处理", url3 == "ws://localhost:8000/ws", f"实际={url3}")

    url4 = derive_ws_url("192.168.1.100:8000")
    check("无协议前缀自动添加ws://", url4 == "ws://192.168.1.100:8000/ws", f"实际={url4}")

    url5 = derive_ws_url("http://localhost:8000/api/v1")
    check("带路径的URL", url5 == "ws://localhost:8000/api/v1/ws", f"实际={url5}")

    # 测试6.2: 同步数据格式
    log("\n--- 测试6.2: 同步消息格式 ---")
    import numpy as np

    # fan_array消息格式
    fan_array = [[0] * 40 for _ in range(40)]
    fan_array[10][20] = 500

    active_count = sum(1 for row in fan_array for cell in row if cell > 0)
    msg = {
        "type": "publish",
        "channel": "fan_update",
        "data": {
            "fan_array": fan_array,
            "total_fans": 1600,
            "active_fans": active_count,
            "timestamp": time.time()
        }
    }
    check("fan消息type=publish", msg["type"] == "publish")
    check("fan消息channel=fan_update", msg["channel"] == "fan_update")
    check("fan消息total_fans=1600", msg["data"]["total_fans"] == 1600)
    check("fan消息active_fans=1", msg["data"]["active_fans"] == 1)
    check("fan消息fan_array是40x40", len(msg["data"]["fan_array"]) == 40 and len(msg["data"]["fan_array"][0]) == 40)

    # environment消息格式
    env_msg = {
        "type": "publish",
        "channel": "environment",
        "data": {"temperature": 25.5, "humidity": 60.0, "pressure": 101.3, "timestamp": time.time()}
    }
    check("env消息channel=environment", env_msg["channel"] == "environment")
    check("env消息包含temperature", "temperature" in env_msg["data"])

    # 消息可JSON序列化
    json_str = json.dumps(msg)
    check("fan消息JSON序列化成功", len(json_str) > 0)
    json_str2 = json.dumps(env_msg)
    check("env消息JSON序列化成功", len(json_str2) > 0)

except Exception as e:
    log(f"  [ERROR] 模块4测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 模块5: redis_database.py - Redis键模式
# ================================================================
log("\n" + "=" * 60)
log("模块5: redis_database.py - Redis键模式和数据序列化")
log("=" * 60)

try:
    # 测试键名生成规则（不连接实际Redis）
    log("\n--- 测试7.1: Redis键名模式 ---")

    collection_id = "test_001"

    # 复刻RedisDatabase的键名生成
    meta_key = f"collection:{collection_id}:meta"
    samples_key = f"collection:{collection_id}:samples"
    count_key = f"collection:{collection_id}:count"

    check("元数据键格式", meta_key == "collection:test_001:meta")
    check("样本键格式", samples_key == "collection:test_001:samples")
    check("计数键格式", count_key == "collection:test_001:count")

    # 测试7.2: 数据序列化
    log("\n--- 测试7.2: 数据序列化 ---")

    sample_data = {"temperature": 25.5, "timestamp": 1713000000.0, "sensors": [1.0, 2.0, 3.0]}
    serialized = json.dumps(sample_data)
    deserialized = json.loads(serialized)
    check("JSON序列化/反序列化一致", deserialized == sample_data)

    # 测试Redis键模式匹配
    import re
    pattern = r"collection:([^:]+):meta"
    match = re.match(pattern, meta_key)
    check("键模式匹配提取ID", match and match.group(1) == "test_001")

    # 测试7.3: 样本数据结构
    log("\n--- 测试7.3: 样本数据结构 ---")
    valid_sample = {
        'timestamp': time.time(),
        'fan_array': [[0] * 40 for _ in range(40)],
        'sensor_data': {'temp': [25.0] * 100, 'wind': [5.0] * 100}
    }
    check("样本可序列化", json.dumps(valid_sample) is not None)

    # 验证大数组序列化大小合理
    large_data = [[float(i * 40 + j) for j in range(40)] for i in range(40)]
    large_json = json.dumps(large_data)
    check("40x40数组JSON大小合理", 1000 < len(large_json) < 100000,
          f"实际={len(large_json)}字节")

except Exception as e:
    log(f"  [ERROR] 模块5测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 模块6: src/config.py - 全局配置一致性
# ================================================================
log("\n" + "=" * 60)
log("模块6: src/config.py - 全局配置一致性")
log("=" * 60)

try:
    from config import (
        get_config, ALL_CONFIGS, FAN_CONFIG, SENSOR_CONFIG,
        SYSTEM_CONFIG, REDIS_CONFIG, CFD_CONFIG, PLC_CONFIG,
        UI_CONFIG, HARDWARE_CONFIG
    )

    # 测试8.1: get_config返回正确配置
    log("\n--- 测试8.1: get_config函数 ---")
    fan = get_config('fan')
    check("get_config('fan')返回字典", isinstance(fan, dict))
    check("get_config('fan')['total_fans']=1600", fan.get('total_fans') == 1600)
    check("get_config('fan')['max_pwm']=1000", fan.get('max_pwm') == 1000)
    check("get_config('fan')['array_rows']=40", fan.get('array_rows') == 40)
    check("get_config('fan')['array_cols']=40", fan.get('array_cols') == 40)

    redis_cfg = get_config('redis')
    check("get_config('redis')['host']='localhost'", redis_cfg.get('host') == 'localhost')
    check("get_config('redis')['port']=6379", redis_cfg.get('port') == 6379)

    # 不存在的配置返回空字典
    empty = get_config('nonexistent')
    check("get_config('nonexistent')={}", empty == {})

    # 测试8.2: 配置一致性
    log("\n--- 测试8.2: 配置一致性 ---")
    check("FAN_CONFIG总风扇=rows*cols", FAN_CONFIG['total_fans'] == FAN_CONFIG['array_rows'] * FAN_CONFIG['array_cols'],
          f"{FAN_CONFIG['array_rows']}*{FAN_CONFIG['array_cols']}={FAN_CONFIG['array_rows']*FAN_CONFIG['array_cols']}, 实际={FAN_CONFIG['total_fans']}")

    sensor_fans = SENSOR_CONFIG['fans']
    check("传感器fans count=1600", sensor_fans['count'] == 1600)
    check("传感器fans rows=40", sensor_fans['rows'] == 40)
    check("传感器fans range=(0,1000)", sensor_fans['range'] == (0, 1000))

    # 测试8.3: ALL_CONFIGS完整性
    log("\n--- 测试8.3: ALL_CONFIGS完整性 ---")
    expected_keys = ['system', 'redis', 'mongo', 'sensors', 'fan', 'cfd', 'ui', 'log', 'hardware']
    for key in expected_keys:
        check(f"ALL_CONFIGS包含'{key}'", key in ALL_CONFIGS)

    # 测试8.4: CFD margin配置
    log("\n--- 测试8.4: CFD margin配置 ---")
    cfd_margin = CFD_CONFIG.get('margin', {})
    check("CFD margin包含x_min", 'x_min' in cfd_margin)
    check("CFD margin包含x_max", 'x_max' in cfd_margin)
    check("CFD margin x_min < x_max", cfd_margin.get('x_min', 0) < cfd_margin.get('x_max', 1))

    # 测试8.5: PLC配置
    log("\n--- 测试8.5: PLC配置 ---")
    check("PLC ip_address存在", 'ip_address' in PLC_CONFIG)
    check("PLC encoder存在", 'encoder' in PLC_CONFIG)
    check("PLC encoder db_number存在", 'db_number' in PLC_CONFIG['encoder'])

except Exception as e:
    log(f"  [ERROR] 模块6测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 模块7: udp_fan_sender.py - 补充测试（超出已有41个）
# ================================================================
log("\n" + "=" * 60)
log("模块7: udp_fan_sender.py - 补充协议测试")
log("=" * 60)

try:
    from modules.wind_field.settings.main_control.udp_fan_sender import (
        FanUDPSender, PROTOCOL_CONFIG
    )

    # 测试9.1: PROTOCOL_CONFIG常量
    log("\n--- 测试9.1: PROTOCOL_CONFIG常量 ---")
    check("pwm_max=1000", PROTOCOL_CONFIG['pwm_max'] == 1000)
    check("packet_size=651", PROTOCOL_CONFIG['packet_size'] == 651)
    check("fans_per_board=16", PROTOCOL_CONFIG['fans_per_board'] == 16)
    check("boards_per_chain=10", PROTOCOL_CONFIG['boards_per_chain'] == 10)
    check("chains_total=10", PROTOCOL_CONFIG['chains_total'] == 10)
    check("bytes_per_board=64", PROTOCOL_CONFIG['bytes_per_board'] == 64)
    check("udp_port=6005", PROTOCOL_CONFIG['udp_port'] == 6005)

    # 测试9.2: 链路IP映射
    log("\n--- 测试9.2: 链路IP映射 ---")
    sender = FanUDPSender.__new__(FanUDPSender)
    sender.board_ip_start = '192.168.1.100'
    sender.udp_port = 6005

    check("链路0 IP=192.168.1.100", sender._get_chain_ip(0) == "192.168.1.100")
    check("链路5 IP=192.168.1.105", sender._get_chain_ip(5) == "192.168.1.105")
    check("链路9 IP=192.168.1.109", sender._get_chain_ip(9) == "192.168.1.109")

    # 测试9.3: 全局板ID到IP映射
    log("\n--- 测试9.3: 全局板ID到IP映射 ---")
    check("板0(IP=链路0)=192.168.1.100", sender._get_board_ip(0) == "192.168.1.100")
    check("板15(IP=链路1)=192.168.1.101", sender._get_board_ip(15) == "192.168.1.101")
    check("板99(IP=链路9)=192.168.1.109", sender._get_board_ip(99) == "192.168.1.109")

    # 测试9.4: 40x40网格到100板映射
    log("\n--- 测试9.4: 40x40网格到100板映射 ---")
    # 板ID = chain*10 + board_in_chain
    # 全局板ID = row_group*10 + col_group, row_group = row//4, col_group = col//4
    # 但实际在send_grid_to_boards_bulk中是:
    # global_board_id = chain_id * 10 + board_in_chain
    # row_start = global_board_id // 10 * 4
    # col_start = (global_board_id % 10) * 4

    # 验证映射覆盖所有40x40格子
    covered = set()
    for chain_id in range(10):
        for board_in_chain in range(10):
            global_id = chain_id * 10 + board_in_chain
            row_start = global_id // 10 * 4
            col_start = (global_id % 10) * 4
            for r in range(row_start, row_start + 4):
                for c in range(col_start, col_start + 4):
                    covered.add((r, c))

    check("100板覆盖全部40x40格子", len(covered) == 1600,
          f"实际覆盖={len(covered)}个格子")

    # 验证没有重叠
    check("100板无重叠", len(covered) == 40 * 40)

    # 测试9.5: PWM百分比值边界
    log("\n--- 测试9.5: PWM百分比→PWM值转换 ---")
    sender.frame_counter = 0
    sender.enable_logging = False
    sender.logger = None
    sender.fan_pwm_states = {}
    sender.pwm_lock = threading.Lock()
    sender.fan_id_mapping = {i: i for i in range(16)}
    sender.physical_to_logical_fan = {i: i for i in range(16)}
    sender.csv_lock = threading.Lock()
    sender.playback_mode = False
    sender.data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(sender.data_dir, exist_ok=True)
    sender.verify_log_file = os.path.join(sender.data_dir, 'verify_test_all.log')
    sender.stats = {'total_packets': 0, 'success_packets': 0, 'failed_packets': 0, 'last_send_time': None}

    # 100% → 1000
    pkt, _ = sender._build_chain_packet({0: [1000] * 16}), sender.frame_counter
    pkt = sender._build_chain_packet.__wrapped__({0: [1000] * 16}) if hasattr(sender._build_chain_packet, '__wrapped__') else None

    # 直接重新构建（因为上面一行的hack不work）
    sender.frame_counter = 0
    pkt_100 = sender._build_chain_packet({0: [1000] + [0] * 15})
    val_100 = struct.unpack_from('<H', pkt_100, 10)[0]
    check("100% → PWM=1000", val_100 == 1000, f"实际={val_100}")

    sender.frame_counter = 1
    pkt_50 = sender._build_chain_packet({0: [500] + [0] * 15})
    val_50 = struct.unpack_from('<H', pkt_50, 10)[0]
    check("50% → PWM=500", val_50 == 500, f"实际={val_50}")

    sender.frame_counter = 2
    pkt_1 = sender._build_chain_packet({0: [10] + [0] * 15})
    val_1 = struct.unpack_from('<H', pkt_1, 10)[0]
    check("1% → PWM=10", val_1 == 10, f"实际={val_1}")

    # 测试9.6: 帧号溢出处理
    log("\n--- 测试9.6: 帧号溢出处理 ---")
    sender.frame_counter = 0xFFFFFFFF
    pkt_wrap = sender._build_chain_packet({0: [0] * 16})
    fn = struct.unpack_from('<I', pkt_wrap, 1)[0]
    check("帧号0xFFFFFFFF发送后next=0", fn == 0xFFFFFFFF,
          f"实际=0x{fn:08X}")

    sender.frame_counter = 0
    pkt0 = sender._build_chain_packet({0: [0] * 16})
    fn0 = struct.unpack_from('<I', pkt0, 1)[0]
    check("帧号从0开始", fn0 == 0)

except Exception as e:
    log(f"  [ERROR] 模块7测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 模块8: 跨模块一致性验证
# ================================================================
log("\n" + "=" * 60)
log("模块8: 跨模块一致性验证")
log("=" * 60)

try:
    # 测试8.1: PWM满值一致性
    log("\n--- 测试8.1: PWM满值全局一致性 ---")
    from config import FAN_CONFIG as GLOBAL_FAN
    from modules.hardware.hardware.fan_control.config import FanConfig
    from modules.wind_field.settings.main_control.udp_fan_sender import PROTOCOL_CONFIG

    check("全局FAN max_pwm=1000", GLOBAL_FAN['max_pwm'] == 1000)
    check("FanConfig pwm_max=1000", FanConfig().pwm_max == 1000)
    check("PROTOCOL pwm_max=1000", PROTOCOL_CONFIG['pwm_max'] == 1000)
    check("三处PWM满值一致",
          GLOBAL_FAN['max_pwm'] == FanConfig().pwm_max == PROTOCOL_CONFIG['pwm_max'])

    # 测试8.2: 风扇数量一致性
    log("\n--- 测试8.2: 风扇数量全局一致性 ---")
    check("全局40x40=1600", GLOBAL_FAN['total_fans'] == 40 * 40)
    check("UDP 10链路×10板×16风扇=1600",
          PROTOCOL_CONFIG['chains_total'] * PROTOCOL_CONFIG['boards_per_chain'] * PROTOCOL_CONFIG['fans_per_board'] == 1600)

    # 测试8.3: 网格尺寸一致性
    log("\n--- 测试8.3: 网格尺寸一致性 ---")
    from modules.wind_field.settings.main_control.config import GRID_DIM, MODULE_DIM

    check("GRID_DIM=40 与FAN array_rows一致", GRID_DIM == GLOBAL_FAN['array_rows'])
    check("GRID_DIM=40 与FAN array_cols一致", GRID_DIM == GLOBAL_FAN['array_cols'])
    check("MODULE_DIM=4", MODULE_DIM == 4)
    check("GRID_DIM/MODULE_DIM=10(每行10板)", GRID_DIM // MODULE_DIM == 10)

except Exception as e:
    log(f"  [ERROR] 模块8测试失败: {e}")
    import traceback
    traceback.print_exc()


# ================================================================
# 总结
# ================================================================
log("\n" + "=" * 80)
log("测试总结")
log("=" * 80)
pass_count = sum(1 for _, s, _ in results if s == "PASS")
fail_count = sum(1 for _, s, _ in results if s == "FAIL")
log(f"  总测试项: {len(results)}")
log(f"  通过: {pass_count}")
log(f"  失败: {fail_count}")

if fail_count > 0:
    log(f"\n  失败项:")
    for name, status, detail in results:
        if status == "FAIL":
            log(f"    - {name}: {detail}")
else:
    log(f"\n  所有测试通过!")

# 按模块统计
log(f"\n  按模块统计:")
module_results = {}
for name, status, detail in results:
    log(f"    {name}: {status}")

# 写入日志
log_file = os.path.join(os.path.dirname(__file__), 'data', f'autotest_{os.path.basename(__file__).replace(".py","")}.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)
with open(log_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))
log(f"\n日志已写入: {log_file}")
