"""Activity Logs API routes"""
from fastapi import APIRouter
from datetime import datetime
from app.database import db

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
async def get_logs(limit: int = 100, level: str = None, category: str = None):
    """Get activity logs"""
    
    query = {}
    if level:
        query["level"] = level
    if category:
        query["category"] = category
    
    logs = []
    async for log in db.logs.find(query).sort("timestamp", -1).limit(limit):
        log["_id"] = str(log["_id"])
        logs.append(log)
    
    return {
        "logs": logs,
        "total": len(logs)
    }

@router.post("")
async def create_log(data: dict):
    """Create a new log entry"""
    
    log = {
        "timestamp": datetime.utcnow(),
        "level": data.get("level", "info"),
        "category": data.get("category", "system"),
        "action": data.get("action", ""),
        "message": data.get("message", ""),
        "metadata": data.get("metadata", {}),
        "projectId": data.get("projectId"),
        "customerId": data.get("customerId")
    }
    
    result = await db.logs.insert_one(log)
    log["_id"] = str(result.inserted_id)
    
    return log
