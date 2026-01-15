from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.api import deps
from app.core.config import settings

router = APIRouter()

@router.get("/config")
async def get_config(
    # current_user = Depends(deps.require_role("admin")) # Uncomment for security
) -> Dict[str, Any]:
    """
    Get system configuration (Safe subset).
    """
    return {
        "APP_NAME": settings.APP_NAME,
        "APP_ENV": settings.APP_ENV,
        "API_V1_STR": settings.API_V1_STR,
        "POSTGRES_PORT": settings.POSTGRES_PORT,
        "REDIS_STREAM_NAME": settings.REDIS_STREAM_NAME
    }

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(deps.require_role("admin"))
) -> Any:
    """
    List all users.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/logs")
async def get_logs(lines: int = 50) -> Dict[str, List[str]]:
    """
    Retrieve recent system logs (Placeholder).
    In a real app, this would read from file or centralized logging system.
    """
    # Simulated logs
    return {
        "logs": [
            "2024-01-01 12:00:00 INFO System started",
            "2024-01-01 12:05:00 INFO User logged in",
            "2024-01-01 12:10:00 WARNING High latency detected",
            f"Current Log Level: {os.getenv('LOG_LEVEL', 'INFO')}"
        ]
    }
