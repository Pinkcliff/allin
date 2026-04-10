# -*- coding: utf-8 -*-
"""
====================================================================
LuMo动捕数据 Redis存储客户端
====================================================================
功能：
  1. 高性能批量写入帧数据
  2. 实时状态查询
  3. 历史轨迹回放
  4. 数据流消费
  5. 统计分析
====================================================================

依赖安装：
  pip install redis

使用示例：
  from redis_storage_client import LuMoRedisClient

  client = LuMoRedisClient(host='localhost', db=1)
  client.connect()
  client.store_frame(frame)
  client.close()
===================================================================="""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import redis
    from redis.cluster import RedisCluster
except ImportError:
    logger.error("请安装redis库: pip install redis")
    raise


class LuMoRedisClient:
    """
    LuMo动捕数据Redis存储客户端
    """

    def __init__(self, host='localhost', port=6379, db=1, password=None,
                 decode_responses=True, max_connections=50, use_cluster=False):
        """
        初始化Redis客户端

        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号（默认1）
            password: Redis密码
            decode_responses: 是否解码响应
            max_connections: 连接池最大连接数
            use_cluster: 是否使用Redis集群
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.use_cluster = use_cluster

        # 连接池配置
        self.pool = None
        self.client = None

        # 会话信息
        self.session_id = None
        self.session_start_time = None
        self.total_frames = 0

        # 性能统计
        self.last_write_time = None
        self.write_count = 0

        # 数据保留策略
        self.HOT_DATA_TTL = 3600           # 热数据1小时
        self.HISTORY_TTL = 86400 * 7       # 历史数据7天
        self.STREAM_MAX_LEN = 100000       # Stream最大长度

    def connect(self) -> bool:
        """连接Redis服务器"""
        try:
            if self.use_cluster:
                self.client = RedisCluster(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    decode_responses=self.decode_responses,
                    skip_full_coverage_check=True,
                )
            else:
                self.pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=50,
                    decode_responses=self.decode_responses,
                )
                self.client = redis.Redis(connection_pool=self.pool)

            # 测试连接
            self.client.ping()
            logger.info(f"成功连接到Redis: {self.host}:{self.port} DB:{self.db}")

            # 初始化会话
            self._init_session()
            return True

        except Exception as e:
            logger.error(f"连接Redis失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        try:
            if self.client:
                # 更新会话结束时间
                if self.session_id:
                    self.client.hset("session:info", "end_time", datetime.now().isoformat())
                    self.client.hset("session:info", "status", "stopped")
                self.client.close()
            if self.pool:
                self.pool.close()
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭连接时出错: {e}")

    def _init_session(self):
        """初始化会话信息"""
        self.session_id = f"session_{int(time.time())}"
        self.session_start_time = datetime.now()

        session_info = {
            "session_id": self.session_id,
            "start_time": self.session_start_time.isoformat(),
            "status": "running",
            "total_frames": "0",
            "db_index": str(self.db),
        }

        self.client.hset("session:info", mapping=session_info)
        logger.info(f"会话已初始化: {self.session_id}")

    def store_frame(self, frame) -> bool:
        """
        存储一帧数据到Redis

        Args:
            frame: LusterFrameStruct_pb2.Frame 对象

        Returns:
            bool: 是否存储成功
        """
        try:
            pipe = self.client.pipeline()

            frame_id = frame.FrameId
            timestamp = frame.TimeStamp

            # ========== 1. 存储帧完整数据 ==========
            frame_key = f"frame:{frame_id}"

            # 基础信息
            base_fields = self._get_frame_base_fields(frame)
            pipe.hset(frame_key, mapping=base_fields)

            # 标记数据
            for marker in frame.markers:
                marker_fields = self._get_marker_fields(marker)
                pipe.hset(frame_key, mapping=marker_fields)

                # 更新标记最新状态
                marker_latest_key = f"marker:{marker.Id}:latest"
                pipe.hset(marker_latest_key, mapping={
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "id": marker.Id,
                    "name": marker.Name,
                    "x": marker.X,
                    "y": marker.Y,
                    "z": marker.Z,
                })

                # 添加到标记历史（使用JSON序列化）
                marker_history_key = f"marker:{marker.Id}:history"
                marker_data = json.dumps({
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "x": marker.X,
                    "y": marker.Y,
                    "z": marker.Z,
                })
                pipe.zadd(marker_history_key, {marker_data: timestamp})
                pipe.expire(marker_history_key, self.HISTORY_TTL)

            # 刚体数据
            rigidbody_ids = []
            for rigid in frame.rigidBodys:
                rigidbody_ids.append(rigid.Id)
                rigid_fields = self._get_rigidbody_fields(rigid)

                # 添加到帧数据
                for k, v in rigid_fields.items():
                    pipe.hset(frame_key, k, v)

                # 更新刚体最新状态
                rigid_latest_key = f"rigidbody:{rigid.Id}:latest"
                latest_fields = self._get_rigidbody_latest_fields(frame, rigid)
                pipe.hset(rigid_latest_key, mapping=latest_fields)

                # 添加到刚体历史
                if rigid.IsTrack:
                    rigid_history_key = f"rigidbody:{rigid.Id}:history"
                    history_data = json.dumps({
                        "frame_id": frame_id,
                        "timestamp": timestamp,
                        "x": rigid.X,
                        "y": rigid.Y,
                        "z": rigid.Z,
                        "qx": rigid.qx,
                        "qy": rigid.qy,
                        "qz": rigid.qz,
                        "qw": rigid.qw,
                        "quality": rigid.QualityGrade,
                    })
                    pipe.zadd(rigid_history_key, {history_data: timestamp})
                    pipe.expire(rigid_history_key, self.HISTORY_TTL)

            # 骨骼数据
            skeleton_ids = []
            for skeleton in frame.skeletons:
                skeleton_ids.append(skeleton.Id)
                skeleton_fields = self._get_skeleton_fields(skeleton)
                for k, v in skeleton_fields.items():
                    pipe.hset(frame_key, k, v)

                # 更新骨骼最新状态
                skeleton_latest_key = f"skeleton:{skeleton.Id}:latest"
                pipe.hset(skeleton_latest_key, mapping={
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "id": skeleton.Id,
                    "name": skeleton.Name,
                    "is_track": int(skeleton.IsTrack),
                })

            # 时码数据
            timecode_fields = {
                "timecode_hours": frame.timeCode.mHours,
                "timecode_minutes": frame.timeCode.mMinutes,
                "timecode_seconds": frame.timeCode.mSeconds,
                "timecode_frames": frame.timeCode.mFrames,
                "timecode_subframe": frame.timeCode.mSubFrame,
            }
            pipe.hset(frame_key, mapping=timecode_fields)

            # 设置过期时间
            pipe.expire(frame_key, self.HOT_DATA_TTL)

            # ========== 2. 更新索引 ==========
            # 时间线索引
            pipe.zadd("frames:timeline", {str(frame_id): timestamp})

            # 时间戳索引
            ts_index_key = f"idx:frames:{timestamp}"
            pipe.set(ts_index_key, frame_id)
            pipe.expire(ts_index_key, self.HOT_DATA_TTL)

            # 帧内实体索引
            if rigidbody_ids:
                pipe.sadd(f"frame:{frame_id}:rigidbodies", *rigidbody_ids)
            if frame.markers:
                marker_ids = [m.Id for m in frame.markers]
                pipe.sadd(f"frame:{frame_id}:markers", *marker_ids)
            if skeleton_ids:
                pipe.sadd(f"frame:{frame_id}:skeletons", *skeleton_ids)

            # ========== 3. 更新全局状态 ==========
            pipe.set("latest:frame", frame_id)

            # ========== 4. 添加到实时数据流 ==========
            stream_entry = {
                "frame_id": str(frame_id),
                "timestamp": str(timestamp),
                "camera_sync": str(frame.uCameraSyncTime),
                "broadcast": str(frame.uBroadcastTime),
                "rigidbody_count": str(len(frame.rigidBodys)),
                "marker_count": str(len(frame.markers)),
                "skeleton_count": str(len(frame.skeletons)),
            }
            pipe.xadd("stream:frames", stream_entry, maxlen=self.STREAM_MAX_LEN)

            # ========== 5. 执行批量操作 ==========
            pipe.execute()

            # ========== 6. 更新统计 ==========
            self.total_frames += 1
            self._update_stats(frame)

            return True

        except Exception as e:
            logger.error(f"存储帧数据失败: {e}")
            return False

    def _update_stats(self, frame):
        """更新统计信息"""
        try:
            # 计算帧率
            now = time.time()
            if self.last_write_time:
                elapsed = now - self.last_write_time
                fps = 1.0 / elapsed if elapsed > 0 else 0
            else:
                fps = 0
            self.last_write_time = now

            # 计算平均质量
            total_quality = 0
            quality_count = 0
            for rigid in frame.rigidBodys:
                if rigid.IsTrack:
                    total_quality += rigid.QualityGrade
                    quality_count += 1
            avg_quality = total_quality / quality_count if quality_count > 0 else 0

            stats = {
                "fps": f"{fps:.2f}",
                "avg_quality": f"{avg_quality:.2f}",
                "frames_received": str(self.total_frames),
                "last_update": datetime.now().isoformat(),
            }

            self.client.hset("session:stats", mapping=stats)
            self.client.hset("session:info", "total_frames", str(self.total_frames))

        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")

    # ==================== 数据字段生成方法 ====================

    def _get_frame_base_fields(self, frame) -> Dict[str, Any]:
        """获取帧基础字段"""
        return {
            "frame_id": frame.FrameId,
            "timestamp": frame.TimeStamp,
            "camera_sync_time": frame.uCameraSyncTime,
            "broadcast_time": frame.uBroadcastTime,
        }

    def _get_marker_fields(self, marker) -> Dict[str, Any]:
        """获取标记点字段"""
        prefix = f"marker:{marker.Id}"
        return {
            f"{prefix}:id": marker.Id,
            f"{prefix}:name": marker.Name,
            f"{prefix}:x": marker.X,
            f"{prefix}:y": marker.Y,
            f"{prefix}:z": marker.Z,
        }

    def _get_rigidbody_fields(self, rigid) -> Dict[str, Any]:
        """获取刚体字段"""
        prefix = f"rigidbody:{rigid.Id}"
        fields = {
            f"{prefix}:id": rigid.Id,
            f"{prefix}:name": rigid.Name,
            f"{prefix}:is_track": int(rigid.IsTrack),
            f"{prefix}:x": rigid.X,
            f"{prefix}:y": rigid.Y,
            f"{prefix}:z": rigid.Z,
            f"{prefix}:qx": rigid.qx,
            f"{prefix}:qy": rigid.qy,
            f"{prefix}:qz": rigid.qz,
            f"{prefix}:qw": rigid.qw,
            f"{prefix}:quality": rigid.QualityGrade,
        }

        if rigid.IsTrack:
            fields.update({
                f"{prefix}:speed": rigid.speeds.fSpeed,
                f"{prefix}:speed_x": rigid.speeds.XfSpeed,
                f"{prefix}:speed_y": rigid.speeds.YfSpeed,
                f"{prefix}:speed_z": rigid.speeds.ZfSpeed,
                f"{prefix}:accel": rigid.acceleratedSpeeds.fAcceleratedSpeed,
                f"{prefix}:accel_x": rigid.acceleratedSpeeds.XfAcceleratedSpeed,
                f"{prefix}:accel_y": rigid.acceleratedSpeeds.YfAcceleratedSpeed,
                f"{prefix}:accel_z": rigid.acceleratedSpeeds.ZfAcceleratedSpeed,
                f"{prefix}:euler_x": rigid.eulerAngle.X,
                f"{prefix}:euler_y": rigid.eulerAngle.Y,
                f"{prefix}:euler_z": rigid.eulerAngle.Z,
                f"{prefix}:angular_x": rigid.palstance.fXPalstance,
                f"{prefix}:angular_y": rigid.palstance.fYPalstance,
                f"{prefix}:angular_z": rigid.palstance.fZPalstance,
            })

        return fields

    def _get_rigidbody_latest_fields(self, frame, rigid) -> Dict[str, Any]:
        """获取刚体最新状态字段"""
        return {
            "frame_id": frame.FrameId,
            "timestamp": frame.TimeStamp,
            "id": rigid.Id,
            "name": rigid.Name,
            "is_track": int(rigid.IsTrack),
            "x": rigid.X,
            "y": rigid.Y,
            "z": rigid.Z,
            "qx": rigid.qx,
            "qy": rigid.qy,
            "qz": rigid.qz,
            "qw": rigid.qw,
            "quality": rigid.QualityGrade,
            "speed": rigid.speeds.fSpeed if rigid.IsTrack else 0,
            "speed_x": rigid.speeds.XfSpeed if rigid.IsTrack else 0,
            "speed_y": rigid.speeds.YfSpeed if rigid.IsTrack else 0,
            "speed_z": rigid.speeds.ZfSpeed if rigid.IsTrack else 0,
        }

    def _get_skeleton_fields(self, skeleton) -> Dict[str, Any]:
        """获取骨骼字段"""
        prefix = f"skeleton:{skeleton.Id}"
        fields = {
            f"{prefix}:id": skeleton.Id,
            f"{prefix}:name": skeleton.Name,
            f"{prefix}:is_track": int(skeleton.IsTrack),
            f"{prefix}:robot_name": skeleton.RobotName,
        }

        for bone in skeleton.skeletonBones:
            bone_prefix = f"{prefix}:bone:{bone.Id}"
            fields.update({
                f"{bone_prefix}:id": bone.Id,
                f"{bone_prefix}:name": bone.Name,
                f"{bone_prefix}:x": bone.X,
                f"{bone_prefix}:y": bone.Y,
                f"{bone_prefix}:z": bone.Z,
            })

        return fields

    # ==================== 查询方法 ====================

    def get_latest_frame_id(self) -> Optional[int]:
        """获取最新帧ID"""
        try:
            result = self.client.get("latest:frame")
            return int(result) if result else None
        except Exception as e:
            logger.error(f"获取最新帧ID失败: {e}")
            return None

    def get_frame_data(self, frame_id: int) -> Optional[Dict]:
        """获取指定帧的完整数据"""
        try:
            frame_key = f"frame:{frame_id}"
            data = self.client.hgetall(frame_key)
            return data if data else None
        except Exception as e:
            logger.error(f"获取帧数据失败: {e}")
            return None

    def get_rigidbody_latest(self, rigid_id: int) -> Optional[Dict]:
        """获取刚体最新状态"""
        try:
            key = f"rigidbody:{rigid_id}:latest"
            data = self.client.hgetall(key)
            return data if data else None
        except Exception as e:
            logger.error(f"获取刚体最新状态失败: {e}")
            return None

    def get_rigidbody_trajectory(self, rigid_id: int, start_time: float = None,
                                 end_time: float = None, limit: int = 1000) -> List[Dict]:
        """
        获取刚体历史轨迹

        Args:
            rigid_id: 刚体ID
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 返回数量限制

        Returns:
            List[Dict]: 轨迹点列表
        """
        try:
            key = f"rigidbody:{rigid_id}:history"
            results = self.client.zrangebyscore(
                key,
                min=start_time or '-inf',
                max=end_time or '+inf',
                start=0,
                num=limit,
                withscores=True
            )

            trajectory = []
            for data, score in results:
                point = json.loads(data)
                point['timestamp_redis'] = score
                trajectory.append(point)

            return trajectory

        except Exception as e:
            logger.error(f"获取刚体轨迹失败: {e}")
            return []

    def get_frames_by_timerange(self, start_time: float, end_time: float,
                                limit: int = 1000) -> List[Tuple[int, float]]:
        """
        获取时间范围内的帧

        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 返回数量限制

        Returns:
            List[Tuple[frame_id, timestamp]]: 帧ID和时间戳列表
        """
        try:
            results = self.client.zrangebyscore(
                "frames:timeline",
                min=start_time,
                max=end_time,
                start=0,
                num=limit,
                withscores=True
            )
            return [(int(frame_id), score) for frame_id, score in results]

        except Exception as e:
            logger.error(f"获取时间范围帧失败: {e}")
            return []

    def get_session_info(self) -> Dict:
        """获取会话信息"""
        try:
            return self.client.hgetall("session:info")
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return {}

    def get_session_stats(self) -> Dict:
        """获取会话统计"""
        try:
            return self.client.hgetall("session:stats")
        except Exception as e:
            logger.error(f"获取会话统计失败: {e}")
            return {}

    # ==================== Stream消费方法 ====================

    def create_consumer_group(self, stream_name: str, group_name: str,
                              consumer_name: str = None):
        """
        创建消费者组

        Args:
            stream_name: Stream名称
            group_name: 组名称
            consumer_name: 消费者名称
        """
        try:
            try:
                self.client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
                logger.info(f"消费者组创建成功: {group_name}")
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(f"消费者组已存在: {group_name}")
                else:
                    raise
        except Exception as e:
            logger.error(f"创建消费者组失败: {e}")

    def read_from_stream(self, stream_name: str, group_name: str,
                         consumer_name: str, count: int = 10,
                         block: int = 1000) -> List:
        """
        从Stream读取消息

        Args:
            stream_name: Stream名称
            group_name: 组名称
            consumer_name: 消费者名称
            count: 读取数量
            block: 阻塞时间(毫秒)

        Returns:
            List: 消息列表
        """
        try:
            messages = self.client.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count,
                block=block
            )
            return messages
        except Exception as e:
            logger.error(f"读取Stream失败: {e}")
            return []

    def ack_stream_message(self, stream_name: str, group_name: str, message_id: str):
        """确认消息已处理"""
        try:
            self.client.xack(stream_name, group_name, message_id)
        except Exception as e:
            logger.error(f"确认消息失败: {e}")

    # ==================== 数据清理方法 ====================

    def cleanup_old_frames(self, keep_seconds: int = 3600):
        """
        清理旧帧数据

        Args:
            keep_seconds: 保留时间(秒)
        """
        try:
            cutoff_time = time.time() - keep_seconds
            # 获取过期帧
            old_frames = self.client.zrangebyscore(
                "frames:timeline",
                min='-inf',
                max=cutoff_time
            )

            count = 0
            pipe = self.client.pipeline()
            for frame_id in old_frames:
                # 删除帧数据
                pipe.delete(f"frame:{frame_id}")
                # 删除实体索引
                pipe.delete(f"frame:{frame_id}:rigidbodies")
                pipe.delete(f"frame:{frame_id}:markers")
                pipe.delete(f"frame:{frame_id}:skeletons")
                # 从时间线移除
                pipe.zrem("frames:timeline", frame_id)
                count += 1

                # 批量执行
                if count % 1000 == 0:
                    pipe.execute()
                    pipe = self.client.pipeline()

            pipe.execute()
            logger.info(f"清理了 {count} 条旧帧数据")

        except Exception as e:
            logger.error(f"清理旧帧数据失败: {e}")


# ==================== 集成到PythonSample.py ====================

def create_redis_integrated_sample():
    """
    生成集成Redis的PythonSample.py代码

    将此代码添加到PythonSample.py中使用
    """

    return '''
# ============ Redis存储集成代码 ============
# 在PythonSample.py中添加以下代码

import sys
sys.path.append(os.path.dirname(__file__))
from redis_storage_client import LuMoRedisClient

# 创建Redis客户端
redis_client = LuMoRedisClient(
    host='localhost',
    port=6379,
    db=1,
    password=None  # 如果有密码则填写
)

# 连接Redis
if not redis_client.connect():
    print("警告: Redis连接失败，数据将不会被存储到Redis")
    redis_client = None

# 在数据接收循环中添加Redis存储
try:
    while True:
        # ... 原有的接收逻辑 ...

        frame = LuMoSDKClient.ReceiveData(0)
        if frame is None:
            continue

        # 原有的CSV写入逻辑
        # ...

        # 新增：同时存储到Redis
        if redis_client:
            redis_client.store_frame(frame)

except KeyboardInterrupt:
    print("\\n用户手动中断程序...")
finally:
    # 关闭Redis连接
    if redis_client:
        redis_client.close()

    # 原有的清理逻辑
    # ...


# ============ Redis查询示例 ============
# 可以在另一个Python脚本中使用

from redis_storage_client import LuMoRedisClient

# 连接
client = LuMoRedisClient(host='localhost', db=1)
client.connect()

# 1. 获取最新帧ID
latest_id = client.get_latest_frame_id()
print(f"最新帧ID: {latest_id}")

# 2. 获取刚体最新状态
rigid_state = client.get_rigidbody_latest(rigid_id=1)
print(f"刚体状态: {rigid_state}")

# 3. 获取历史轨迹（最近10秒）
import time
end = time.time() * 1000  # 转换为毫秒
start = end - 10000
trajectory = client.get_rigidbody_trajectory(rigid_id=1, start_time=start, end_time=end)
print(f"轨迹点数量: {len(trajectory)}")

# 4. 获取会话统计
stats = client.get_session_stats()
print(f"帧率: {stats.get('fps')}")
print(f"总帧数: {stats.get('frames_received')}")

client.close()
'''
