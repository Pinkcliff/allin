# -*- coding: utf-8 -*-
"""
WebSocket连接管理器
管理所有WebSocket连接和数据推送
从Redis读取真实数据并推送给前端
"""
from fastapi import WebSocket
from typing import List, Set, Dict
import json
import asyncio
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 所有活跃连接
        self.active_connections: List[WebSocket] = []
        # 每个连接订阅的频道
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        # 数据生成任务
        self.data_tasks: List[asyncio.Task] = []
        # Redis客户端
        self.redis_client = None
        self._connect_redis()

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    def _connect_redis(self):
        """连接Redis服务器"""
        try:
            from modules.core.data_storage.redis_database import RedisDatabase
            self.redis_client = RedisDatabase(host='localhost', port=6379, db=0)
            if self.redis_client.connect():
                logger.info("Redis连接成功")
            else:
                logger.warning("Redis连接失败，将使用模拟数据")
        except Exception as e:
            logger.warning(f"Redis初始化失败: {e}，将使用模拟数据")

    async def handle_message(self, websocket: WebSocket, message: dict):
        """处理客户端消息"""
        msg_type = message.get("type")

        if msg_type == "subscribe":
            # 订阅频道
            channels = message.get("channels", [])
            for channel in channels:
                self.subscriptions[websocket].add(channel)
            logger.info(f"客户端订阅频道: {channels}")

        elif msg_type == "unsubscribe":
            # 取消订阅
            channels = message.get("channels", [])
            for channel in channels:
                self.subscriptions[websocket].discard(channel)
            logger.info(f"客户端取消订阅频道: {channels}")

        elif msg_type == "ping":
            # 心跳响应
            await websocket.send_json({"type": "pong"})

        elif msg_type == "publish":
            # 桌面端直接通过WebSocket推送数据，跳过HTTP
            channel = message.get("channel")
            data = message.get("data")
            if channel and data:
                # 更新风扇数据存储（保持 /api/fan/status 接口数据最新）
                if channel == "fan_update" and "fan_array" in data:
                    from web.backend.api.fan import _fan_data_store
                    import time as _time
                    fan_array = data["fan_array"]
                    ts = data.get("timestamp", _time.time())
                    if ts > _fan_data_store["last_timestamp"]:
                        _fan_data_store["fan_array"] = fan_array
                        _fan_data_store["last_timestamp"] = ts
                        _fan_data_store["last_update"] = ts

                await self.broadcast(channel, data)

    async def broadcast(self, channel: str, data: dict):
        """向订阅指定频道的所有客户端广播消息"""
        message = {
            "type": channel,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # 获取订阅了该频道的连接
        target_connections = [
            conn for conn, channels in self.subscriptions.items()
            if channel in channels
        ]

        # 发送消息
        disconnected = []
        for connection in target_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, channel: str, data: dict):
        """向指定客户端发送消息"""
        message = {
            "type": channel,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
            self.disconnect(websocket)

    def start_data_generation(self):
        """启动数据生成任务（用于演示）"""
        # 创建设备状态推送任务
        task1 = asyncio.create_task(self._push_device_status())
        self.data_tasks.append(task1)

        # 创建环境数据推送任务
        task2 = asyncio.create_task(self._push_environment_data())
        self.data_tasks.append(task2)

        # 创建电力数据推送任务
        task3 = asyncio.create_task(self._push_power_data())
        self.data_tasks.append(task3)

        logger.info("数据生成任务已启动")

    def stop_data_generation(self):
        """停止数据生成任务"""
        for task in self.data_tasks:
            task.cancel()
        self.data_tasks.clear()
        logger.info("数据生成任务已停止")

    async def _push_device_status(self):
        """推送设备状态（每秒）"""
        import random

        while True:
            await asyncio.sleep(1)

            # 尝试从Redis读取真实数据
            try:
                if self.redis_client and self.redis_client.is_connected():
                    # 从Redis读取最新的设备状态
                    # 这里需要根据实际的Redis键结构来读取
                    # 暂时使用模拟数据，实际应该从Redis读取
                    pass
            except Exception as e:
                logger.warning(f"从Redis读取设备状态失败: {e}")

            # 模拟数据（实际应从Redis读取）
            data = {
                "device_on": True,
                "health": "normal",
                "devices": [
                    {"name": "主控制器", "status": "online"},
                    {"name": "电驱", "status": "online"},
                    {"name": "风速传感", "status": "online"},
                    {"name": "温度传感", "status": "online"},
                    {"name": "湿度传感", "status": "online"},
                    {"name": "动捕", "status": "online", "cameras": f"{random.randint(7, 9)}/12"},
                ]
            }

            await self.broadcast("device_status", data)

    async def _push_environment_data(self):
        """推送环境数据（每秒）"""
        import random

        while True:
            await asyncio.sleep(1)

            # 尝试从Redis读取真实数据
            try:
                if self.redis_client and self.redis_client.is_connected():
                    # 从Redis读取最新的环境数据
                    # 这里需要根据实际的Redis键结构来读取
                    pass
            except Exception as e:
                logger.warning(f"从Redis读取环境数据失败: {e}")

            # 模拟数据（实际应从Redis读取）
            data = {
                "temperature": round(random.uniform(23, 28), 1),
                "humidity": round(random.uniform(55, 75), 1),
                "pressure": round(random.uniform(101200, 101400), 0),
                "density": round(random.uniform(1.15, 1.22), 3)
            }

            await self.broadcast("environment", data)

    async def _push_power_data(self):
        """推送电力数据（每秒）"""
        import random

        while True:
            await asyncio.sleep(1)

            # 尝试从Redis读取真实数据
            try:
                if self.redis_client and self.redis_client.is_connected():
                    # 从Redis读取最新的电力数据
                    # 这里需要根据实际的Redis键结构来读取
                    pass
            except Exception as e:
                logger.warning(f"从Redis读取电力数据失败: {e}")

            # 模拟数据（实际应从Redis读取）
            data = {
                "current": round(random.uniform(100, 150), 1),
                "voltage": round(random.uniform(375, 385), 1),
                "power": round(random.uniform(40, 55), 1)
            }

            await self.broadcast("power", data)


# 创建全局管理器实例
websocket_manager = WebSocketManager()
