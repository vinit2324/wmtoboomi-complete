"""
Logging data models for activity tracking.
"""
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Log entry model."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    customerId: Optional[str] = None
    projectId: Optional[str] = None
    level: Literal["debug", "info", "warning", "error"] = "info"
    category: Literal["upload", "parse", "analyze", "convert", "validate", "push", "ai", "system"] = "system"
    action: str
    message: str
    metadata: dict[str, Any] = {}


class LogResponse(BaseModel):
    """Response model for log entry."""
    id: str
    timestamp: datetime
    customerId: Optional[str] = None
    projectId: Optional[str] = None
    level: str
    category: str
    action: str
    message: str
    metadata: dict = {}


class LogListResponse(BaseModel):
    """Response model for list of logs."""
    logs: list[LogResponse]
    total: int
    hasMore: bool = False


class LogFilter(BaseModel):
    """Filter for querying logs."""
    customerId: Optional[str] = None
    projectId: Optional[str] = None
    level: Optional[str] = None
    category: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
