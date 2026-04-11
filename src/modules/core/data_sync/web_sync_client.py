# -*- coding: utf-8 -*-
"""
Web同步客户端
通过WebSocket将桌面端数据实时推送到Web端（跳过HTTP，极低延迟）
"""
import json
import threading
import logging
import time
import asyncio
from typing import Dict, Any, Optional
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class WebSyncClient:
    """WebSocket同步客户端 - 直连后端WebSocket，实时推送数据"""

    def __init__(self, web_api_url: str = "http://localhost:8000"):
        # 从HTTP URL推导WebSocket URL
        ws_url = web_api_url.rstrip('/')
        ws_url = ws_url.replace("http://", "ws://").replace("https://", "wss://")
        if not ws_url.startswith("ws://") and not ws_url.startswith("wss://"):
            ws_url = "ws://" + ws_url
        self.ws_url = ws_url + "/ws"

        self.enabled = True
        self.sync_queue = Queue()
        self.running = False
        self.sync_thread = None
        self._connected = False
        self.last_error_time = None
        self.consecutive_errors = 0

        self.start()

    def start(self):
        """启动同步线程"""
        if not self.running:
            self.running = True
            self.sync_thread = threading.Thread(target=self._ws_thread_main, daemon=True)
            self.sync_thread.start()
            logger.info("WebSocket同步客户端已启动")

    def stop(self):
        """停止同步线程"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
        logger.info("WebSocket同步客户端已停止")

    def _ws_thread_main(self):
        """WebSocket线程主循环（独立线程 + 独立事件循环）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ws_connect_and_run())
        except Exception as e:
            logger.error(f"WebSocket线程异常: {e}")
        finally:
            loop.close()

    async def _ws_connect_and_run(self):
        """连接WebSocket并持续发送数据"""
        try:
            import websockets
        except ImportError:
            logger.error("websockets库未安装，请运行: pip install websockets")
            return

        while self.running:
            ws = None
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5
                ) as ws:
                    self._connected = True
                    logger.info(f"WebSocket已连接: {self.ws_url}")
                    self.consecutive_errors = 0

                    # 持续从队列取数据并发送
                    while self.running:
                        try:
                            task = self.sync_queue.get(timeout=0.05)
                        except Empty:
                            await asyncio.sleep(0.01)
                            continue

                        if task:
                            await ws.send(json.dumps(task))

            except Exception as e:
                self._connected = False
                self.consecutive_errors += 1

                current_time = time.time()
                if self.last_error_time is None or current_time - self.last_error_time > 10:
                    logger.warning(f"WebSocket连接失败: {e}，1秒后重连...")
                    self.last_error_time = current_time

                await asyncio.sleep(1)

    @property
    def is_connected(self):
        return self._connected

    def sync_fan_array(self, fan_array: list):
        """
        同步风扇阵列数据（直接通过WebSocket推送）

        Args:
            fan_array: 40x40二维数组，值为PWM值(0-1000)
        """
        # 计算活跃风扇数
        active_count = sum(1 for row in fan_array for cell in row if cell > 0)

        self.sync_queue.put({
            "type": "publish",
            "channel": "fan_update",
            "data": {
                "fan_array": fan_array,
                "total_fans": 1600,
                "active_fans": active_count,
                "timestamp": time.time()
            }
        })

    def sync_environment(self, temperature: float, humidity: float, pressure: float):
        """同步环境数据"""
        self.sync_queue.put({
            "type": "publish",
            "channel": "environment",
            "data": {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "timestamp": time.time()
            }
        })

    def sensor_update(self, sensors_data: list):
        """同步传感器数据"""
        self.sync_queue.put({
            "type": "publish",
            "channel": "sensor_update",
            "data": {
                "sensors": sensors_data,
                "timestamp": time.time()
            }
        })

    def sync_plc_status(self, connected: bool, status: Dict[str, Any]):
        """同步PLC状态"""
        self.sync_queue.put({
            "type": "publish",
            "channel": "device_status",
            "data": {
                "plc_connected": connected,
                "plc_status": status,
                "timestamp": time.time()
            }
        })

    def sync_device_status(self, devices: list):
        """同步设备状态"""
        self.sync_queue.put({
            "type": "publish",
            "channel": "device_status",
            "data": {
                "devices": devices,
                "timestamp": time.time()
            }
        })

    def sync_motion_data(self, motion_data: Dict[str, Any]):
        """同步动捕数据"""
        self.sync_queue.put({
            "type": "publish",
            "channel": "motion_update",
            "data": {**motion_data, "timestamp": time.time()}
        })


# 创建全局同步客户端实例
_web_sync_client: Optional[WebSyncClient] = None


def get_web_sync_client() -> WebSyncClient:
    """获取全局同步客户端实例"""
    global _web_sync_client
    if _web_sync_client is None:
        _web_sync_client = WebSyncClient()
    return _web_sync_client


def enable_web_sync(enabled: bool = True):
    """启用或禁用Web同步"""
    client = get_web_sync_client()
    client.enabled = enabled
    if not enabled:
        client.stop()
    elif not client.running:
        client.start()
