# -*- coding: utf-8 -*-
"""
====================================================================
LuMo动捕数据 Redis存储方案设计
====================================================================
数据库：Redis DB1
设计理念：
  1. 分层存储：实时数据、历史数据、索引分离
  2. 高频写入优化：使用Pipeline批量写入
  3. 快速查询：支持按帧ID、时间戳、实体ID查询
  4. 内存优化：热点数据保留，冷数据可归档
===================================================================="""

class RedisKeyDesign:
    """Redis键名设计规范"""

    # ==================== 基础配置 ====================
    DB_INDEX = 1

    # ==================== 全局信息 ====================
    LATEST_FRAME_ID = "latest:frame"                    # 最新帧ID (String)
    SESSION_INFO = "session:info"                       # 会话信息 (Hash)
    SESSION_STATS = "session:stats"                     # 会话统计 (Hash)

    # ==================== 帧数据存储 ====================
    # 帧完整数据 - 存储所有帧内容
    FRAME_DATA = "frame:{frame_id}"                     # Hash: 帧完整数据

    # 帧元数据 - 快速查询用
    FRAME_META = "frame:meta:{frame_id}"                # Hash: FrameId, TimeStamp, CameraSyncTime, BroadcastTime

    # 时间线索引 - 用于时间范围查询和排序
    FRAMES_TIMELINE = "frames:timeline"                 # ZSet: score=TimeStamp, member=frame_id

    # 时间戳索引 - 用于精确查找
    FRAME_TS_INDEX = "idx:frames:{timestamp}"           # String: frame_id

    # ==================== 实体最新状态 ====================
    # 用于实时获取当前状态，覆盖式更新
    RIGIDBODY_LATEST = "rigidbody:{id}:latest"          # Hash: 刚体最新完整状态
    MARKER_LATEST = "marker:{id}:latest"                # Hash: 标记最新位置
    SKELETON_LATEST = "skeleton:{id}:latest"            # Hash: 骨骼最新状态
    CUSTOM_SKELETON_LATEST = "custom_skeleton:{id}:latest"  # Hash: 自定义骨骼最新状态

    # ==================== 实体历史轨迹 ====================
    # 用于回放和分析
    RIGIDBODY_HISTORY = "rigidbody:{id}:history"        # ZSet: score=TimeStamp, member=序列化数据
    MARKER_HISTORY = "marker:{id}:history"              # ZSet: score=TimeStamp, member=序列化数据
    SKELETON_HISTORY = "skeleton:{id}:history"          # ZSet: score=TimeStamp, member=序列化数据

    # ==================== 实时数据流 ====================
    # 使用Redis Stream实现实时数据推送
    STREAM_FRAMES = "stream:frames"                     # Stream: 实时帧数据流
    STREAM_RIGIDBODY = "stream:rigidbody"               # Stream: 刚体数据流
    STREAM_ALERTS = "stream:alerts"                     # Stream: 告警事件流

    # ==================== 辅助索引 ====================
    # 帧内实体索引 - 快速查找某帧包含哪些实体
    FRAME_RIGIDBODIES = "frame:{frame_id}:rigidbodies"  # Set: 刚体ID列表
    FRAME_MARKERS = "frame:{frame_id}:markers"          # Set: 标记ID列表
    FRAME_SKELETONS = "frame:{frame_id}:skeletons"      # Set: 骨骼ID列表

    # ==================== 统计与分析 ====================
    # 质量统计
    QUALITY_STATS = "stats:quality:rigidbody:{id}"      # Hash: 质量等级统计
    POSITION_RANGE = "stats:position:rigidbody:{id}"    # Hash: 位置范围统计

    # ==================== 归档标记 ====================
    ARCHIVED_FRAMES = "archived:frames"                 # Set: 已归档的帧ID


