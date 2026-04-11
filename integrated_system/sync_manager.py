# -*- coding: utf-8 -*-
"""
数据同步管理器 - 负责桌面客户端与Web端的数据同步
"""
import json
import requests
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, Signal


class SyncManager(QObject):
    """数据同步管理器"""

    # 同步状态信号
    sync_success = Signal(str)  # 同步成功
    sync_error = Signal(str)    # 同步失败

    def __init__(self, api_base_url="http://localhost:8000/api"):
        super().__init__()
        self.api_base_url = api_base_url
        self.token = None

    def set_token(self, token: str):
        """设置认证Token"""
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def sync_fan_status(self, fan_data: Dict[str, Any]):
        """同步风扇状态"""
        try:
            response = requests.post(
                f"{self.api_base_url}/fan/sync",
                json=fan_data,
                headers=self._get_headers(),
                timeout=2
            )
            if response.status_code == 200:
                self.sync_success.emit("风扇状态同步成功")
                return True
            else:
                self.sync_error.emit(f"风扇状态同步失败: {response.status_code}")
                return False
        except Exception as e:
            # 静默失败，不影响桌面客户端使用
            print(f"风扇同步警告: {e}")
            return False

    def sync_env_data(self, env_data: Dict[str, Any]):
        """同步环境数据"""
        try:
            response = requests.post(
                f"{self.api_base_url}/env/sync",
                json=env_data,
                headers=self._get_headers(),
                timeout=2
            )
            if response.status_code == 200:
                self.sync_success.emit("环境数据同步成功")
                return True
        except Exception as e:
            print(f"环境数据同步警告: {e}")
            return False

    def sync_plc_status(self, plc_data: Dict[str, Any]):
        """同步PLC状态"""
        try:
            response = requests.post(
                f"{self.api_base_url}/plc/sync",
                json=plc_data,
                headers=self._get_headers(),
                timeout=2
            )
            if response.status_code == 200:
                self.sync_success.emit("PLC状态同步成功")
                return True
        except Exception as e:
            print(f"PLC状态同步警告: {e}")
            return False

    def sync_sensor_data(self, sensor_data: Dict[str, Any]):
        """同步传感器数据"""
        try:
            response = requests.post(
                f"{self.api_base_url}/sensor/sync",
                json=sensor_data,
                headers=self._get_headers(),
                timeout=2
            )
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"传感器数据同步警告: {e}")
            return False

    def sync_motion_data(self, motion_data: Dict[str, Any]):
        """同步动捕数据"""
        try:
            response = requests.post(
                f"{self.api_base_url}/motion/sync",
                json=motion_data,
                headers=self._get_headers(),
                timeout=2
            )
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"动捕数据同步警告: {e}")
            return False


# 全局同步管理器实例
sync_manager = SyncManager()
