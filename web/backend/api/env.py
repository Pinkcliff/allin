# -*- coding: utf-8 -*-
"""
环境控制API（俯仰、造雨、喷雾）
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class PitchControlRequest(BaseModel):
    """俯仰控制请求"""
    angle: float  # 俯仰角度
    speed: Optional[int] = 50  # 速度百分比


class RainControlRequest(BaseModel):
    """造雨控制请求"""
    intensity: int  # 强度 0-100
    duration: Optional[int] = 10  # 持续时间（秒）


class SprayControlRequest(BaseModel):
    """喷雾控制请求"""
    intensity: int  # 强度 0-100
    duration: Optional[int] = 10  # 持续时间（秒）


@router.get("/status")
async def get_env_status():
    """获取环境设备状态"""
    return {
        "pitch": {
            "enabled": False,
            "current_angle": 0.0,
            "target_angle": 0.0
        },
        "rain": {
            "enabled": False,
            "intensity": 0,
            "remaining_time": 0
        },
        "spray": {
            "enabled": False,
            "intensity": 0,
            "remaining_time": 0
        }
    }


@router.post("/pitch")
async def control_pitch(request: PitchControlRequest):
    """
    俯仰伺服控制

    - angle: 目标角度（度）
    - speed: 运动速度百分比（默认50）
    """
    # TODO: 通过Modbus控制俯仰伺服
    return {
        "success": True,
        "angle": request.angle,
        "speed": request.speed,
        "message": f"俯仰角度设置为 {request.angle} 度"
    }


@router.post("/rain")
async def control_rain(request: RainControlRequest):
    """
    造雨控制

    - intensity: 强度（0-100）
    - duration: 持续时间（秒）
    """
    # TODO: 通过Modbus控制造雨系统
    return {
        "success": True,
        "intensity": request.intensity,
        "duration": request.duration,
        "message": f"造雨系统启动，强度 {request.intensity}%，持续 {request.duration} 秒"
    }


@router.post("/spray")
async def control_spray(request: SprayControlRequest):
    """
    喷雾控制

    - intensity: 强度（0-100）
    - duration: 持续时间（秒）
    """
    # TODO: 通过Modbus控制喷雾系统
    return {
        "success": True,
        "intensity": request.intensity,
        "duration": request.duration,
        "message": f"喷雾系统启动，强度 {request.intensity}%，持续 {request.duration} 秒"
    }


@router.post("/rain/stop")
async def stop_rain():
    """停止造雨"""
    return {
        "success": True,
        "message": "造雨已停止"
    }


@router.post("/spray/stop")
async def stop_spray():
    """停止喷雾"""
    return {
        "success": True,
        "message": "喷雾已停止"
    }