class FrameDataStructure:
    """
    帧数据Hash字段结构
    Key: frame:{frame_id}
    Type: Hash
    """

    @staticmethod
    def get_base_fields(frame):
        """基础帧信息字段"""
        return {
            "frame_id": frame.FrameId,
            "timestamp": frame.TimeStamp,
            "camera_sync_time": frame.uCameraSyncTime,
            "broadcast_time": frame.uBroadcastTime,
            # 时间码
            "timecode_hours": frame.timeCode.mHours,
            "timecode_minutes": frame.timeCode.mMinutes,
            "timecode_seconds": frame.timeCode.mSeconds,
            "timecode_frames": frame.timeCode.mFrames,
            "timecode_subframe": frame.timeCode.mSubFrame,
        }

    @staticmethod
    def get_marker_fields(marker):
        """标记点数据字段"""
        prefix = f"marker:{marker.Id}"
        return {
            f"{prefix}:id": marker.Id,
            f"{prefix}:name": marker.Name,
            f"{prefix}:x": marker.X,
            f"{prefix}:y": marker.Y,
            f"{prefix}:z": marker.Z,
        }

    @staticmethod
    def get_rigidbody_fields(rigid):
        """刚体数据字段"""
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
            # 速度
            fields.update({
                f"{prefix}:speed": rigid.speeds.fSpeed,
                f"{prefix}:speed_x": rigid.speeds.XfSpeed,
                f"{prefix}:speed_y": rigid.speeds.YfSpeed,
                f"{prefix}:speed_z": rigid.speeds.ZfSpeed,
            })
            # 加速度
            fields.update({
                f"{prefix}:accel": rigid.acceleratedSpeeds.fAcceleratedSpeed,
                f"{prefix}:accel_x": rigid.acceleratedSpeeds.XfAcceleratedSpeed,
                f"{prefix}:accel_y": rigid.acceleratedSpeeds.YfAcceleratedSpeed,
                f"{prefix}:accel_z": rigid.acceleratedSpeeds.ZfAcceleratedSpeed,
            })
            # 欧拉角
            fields.update({
                f"{prefix}:euler_x": rigid.eulerAngle.X,
                f"{prefix}:euler_y": rigid.eulerAngle.Y,
                f"{prefix}:euler_z": rigid.eulerAngle.Z,
            })
            # 角速度
            fields.update({
                f"{prefix}:angular_x": rigid.palstance.fXPalstance,
                f"{prefix}:angular_y": rigid.palstance.fYPalstance,
                f"{prefix}:angular_z": rigid.palstance.fZPalstance,
            })
            # 角加速度
            fields.update({
                f"{prefix}:angular_accel_x": rigid.accpalstance.AccfXPalstance,
                f"{prefix}:angular_accel_y": rigid.accpalstance.AccfYPalstance,
                f"{prefix}:angular_accel_z": rigid.accpalstance.AccfZPalstance,
            })

        return fields

    @staticmethod
    def get_skeleton_fields(skeleton):
        """骨骼数据字段"""
        prefix = f"skeleton:{skeleton.Id}"
        fields = {
            f"{prefix}:id": skeleton.Id,
            f"{prefix}:name": skeleton.Name,
            f"{prefix}:is_track": int(skeleton.IsTrack),
            f"{prefix}:robot_name": skeleton.RobotName,
        }

        # 骨骼数据
        for bone in skeleton.skeletonBones:
            bone_prefix = f"{prefix}:bone:{bone.Id}"
            fields.update({
                f"{bone_prefix}:id": bone.Id,
                f"{bone_prefix}:name": bone.Name,
                f"{bone_prefix}:x": bone.X,
                f"{bone_prefix}:y": bone.Y,
                f"{bone_prefix}:z": bone.Z,
                f"{bone_prefix}:qx": bone.qx,
                f"{bone_prefix}:qy": bone.qy,
                f"{bone_prefix}:qz": bone.qz,
                f"{bone_prefix}:qw": bone.qw,
                f"{bone_prefix}:confidence": bone.Confidence,
                f"{bone_prefix}:angle_x": bone.AngleX,
                f"{bone_prefix}:angle_y": bone.AngleY,
                f"{bone_prefix}:angle_z": bone.AngleZ,
            })

        # 电机角度
        for motor_name, motor_angle in skeleton.MotorAngle.items():
            fields[f"{prefix}:motor:{motor_name}"] = motor_angle

        return fields


