"""
测试桌面端到Web端风扇数据同步
"""
import requests
import time

def sync_test_data():
    """发送测试的风扇数据到Web端"""
    # 创建一个测试风扇阵列（中心聚焦模式）
    test_fan_array = []
    for y in range(40):
        row = []
        for x in range(40):
            # 计算到中心的距离
            cx, cy = 20, 20
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            # 中心高PWM（红色），边缘低PWM（蓝色）
            pwm = max(0, min(1000, int(1000 - dist * 30)))
            row.append(pwm)
        test_fan_array.append(row)

    # 发送到Web端
    response = requests.post(
        'http://localhost:8000/api/fan/sync',
        json={
            'fans': test_fan_array,
            'timestamp': time.time()
        },
        timeout=5
    )

    print(f"同步状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果: {result}")
    else:
        print(f"同步失败: {response.text}")

if __name__ == '__main__':
    print("发送测试风扇数据到Web端...")
    sync_test_data()
    print("\n请检查Web端 http://localhost:5174/fan 是否显示同步的数据")
    print("应该看到中心红色，边缘蓝色的风扇阵列")
