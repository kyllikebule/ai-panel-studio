"""讨论路由 —— DDD 阶段仅定义 Router 骨架，业务逻辑后续实现。"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/discussions", tags=["discussions"])
