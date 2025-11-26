"""
Field mapping API routes.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.database import db

router = APIRouter(prefix="/api/mappings", tags=["mappings"])


@router.post("")
async def create_mapping(data: dict):
    """Create a new field mapping."""
    mapping = {
        "mappingId": str(datetime.utcnow().timestamp()),
        "projectId": data.get("projectId"),
        "sourceName": data.get("sourceName"),
        "targetName": data.get("targetName"),
        "fieldMappings": data.get("fieldMappings", []),
        "createdAt": datetime.utcnow()
    }
    
    result = await db.mappings.insert_one(mapping)
    mapping["_id"] = str(result.inserted_id)
    
    return mapping


@router.get("")
async def list_mappings():
    """List all mappings."""
    mappings = []
    async for mapping in db.mappings.find():
        mapping["_id"] = str(mapping["_id"])
        mappings.append(mapping)
    
    return {"mappings": mappings}


@router.get("/{mapping_id}")
async def get_mapping(mapping_id: str):
    """Get a specific mapping."""
    mapping = await db.mappings.find_one({"mappingId": mapping_id})
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    mapping["_id"] = str(mapping["_id"])
    return mapping
