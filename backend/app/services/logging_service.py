"""
Logging service for activity tracking.
"""
from datetime import datetime
from typing import Optional, Any
from bson import ObjectId

from app.database import get_logs_collection
from app.models import LogEntry, LogResponse, LogListResponse, LogFilter


class LoggingService:
    """Service for logging application activities."""
    
    @staticmethod
    async def log(
        action: str,
        message: str,
        category: str = "system",
        level: str = "info",
        customer_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: dict[str, Any] = None
    ) -> str:
        """Create a log entry."""
        logs = get_logs_collection()
        
        entry = {
            "timestamp": datetime.utcnow(),
            "customerId": customer_id,
            "projectId": project_id,
            "level": level,
            "category": category,
            "action": action,
            "message": message,
            "metadata": metadata or {}
        }
        
        result = await logs.insert_one(entry)
        return str(result.inserted_id)
    
    @staticmethod
    async def info(action: str, message: str, **kwargs):
        """Log info level message."""
        return await LoggingService.log(action, message, level="info", **kwargs)
    
    @staticmethod
    async def warning(action: str, message: str, **kwargs):
        """Log warning level message."""
        return await LoggingService.log(action, message, level="warning", **kwargs)
    
    @staticmethod
    async def error(action: str, message: str, **kwargs):
        """Log error level message."""
        return await LoggingService.log(action, message, level="error", **kwargs)
    
    @staticmethod
    async def debug(action: str, message: str, **kwargs):
        """Log debug level message."""
        return await LoggingService.log(action, message, level="debug", **kwargs)
    
    @staticmethod
    async def get_logs(filter_params: LogFilter) -> LogListResponse:
        """Get logs with filtering."""
        logs = get_logs_collection()
        
        # Build query
        query = {}
        if filter_params.customerId:
            query["customerId"] = filter_params.customerId
        if filter_params.projectId:
            query["projectId"] = filter_params.projectId
        if filter_params.level:
            query["level"] = filter_params.level
        if filter_params.category:
            query["category"] = filter_params.category
        if filter_params.startDate:
            query["timestamp"] = {"$gte": filter_params.startDate}
        if filter_params.endDate:
            query.setdefault("timestamp", {})["$lte"] = filter_params.endDate
        
        # Get total count
        total = await logs.count_documents(query)
        
        # Get logs with pagination
        cursor = logs.find(query).sort("timestamp", -1).skip(filter_params.offset).limit(filter_params.limit)
        
        log_list = []
        async for doc in cursor:
            log_list.append(LogResponse(
                id=str(doc["_id"]),
                timestamp=doc["timestamp"],
                customerId=doc.get("customerId"),
                projectId=doc.get("projectId"),
                level=doc["level"],
                category=doc["category"],
                action=doc["action"],
                message=doc["message"],
                metadata=doc.get("metadata", {})
            ))
        
        return LogListResponse(
            logs=log_list,
            total=total,
            hasMore=total > (filter_params.offset + len(log_list))
        )


# Convenience function for quick logging
async def log_activity(
    action: str,
    message: str,
    category: str = "system",
    level: str = "info",
    customer_id: Optional[str] = None,
    project_id: Optional[str] = None,
    **metadata
):
    """Quick logging function."""
    await LoggingService.log(
        action=action,
        message=message,
        category=category,
        level=level,
        customer_id=customer_id,
        project_id=project_id,
        metadata=metadata
    )
