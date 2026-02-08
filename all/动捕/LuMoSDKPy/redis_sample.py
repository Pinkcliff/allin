# -*- coding: utf-8 -*-
"""
====================================================================
Redis存储集成示例 - 完整可运行版本
====================================================================
这是将原始的PythonSample.py与Redis存储集成的完整版本

功能：
  1. 接收LuMo动捕数据
  2. 同时保存到CSV文件和Redis
  3. 支持实时查询最新状态
  4. 支持历史轨迹回放

使用方法：
  1. 确保Redis服务已启动
  2. 修改下方的IP地址配置
  3. 运行: python redis_sample.py

查询数据：
  使用 redis_query.py 或 redis-cli 查询存储的数据
===================================================================="""

import LuMoSDKClient
import csv
from datetime import datetime
import time
import sys
import os

# 添加当前目录到路径，以便导入redis_storage_client
sys.path.append(os.path.dirname(__file__))

try:
    from redis_storage_client import LuMoRedisClient
    REDIS_AVAILABLE = True
except ImportError:
    print("警告: 无法导入redis_storage_client，请确保已安装redis库")
    print("安装命令: pip install redis")
    REDIS_AVAILABLE = False

# ==================== 配置参数 ====================

# LuMo数据源配置
LUMO_IP = "192.168.3.24"

# Redis配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1
REDIS_PASSWORD = None  # 如果有密码则填写

# 数据超时设置（秒）
DATA_TIMEOUT = 5

# CSV文件配置
CSV_ENABLED = True  # 是否同时保存到CSV


# ==================== 主程序 ====================

def main():
    """主函数"""

    print("=" * 60)
    print("LuMo动捕数据存储系统")
    print("=" * 60)

    # ==================== 初始化Redis客户端 ====================
    redis_client = None

    if REDIS_AVAILABLE:
        print("\n[1/3] 连接Redis...")
        redis_client = LuMoRedisClient(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD
        )

        if redis_client.connect():
            print(f"  ✓ Redis连接成功: {REDIS_HOST}:{REDIS_PORT} DB:{REDIS_DB}")
        else:
            print(f"  ✗ Redis连接失败，数据将不会被存储到Redis")
            redis_client = None
    else:
        print("\n[1/3] Redis不可用，跳过Redis存储")

    # ==================== 初始化CSV文件 ====================
    csv_file = None
    writer = None

    if CSV_ENABLED:
        print("\n[2/3] 初始化CSV文件...")
        csv_filename = f"LuMo_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_file = open(csv_filename, 'w', newline='', encoding='utf-8-sig')
        writer = csv.writer(csv_file)

        # 写入表头
        headers = [
            '帧ID', '时间戳', '相机同步时间', '数据广播时间',
            # 标记1-3
            '标记1_ID', '标记1_名称', '标记1_X', '标记1_Y', '标记1_Z',
            '标记2_ID', '标记2_名称', '标记2_X', '标记2_Y', '标记2_Z',
            '标记3_ID', '标记3_名称', '标记3_X', '标记3_Y', '标记3_Z',
            # 刚体1
            '刚体1_ID', '刚体1_名称', '刚体1_追踪状态', '刚体1_X', '刚体1_Y', '刚体1_Z',
            '刚体1_qx', '刚体1_qy', '刚体1_qz', '刚体1_qw', '刚体1_质量等级',
        ]
        writer.writerow(headers)
        print(f"  ✓ CSV文件已创建: {csv_filename}")

    # ==================== 连接LuMo数据源 ====================
    print("\n[3/3] 连接LuMo数据源...")
    print(f"  目标IP: {LUMO_IP}")

    try:
        LuMoSDKClient.Init()
        LuMoSDKClient.Connnect(LUMO_IP)
        print(f"  ✓ LuMo连接成功")
    except Exception as e:
        print(f"  ✗ LuMo连接失败: {e}")
        if redis_client:
            redis_client.close()
        if csv_file:
            csv_file.close()
        return

    # ==================== 开始接收数据 ====================
    print("\n" + "=" * 60)
    print("开始接收数据...")
    print("=" * 60)
    print(f"数据超时设置: {DATA_TIMEOUT}秒无数据将自动退出")
    print(f"Redis存储: {'启用' if redis_client else '禁用'}")
    print(f"CSV存储: {'启用' if CSV_ENABLED else '禁用'}")
    print("=" * 60)

    frame_count = 0
    last_data_time = time.time()
    redis_store_count = 0
    redis_fail_count = 0

    try:
        while True:
            # 检查是否超时
            current_time = time.time()
            if current_time - last_data_time > DATA_TIMEOUT:
                print(f"\n!!! 超过 {DATA_TIMEOUT} 秒未收到数据，发送方可能已停止 !!!")
                print("程序自动退出...")
                break

            # 接收帧数据
            frame = LuMoSDKClient.ReceiveData(0)  # 0: 阻塞接收
            if frame is None:
                continue

            # 收到数据，更新时间戳
            last_data_time = time.time()
            frame_count += 1

            FrameID = frame.FrameId

            # 每秒打印一次状态
            if frame_count % 100 == 0:
                redis_status = f"Redis成功: {redis_store_count} 失败: {redis_fail_count}" if redis_client else "Redis: 禁用"
                print(f"[{frame_count:5d}帧] 帧ID:{FrameID} {redis_status}")

            # ==================== 存储到Redis ====================
            if redis_client:
                if redis_client.store_frame(frame):
                    redis_store_count += 1
                else:
                    redis_fail_count += 1

            # ==================== 存储到CSV ====================
            if CSV_ENABLED and writer:
                # 收集数据
                row_data = [
                    frame.FrameId,
                    frame.TimeStamp,
                    frame.uCameraSyncTime,
                    frame.uBroadcastTime,
                ]

                # 标记数据（最多3个）
                markers_list = list(frame.markers)
                for i in range(3):
                    if i < len(markers_list):
                        m = markers_list[i]
                        row_data.extend([m.Id, m.Name, m.X, m.Y, m.Z])
                    else:
                        row_data.extend(['', '', '', '', ''])

                # 刚体数据（最多1个）
                rigids_list = list(frame.rigidBodys)
                if len(rigids_list) > 0:
                    r = rigids_list[0]
                    row_data.extend([
                        r.Id, r.Name, int(r.IsTrack),
                        r.X, r.Y, r.Z,
                        r.qx, r.qy, r.qz, r.qw, r.QualityGrade,
                    ])
                else:
                    row_data.extend(['', '', '', '', '', '', '', '', '', '', '', ''])

                # 写入CSV
                writer.writerow(row_data)

    except KeyboardInterrupt:
        print("\n\n用户手动中断程序...")

    except Exception as e:
        print(f"\n\n程序异常: {e}")

    finally:
        # ==================== 清理资源 ====================
        print("\n" + "=" * 60)
        print("正在清理资源...")
        print("=" * 60)

        # 关闭LuMo连接
        LuMoSDKClient.Close()
        print("✓ LuMo连接已关闭")

        # 关闭Redis连接
        if redis_client:
            redis_client.close()
            print(f"✓ Redis连接已关闭 (成功存储 {redis_store_count} 帧)")

        # 关闭CSV文件
        if csv_file:
            csv_file.close()
            print(f"✓ CSV文件已关闭 (共 {frame_count} 帧)")

        print("\n" + "=" * 60)
        print("程序已正常退出")
        print("=" * 60)


if __name__ == "__main__":
    main()
