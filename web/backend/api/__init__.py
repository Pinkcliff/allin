# -*- coding: utf-8 -*-
"""
API路由模块
"""
from fastapi import APIRouter

# 导入各个路由模块
import web.backend.api.auth as auth
import web.backend.api.system as system
import web.backend.api.device as device
import web.backend.api.fan as fan
import web.backend.api.env as env
import web.backend.api.plc as plc
import web.backend.api.motion as motion
import web.backend.api.sensor as sensor
import web.backend.api.sync as sync

__all__ = [
    "auth",
    "system",
    "device",
    "fan",
    "env",
    "plc",
    "motion",
    "sensor",
    "sync"
]
