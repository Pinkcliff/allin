# -*- coding: utf-8 -*-
"""
同步API - 接收桌面客户端的同步数据并通过WebSocket推送到Web端
"""
from fastapi import APIRouter, WebSocket, Depends
from typing import Dict, Any
import logging

from web.backend.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# 注意：风扇同步路由已移至 fan.py 中的 POST /api/fan/sync
# 此处不再重复定义，避免路由冲突


@router.post("/env/sync")
async def sync_env_data(data: Dict[str, Any]):
    """接收环境数据同步"""
    try:
        await websocket_manager.broadcast("environment", {
            "temperature": data.get('temperature'),
            "humidity": data.get('humidity'),
            "pressure": data.get('pressure'),
            "density": data.get('density', 1.177),
            "timestamp": data.get('timestamp')
        })
        logger.info(f"环境数据已同步: 温度={data.get('temperature')}, 湿度={data.get('humidity')}")
        return {"success": True, "message": "环境数据同步成功"}
    except Exception as e:
        logger.error(f"环境数据同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/plc/sync")
async def sync_plc_status(data: Dict[str, Any]):
    """接收PLC状态同步"""
    try:
        await websocket_manager.broadcast("device_status", {
            "plc_connected": data.get('connected'),
            "plc_status": data.get('status'),
            "timestamp": data.get('timestamp')
        })
        logger.info(f"PLC状态已同步: 连接={data.get('connected')}")
        return {"success": True, "message": "PLC状态同步成功"}
    except Exception as e:
        logger.error(f"PLC状态同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/sensor/sync")
async def sync_sensor_data(data: Dict[str, Any]):
    """接收传感器数据同步"""
    try:
        await websocket_manager.broadcast("sensor_update", {
            "sensors": data.get('sensors', []),
            "timestamp": data.get('timestamp')
        })
        logger.info(f"传感器数据已同步: {len(data.get('sensors', []))} 个传感器")
        return {"success": True, "message": "传感器数据同步成功"}
    except Exception as e:
        logger.error(f"传感器数据同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/motion/sync")
async def sync_motion_data(data: Dict[str, Any]):
    """接收动捕数据同步"""
    try:
        await websocket_manager.broadcast("motion_update", {
            **data,
            "timestamp": data.get('timestamp')
        })
        logger.info(f"动捕数据已同步")
        return {"success": True, "message": "动捕数据同步成功"}
    except Exception as e:
        logger.error(f"动捕数据同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/device/sync")
async def sync_device_status(data: Dict[str, Any]):
    """接收设备状态同步"""
    try:
        await websocket_manager.broadcast("device_status", {
            "devices": data.get('devices', []),
            "timestamp": data.get('timestamp')
        })
        logger.info(f"设备状态已同步")
        return {"success": True, "message": "设备状态同步成功"}
    except Exception as e:
        logger.error(f"设备状态同步失败: {e}")
        return {"success": False, "message": str(e)}