class RigidBodyLatestStructure:
    """
    刚体最新状态Hash结构
    Key: rigidbody:{id}:latest
    Type: Hash
    用于快速获取当前状态，实时更新覆盖
    """
    @staticmethod
    def get_fields(frame, rigid):
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
            "accel": rigid.acceleratedSpeeds.fAcceleratedSpeed if rigid.IsTrack else 0,
            "accel_x": rigid.acceleratedSpeeds.XfAcceleratedSpeed if rigid.IsTrack else 0,
            "accel_y": rigid.acceleratedSpeeds.YfAcceleratedSpeed if rigid.IsTrack else 0,
            "accel_z": rigid.acceleratedSpeeds.ZfAcceleratedSpeed if rigid.IsTrack else 0,
            "euler_x": rigid.eulerAngle.X if rigid.IsTrack else 0,
            "euler_y": rigid.eulerAngle.Y if rigid.IsTrack else 0,
            "euler_z": rigid.eulerAngle.Z if rigid.IsTrack else 0,
            "angular_x": rigid.palstance.fXPalstance if rigid.IsTrack else 0,
            "angular_y": rigid.palstance.fYPalstance if rigid.IsTrack else 0,
            "angular_z": rigid.palstance.fZPalstance if rigid.IsTrack else 0,
        }


class SessionInfoStructure:
    """
    会话信息Hash结构
    Key: session:info
    Type: Hash
    """
    @staticmethod
    def get_initial_fields():
        return {
            "start_time": "",           # 开始时间
            "end_time": "",             # 结束时间
            "source_ip": "",           # 数据源IP
            "source_port": "6868",     # 数据源端口
            "total_frames": "0",       # 总帧数
            "status": "running",       # running/stopped/error
            "rigidbody_count": "0",    # 刚体数量
            "marker_count": "0",       # 标记数量
            "skeleton_count": "0",     # 骨骼数量
        }


class SessionStatsStructure:
    """
    会话统计Hash结构
    Key: session:stats
    Type: Hash
    """
    @staticmethod
    def get_fields():
        return {
            "fps": "0",                # 帧率
            "avg_quality": "0",        # 平均质量
            "frames_received": "0",    # 已接收帧数
            "frames_dropped": "0",     # 丢帧数
            "bytes_received": "0",     # 接收字节数
            "last_update": "",         # 最后更新时间
        }


# ==================== Redis Stream 数据结构 ====================

class StreamFrameEntry:
    """
    帧数据Stream条目结构
    Key: stream:frames
    Type: Stream
    """
    @staticmethod
    def get_entry(frame):
        """生成Stream条目数据"""
        return {
            "frame_id": str(frame.FrameId),
            "timestamp": str(frame.TimeStamp),
            "camera_sync": str(frame.uCameraSyncTime),
            "broadcast": str(frame.uBroadcastTime),
            "rigidbody_count": str(len(frame.rigidBodys)),
            "marker_count": str(len(frame.markers)),
            "skeleton_count": str(len(frame.skeletons)),
        }


class StreamRigidBodyEntry:
    """
    刚体数据Stream条目结构
    Key: stream:rigidbody
    Type: Stream
    """
    @staticmethod
    def get_entry(frame, rigid):
        return {
            "frame_id": str(frame.FrameId),
            "timestamp": str(frame.TimeStamp),
            "rigid_id": str(rigid.Id),
            "name": rigid.Name,
            "x": str(rigid.X),
            "y": str(rigid.Y),
            "z": str(rigid.Z),
            "qx": str(rigid.qx),
            "qy": str(rigid.qy),
            "qz": str(rigid.qz),
            "qw": str(rigid.qw),
            "quality": str(rigid.QualityGrade),
            "is_track": str(int(rigid.IsTrack)),
        }


