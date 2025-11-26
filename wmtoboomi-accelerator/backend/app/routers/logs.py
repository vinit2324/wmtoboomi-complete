"""
Activity logging API routes.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query

from app.models import LogListResponse, LogFilter
from app.services import LoggingService

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogListResponse)
async def get_logs(
    customerId: Optional[str] = Query(None),
    projectId: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    startDate: Optional[datetime] = Query(None),
    endDate: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get activity logs with filtering."""
    filter_params = LogFilter(
        customerId=customerId,
        projectId=projectId,
        level=level,
        category=category,
        startDate=startDate,
        endDate=endDate,
        limit=limit,
        offset=offset
    )
    
    return await LoggingService.get_logs(filter_params)
