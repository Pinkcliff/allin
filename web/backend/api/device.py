# -*- coding: utf-8 -*-
"""
设备控制API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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
