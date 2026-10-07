import hashlib
import hmac
import secrets

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter()


class AdminLoginRequest(BaseModel):
    password: str = Field(..., min_length=1)


class AdminLoginResponse(BaseModel):
    token: str


def _expected_token() -> str:
    # 口令派生的固定令牌；换口令即旧令牌全部失效
    return hashlib.sha256(f"stem-admin:{settings.admin_password}".encode()).hexdigest()


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """管理台数据接口的鉴权依赖"""
    if not settings.admin_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin login is disabled (ADMIN_PASSWORD not set)")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, _expected_token()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin token invalid")


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest) -> AdminLoginResponse:
    if not settings.admin_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin login is disabled (ADMIN_PASSWORD not set)")
    if not secrets.compare_digest(data.password, settings.admin_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="口令不正确")
    return AdminLoginResponse(token=_expected_token())
