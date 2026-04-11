# -*- coding: utf-8 -*-
"""
测试桌面端到Web端的数据同步
"""
import time
import requests
import json

def test_sync():
    """测试同步功能"""
    web_api_url = "http://localhost:8000"

    print("=" * 60)
    print("Desktop to Web Sync Test")
    print("=" * 60)
    print()

    # 测试风扇状态同步
    print("[1] Testing fan status sync...")
    fan_data = [
        {"id": "X001Y001", "pwm": 500, "status": "on"},
        {"id": "X001Y002", "pwm": 600, "status": "on"},
        {"id": "X002Y001", "pwm": 0, "status": "off"}
    ]

    try:
        response = requests.post(
            f"{web_api_url}/api/fan/sync",
            json={"fans": fan_data, "timestamp": time.time()},
            timeout=2
        )
        if response.status_code == 200:
            print("   [OK] Fan status sync successful")
        else:
            print(f"   [FAIL] Fan status sync failed: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")

    print()

    # 测试环境数据同步
    print("[2] Testing environment data sync...")
    env_data = {
        "temperature": 26.5,
        "humidity": 65.0,
        "pressure": 101325.0,
        "density": 1.185
    }

    try:
        response = requests.post(
            f"{web_api_url}/api/env/sync",
            json=env_data,
            timeout=2
        )
        if response.status_code == 200:
            print("   [OK] Environment data sync successful")
        else:
            print(f"   [FAIL] Environment data sync failed: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")

    print()

    # 测试设备状态同步
    print("[3] Testing device status sync...")
    device_data = {
        "devices": [
            {"name": "Main Controller", "status": "online"},
            {"name": "Motor Drive", "status": "online"},
            {"name": "Wind Sensor", "status": "online"}
        ]
    }

    try:
        response = requests.post(
            f"{web_api_url}/api/device/sync",
            json=device_data,
            timeout=2
        )
        if response.status_code == 200:
            print("   [OK] Device status sync successful")
        else:
            print(f"   [FAIL] Device status sync failed: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")

    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("Please check the Web frontend at http://localhost:5174")
    print("to see if the synchronized data is displayed.")
    print()

if __name__ == "__main__":
    test_sync()