# ==================== 数据保留策略 ====================

class RetentionPolicy:
    """
    数据保留策略配置
    """

    # 热数据保留时间（秒）
    HOT_DATA_TTL = 3600           # 帧数据保留1小时
    HISTORY_TTL = 86400 * 7       # 历史轨迹保留7天

    # Stream最大长度
    STREAM_MAX_LEN = 100000       # Stream保留最近10万条

    # 归档阈值
    ARCHIVE_FRAME_COUNT = 1000000  # 超过100万帧触发归档

    @staticmethod
    def get_ttl_by_key_pattern(key_pattern):
        """根据键模式获取TTL"""
        ttl_map = {
            "frame:*": RetentionPolicy.HOT_DATA_TTL,
            "*:history": RetentionPolicy.HISTORY_TTL,
        }
        return ttl_map.get(key_pattern, 0)


# ==================== 使用示例 ====================

USAGE_EXAMPLE = '''
====================================================================
Redis存储操作示例
====================================================================

# 1. 连接Redis DB1
import redis
r = redis.Redis(db=1)

# 2. 存储一帧数据（使用Pipeline批量操作）
pipe = r.pipeline()

# 2.1 存储帧完整数据
frame_key = f"frame:{frame_id}"
pipe.hset(frame_key, mapping=FrameDataStructure.get_base_fields(frame))

# 2.2 添加时间线索引
pipe.zadd("frames:timeline", {str(frame_id): frame.TimeStamp})

# 2.3 更新最新帧ID
pipe.set("latest:frame", frame_id)

# 2.4 更新刚体最新状态
for rigid in frame.rigidBodys:
    rigid_key = f"rigidbody:{rigid.Id}:latest"
    pipe.hset(rigid_key, mapping=RigidBodyLatestStructure.get_fields(frame, rigid))

# 2.5 添加到实时数据流
pipe.xadd("stream:frames", StreamFrameEntry.get_entry(frame), maxlen=100000)

# 2.6 批量执行
pipe.execute()

# 3. 查询操作

# 3.1 获取最新帧ID
latest_id = r.get("latest:frame")

# 3.2 获取指定帧完整数据
frame_data = r.hgetall(f"frame:{latest_id}")

# 3.3 获取时间范围内的帧（按时间戳）
frames_in_range = r.zrangebyscore(
    "frames:timeline",
    min=start_time,
    max=end_time,
    withscores=True
)

# 3.4 获取刚体当前状态
rigidbody_state = r.hgetall(f"rigidbody:{rigid_id}:latest")

# 3.5 获取刚体历史轨迹
trajectory = r.zrangebyscore(
    f"rigidbody:{rigid_id}:history",
    min=start_time,
    max=end_time,
    withscores=True
)

# 3.6 读取实时数据流（消费者组）
# 创建消费者组
try:
    r.xgroup_create("stream:frames", "consumer_group", id='0', mkstream=True)
except:
    pass

# 读取新消息
messages = r.xreadgroup(
    "consumer_group",
    "consumer_1",
    {"stream:frames": ">"},
    count=10,
    block=1000
)

# 4. 统计分析

# 4.1 获取帧率统计
fps = r.hget("session:stats", "fps")

# 4.2 获取总帧数
total_frames = r.hget("session:info", "total_frames")

# 4.3 获取某时间段的帧数
frame_count = r.zcount("frames:timeline", min=start_time, max=end_time)

# 4.4 获取刚体位置范围
position_range = r.hgetall(f"stats:position:rigidbody:{rigid_id}")

====================================================================
'''
