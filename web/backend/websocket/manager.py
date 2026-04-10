# -*- coding: utf-8 -*-
"""
WebSocket连接管理器
管理所有WebSocket连接和数据推送
"""
from fastapi import WebSocket
from typing import List, Set, Dict
import json
import asyncio
import logging
from datetime import datetime

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

            data = {
                "current": round(random.uniform(100, 150), 1),
                "voltage": round(random.uniform(375, 385), 1),
                "power": round(random.uniform(40, 55), 1)
            }

            await self.broadcast("power", data)


# 创建全局管理器实例
websocket_manager = WebSocketManager()
