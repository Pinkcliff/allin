# -*- coding: utf-8 -*-
"""
设备控制API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PowerRequest(BaseModel):
    """电源控制请求"""
    device_on: bool


class DeviceConfigRequest(BaseModel):
    """设备配置请求"""
    key: str
    value: str


@router.get("/status")
async def get_device_status():
    """获取设备总状态"""
    return {
        "device_on": True,
        "health": "normal"
    }


@router.post("/power")
async def set_device_power(request: PowerRequest):
    """
    设置设备电源

    - **device_on**: true=开启设备, false=关闭设备
    """
    # TODO: 实际控制设备电源
    return {
        "success": True,
        "device_on": request.device_on,
        "message": f"设备已{'启动' if request.device_on else '关闭'}"
    }


@router.post("/sync")
async def sync_device_status(data: Dict[str, Any]):
    """
    接收桌面端设备状态同步

    Args:
        data: 包含devices列表和timestamp的字典

    Returns:
        同步结果
    """
    try:
        from web.backend.websocket.manager import websocket_manager

        # 通过WebSocket推送到所有订阅的客户端
        await websocket_manager.broadcast("device_status", data)

        logger.info(f"设备状态已同步: {len(data.get('devices', []))} 个设备")
        return {"success": True, "message": "设备状态同步成功"}
    except Exception as e:
        logger.error(f"设备状态同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.put("/config")
async def set_device_config(request: DeviceConfigRequest):
    """
    设置设备配置
    """
    # TODO: 实际设置设备配置
    return {
        "success": True,
        "key": request.key,
        "value": request.value,
        "message": "配置已更新"
    }
