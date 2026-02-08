# -*- coding: utf-8 -*-
"""
====================================================================
Redis数据查询工具
====================================================================

用于查询存储在Redis中的LuMo动捕数据

功能：
  1. 查看会话信息
  2. 查看最新帧数据
  3. 查看刚体最新状态
  4. 查看历史轨迹
  5. 实时监控数据流
  6. 数据统计分析

使用方法：
  python redis_query.py

===================================================================="""

import sys
import os
import time
from datetime import datetime

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

try:
    from redis_storage_client import LuMoRedisClient
except ImportError:
    print("错误: 无法导入redis_storage_client")
    print("请确保已安装redis库: pip install redis")
    sys.exit(1)


class RedisQueryTool:
    """Redis查询工具"""

    def __init__(self, host='localhost', port=6379, db=1, password=None):
        self.client = LuMoRedisClient(
            host=host,
            port=port,
            db=db,
            password=password
        )
        self.connected = False

    def connect(self):
        """连接Redis"""
        print("连接Redis...")
        if self.client.connect():
            self.connected = True
            print(f"✓ 连接成功: {self.client.host}:{self.client.port} DB:{self.client.db}\n")
            return True
        else:
            print("✗ 连接失败\n")
            return False

    def close(self):
        """关闭连接"""
        if self.connected:
            self.client.close()

    # ==================== 查询方法 ====================

    def show_session_info(self):
        """显示会话信息"""
        print("=" * 60)
        print("【会话信息】")
        print("=" * 60)

        info = self.client.get_session_info()
        if info:
            print(f"会话ID:     {info.get('session_id', 'N/A')}")
            print(f"开始时间:    {info.get('start_time', 'N/A')}")
            print(f"结束时间:    {info.get('end_time', 'N/A')}")
            print(f"状态:        {info.get('status', 'N/A')}")
            print(f"总帧数:      {info.get('total_frames', 'N/A')}")
        else:
            print("暂无会话信息")

        print()

    def show_session_stats(self):
        """显示会话统计"""
        print("=" * 60)
        print("【会话统计】")
        print("=" * 60)

        stats = self.client.get_session_stats()
        if stats:
            print(f"帧率(FPS):           {stats.get('fps', 'N/A')}")
            print(f"平均质量:            {stats.get('avg_quality', 'N/A')}")
            print(f"已接收帧数:          {stats.get('frames_received', 'N/A')}")
            print(f"丢帧数:              {stats.get('frames_dropped', 'N/A')}")
            print(f"接收字节数:          {stats.get('bytes_received', 'N/A')}")
            print(f"最后更新:            {stats.get('last_update', 'N/A')}")
        else:
            print("暂无统计数据")

        print()

    def show_latest_frame(self):
        """显示最新帧信息"""
        print("=" * 60)
        print("【最新帧信息】")
        print("=" * 60)

        frame_id = self.client.get_latest_frame_id()
        if frame_id is None:
            print("暂无帧数据")
            print()
            return

        print(f"最新帧ID: {frame_id}")

        frame_data = self.client.get_frame_data(frame_id)
        if frame_data:
            print(f"时间戳:    {frame_data.get('timestamp', 'N/A')}")
            print(f"相机同步:  {frame_data.get('camera_sync_time', 'N/A')}")
            print(f"广播时间:  {frame_data.get('broadcast_time', 'N/A')}")

            # 统计实体数量
            rigid_count = sum(1 for k in frame_data.keys() if k.startswith('rigidbody:') and k.endswith(':id'))
            marker_count = sum(1 for k in frame_data.keys() if k.startswith('marker:') and k.endswith(':id'))

            print(f"刚体数量:  {rigid_count}")
            print(f"标记数量:  {marker_count}")
        else:
            print("无法获取帧数据")

        print()

    def show_rigidbodies(self):
        """显示所有刚体最新状态"""
        print("=" * 60)
        print("【刚体状态列表】")
        print("=" * 60)
        print(f"{'ID':<6} {'名称':<20} {'追踪':<6} {'位置(X,Y,Z)':<30} {'质量':<6}")
        print("-" * 60)

        # 从最新帧获取刚体列表
        frame_id = self.client.get_latest_frame_id()
        if not frame_id:
            print("暂无数据")
            print()
            return

        frame_data = self.client.get_frame_data(frame_id)
        if not frame_data:
            print("无法获取帧数据")
            print()
            return

        # 提取刚体信息
        rigid_ids = set()
        for key in frame_data.keys():
            if key.startswith('rigidbody:') and key.endswith(':id'):
                rigid_id = frame_data[key]
                rigid_ids.add(rigid_id)

        # 显示每个刚体的最新状态
        for rigid_id in sorted(rigid_ids):
            latest = self.client.get_rigidbody_latest(int(rigid_id))
            if latest:
                is_track = "是" if latest.get('is_track') == '1' else "否"
                position = f"({latest.get('x', 'N/A'):.2f}, {latest.get('y', 'N/A'):.2f}, {latest.get('z', 'N/A'):.2f})"
                quality = latest.get('quality', 'N/A')

                print(f"{rigid_id:<6} {latest.get('name', 'N/A'):<20} {is_track:<6} {position:<30} {quality:<6}")

        print()

    def show_rigidbody_detail(self, rigid_id: int):
        """显示刚体详细信息"""
        print("=" * 60)
        print(f"【刚体详情 - ID: {rigid_id}】")
        print("=" * 60)

        latest = self.client.get_rigidbody_latest(rigid_id)
        if not latest:
            print(f"刚体 {rigid_id} 不存在或无数据")
            print()
            return

        print(f"{'属性':<20} {'值'}")
        print("-" * 60)

        fields = [
            ("ID", latest.get('id')),
            ("名称", latest.get('name')),
            ("帧ID", latest.get('frame_id')),
            ("时间戳", latest.get('timestamp')),
            ("追踪状态", "是" if latest.get('is_track') == '1' else "否"),
            ("", ""),
            ("位置 X", f"{float(latest.get('x', 0)):.4f}"),
            ("位置 Y", f"{float(latest.get('y', 0)):.4f}"),
            ("位置 Z", f"{float(latest.get('z', 0)):.4f}"),
            ("", ""),
            ("四元数 qx", f"{float(latest.get('qx', 0)):.6f}"),
            ("四元数 qy", f"{float(latest.get('qy', 0)):.6f}"),
            ("四元数 qz", f"{float(latest.get('qz', 0)):.6f}"),
            ("四元数 qw", f"{float(latest.get('qw', 0)):.6f}"),
            ("", ""),
            ("速度", f"{float(latest.get('speed', 0)):.4f}"),
            ("速度 X", f"{float(latest.get('speed_x', 0)):.4f}"),
            ("速度 Y", f"{float(latest.get('speed_y', 0)):.4f}"),
            ("速度 Z", f"{float(latest.get('speed_z', 0)):.4f}"),
            ("", ""),
            ("加速度", f"{float(latest.get('accel', 0)):.4f}"),
            ("加速度 X", f"{float(latest.get('accel_x', 0)):.4f}"),
            ("加速度 Y", f"{float(latest.get('accel_y', 0)):.4f}"),
            ("加速度 Z", f"{float(latest.get('accel_z', 0)):.4f}"),
            ("", ""),
            ("质量等级", latest.get('quality')),
        ]

        for label, value in fields:
            if label:
                print(f"{label:<20} {value}")
            else:
                print()

        print()

    def show_trajectory(self, rigid_id: int, seconds: int = 10):
        """显示刚体历史轨迹"""
        print("=" * 60)
        print(f"【刚体轨迹 - ID: {rigid_id}】(最近{seconds}秒)")
        print("=" * 60)

        end_time = time.time() * 1000  # 转换为毫秒
        start_time = end_time - (seconds * 1000)

        trajectory = self.client.get_rigidbody_trajectory(
            rigid_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        if not trajectory:
            print(f"刚体 {rigid_id} 在最近 {seconds} 秒内无轨迹数据")
            print()
            return

        print(f"{'帧ID':<10} {'时间戳':<15} {'位置(X,Y,Z)':<35} {'四元数(w)'}")
        print("-" * 60)

        for point in trajectory:
            frame_id = point.get('frame_id', 'N/A')
            timestamp = point.get('timestamp', 'N/A')
            position = f"({point['x']:.2f}, {point['y']:.2f}, {point['z']:.2f})"
            qw = f"{point.get('qw', 0):.4f}"

            print(f"{frame_id:<10} {timestamp:<15} {position:<35} {qw}")

        print(f"\n共 {len(trajectory)} 个轨迹点")
        print()

    def monitor_stream(self, duration: int = 30):
        """监控实时数据流"""
        print("=" * 60)
        print(f"【实时数据流监控】(监控{duration}秒)")
        print("=" * 60)
        print("按 Ctrl+C 提前退出\n")

        # 创建消费者组
        stream_name = "stream:frames"
        group_name = "monitor_group"
        consumer_name = f"monitor_{int(time.time())}"

        self.client.create_consumer_group(stream_name, group_name, consumer_name)

        start_time = time.time()
        frame_count = 0

        try:
            while time.time() - start_time < duration:
                messages = self.client.read_from_stream(
                    stream_name,
                    group_name,
                    consumer_name,
                    count=10,
                    block=1000
                )

                if messages:
                    for stream, entries in messages:
                        for msg_id, data in entries:
                            frame_count += 1
                            frame_id = data.get(b'frame_id', b'N/A').decode()
                            timestamp = data.get(b'timestamp', b'N/A').decode()
                            rb_count = data.get(b'rigidbody_count', b'0').decode()
                            marker_count = data.get(b'marker_count', b'0').decode()

                            print(f"[{frame_count:4d}] 帧ID:{frame_id} 时间:{timestamp} "
                                  f"刚体:{rb_count} 标记:{marker_count}")

                            # 确认消息
                            self.client.ack_stream_message(stream_name, group_name, msg_id)

        except KeyboardInterrupt:
            print("\n监控已手动停止")

        print(f"\n共接收 {frame_count} 帧数据")
        print()

    def show_data_summary(self):
        """显示数据概览"""
        print("=" * 60)
        print("【数据概览】")
        print("=" * 60)

        # 获取Redis数据库信息
        try:
            info = self.client.client.info('db1')
            keys = self.client.client.dbsize()
            print(f"DB1 键数量: {keys}")

            # 获取时间线范围
            timeline_range = self.client.client.zrange("frames:timeline", 0, 0, withscores=True)
            if timeline_range:
                first_frame, first_score = timeline_range[0]
                print(f"最早帧: {first_frame.decode()} (时间戳: {first_score})")

            timeline_range = self.client.client.zrange("frames:timeline", -1, -1, withscores=True)
            if timeline_range:
                last_frame, last_score = timeline_range[0]
                print(f"最新帧: {last_frame.decode()} (时间戳: {last_score})")

        except Exception as e:
            print(f"获取数据概览失败: {e}")

        print()

    # ==================== 主菜单 ====================

    def show_menu(self):
        """显示主菜单"""
        print("=" * 60)
        print("Redis数据查询工具")
        print("=" * 60)
        print()
        print("1. 会话信息")
        print("2. 会话统计")
        print("3. 最新帧信息")
        print("4. 刚体状态列表")
        print("5. 刚体详细信息")
        print("6. 刚体历史轨迹")
        print("7. 实时数据流监控")
        print("8. 数据概览")
        print("0. 退出")
        print()


def main():
    """主函数"""
    # 连接Redis
    tool = RedisQueryTool(host='localhost', port=6379, db=1)
    if not tool.connect():
        return

    tool.show_menu()

    while True:
        try:
            choice = input("请选择操作 [0-8]: ").strip()

            if choice == '0':
                print("退出程序")
                break

            elif choice == '1':
                tool.show_session_info()

            elif choice == '2':
                tool.show_session_stats()

            elif choice == '3':
                tool.show_latest_frame()

            elif choice == '4':
                tool.show_rigidbodies()

            elif choice == '5':
                rigid_id = input("请输入刚体ID: ").strip()
                if rigid_id.isdigit():
                    tool.show_rigidbody_detail(int(rigid_id))
                else:
                    print("无效的刚体ID\n")

            elif choice == '6':
                rigid_id = input("请输入刚体ID: ").strip()
                seconds = input("查询时间范围(秒,默认10): ").strip()
                seconds = int(seconds) if seconds.isdigit() else 10

                if rigid_id.isdigit():
                    tool.show_trajectory(int(rigid_id), seconds)
                else:
                    print("无效的刚体ID\n")

            elif choice == '7':
                duration = input("监控时长(秒,默认30): ").strip()
                duration = int(duration) if duration.isdigit() else 30
                tool.monitor_stream(duration)

            elif choice == '8':
                tool.show_data_summary()

            else:
                print("无效的选择\n")

            tool.show_menu()

        except KeyboardInterrupt:
            print("\n\n退出程序")
            break

        except Exception as e:
            print(f"\n错误: {e}\n")

    tool.close()


if __name__ == "__main__":
    main()
