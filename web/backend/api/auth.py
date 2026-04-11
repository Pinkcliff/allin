# -*- coding: utf-8 -*-
"""
认证相关API
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

from ..config import settings

router = APIRouter()


# 用户数据模型（临时使用内存存储，生产环境应使用数据库）
# 注意：这是开发环境配置，使用明文密码，生产环境必须使用哈希
USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "full_name": "系统管理员"
    },
    "operator": {
        "username": "operator",
        "password": "operator123",
        "role": "operator",
        "full_name": "操作员"
    },
    "viewer": {
        "username": "viewer",
        "password": "viewer123",
        "role": "viewer",
        "full_name": "观察员"
    }
}


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str
    user: dict


class UserProfile(BaseModel):
    """用户信息"""
    username: str
    full_name: str
    role: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, password: str) -> bool:
    """验证密码（开发环境使用明文比较）"""
    return plain_password == password


def get_user(username: str) -> Optional[dict]:
    """获取用户信息"""
    return USERS_DB.get(username)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    用户登录

    默认账号：
    - 管理员: admin/admin123
    - 操作员: operator/operator123
    - 观察员: viewer/viewer123
    """
    user = get_user(request.username)
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    # 返回用户信息（不包含密码）
    user_info = {
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"]
    }

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_info
    )


@router.post("/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}


@router.get("/profile", response_model=UserProfile)
async def get_profile():
    """获取当前用户信息（需要认证）"""
    # TODO: 从JWT token中获取用户信息
    return UserProfile(
        username="admin",
        full_name="系统管理员",
        role="admin"
    )
