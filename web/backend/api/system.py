# -*- coding: utf-8 -*-
"""
系统状态API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

router = APIRouter()


class DeviceStatus(BaseModel):
    """设备状态"""
    name: str
    status: str  # online, offline, error
    message: str


class CommStatus(BaseModel):
    """通讯状态"""
    name: str
    protocol: str
    status: str
    count: int
    speed: str


class EnvironmentData(BaseModel):
    """环境数据"""
    temperature: float
    humidity: float
    pressure: float
    density: float


class PowerData(BaseModel):
    """电力数据"""
    current: float
    voltage: float
    power: float


@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    return {
        "device_on": True,
        "health": "normal",
        "uptime": "12天 5小时 32分钟",
        "last_update": datetime.now().isoformat()
    }


@router.get("/devices", response_model=List[DeviceStatus])
async def get_device_status():
    """获取设备状态列表"""
    return [
        {"name": "主控制器", "status": "online", "message": "正常"},
        {"name": "电驱", "status": "online", "message": "正常"},
        {"name": "风速传感", "status": "online", "message": "正常"},
        {"name": "温度传感", "status": "online", "message": "正常"},
        {"name": "湿度传感", "status": "online", "message": "正常"},
        {"name": "动捕", "status": "online", "message": "8/12 相机在线"},
        {"name": "俯仰伺服", "status": "offline", "message": "未启动"},
        {"name": "造雨", "status": "offline", "message": "未启动"},
        {"name": "喷雾", "status": "offline", "message": "未启动"},
    ]


@router.get("/communications", response_model=List[CommStatus])
async def get_communication_status():
    """获取通讯状态列表"""
    return [
        {"name": "主控制器", "protocol": "TCP/IP", "status": "online", "count": 128, "speed": "100 Mbps"},
        {"name": "电驱", "protocol": "EtherCAT", "status": "online", "count": 64, "speed": "100 Mbps"},
        {"name": "风速传感", "protocol": "EtherCAT", "status": "online", "count": 16, "speed": "100 Mbps"},
        {"name": "温度传感", "protocol": "EtherCAT", "status": "online", "count": 16, "speed": "100 Mbps"},
        {"name": "湿度传感", "protocol": "EtherCAT", "status": "online", "count": 16, "speed": "100 Mbps"},
        {"name": "动捕", "protocol": "API", "status": "online", "count": 12, "speed": "1 Gbps"},
        {"name": "俯仰伺服", "protocol": "Modbus", "status": "offline", "count": 0, "speed": "-"},
        {"name": "造雨", "protocol": "Modbus", "status": "offline", "count": 0, "speed": "-"},
        {"name": "喷雾", "protocol": "Modbus", "status": "offline", "count": 0, "speed": "-"},
    ]


@router.get("/environment", response_model=EnvironmentData)
async def get_environment_data():
    """获取环境数据"""
    return {
        "temperature": 25.3,
        "humidity": 65.2,
        "pressure": 101325,
        "density": 1.184
    }


@router.get("/power", response_model=PowerData)
async def get_power_data():
    """获取电力数据"""
    return {
        "current": 125.5,
        "voltage": 380.2,
        "power": 47.7
    }


@router.get("/logs")
async def get_system_logs(limit: int = 100):
    """获取系统日志"""
    return {
        "logs": [
            {"time": "2026-04-10 10:30:15", "level": "INFO", "module": "系统", "message": "系统启动完成"},
            {"time": "2026-04-10 10:30:16", "level": "INFO", "module": "通讯", "message": "主控制器连接成功"},
            {"time": "2026-04-10 10:30:17", "level": "INFO", "module": "动捕", "message": "8/12 相机在线"},
        ]
    }
