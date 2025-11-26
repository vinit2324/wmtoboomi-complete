"""
Field mapping API routes.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from app.database import get_mappings_collection
from app.models import (
    MappingCreate,
    MappingUpdate,
    MappingResponse,
    MappingListResponse,
    MappingSuggestion,
)
from app.services import log_activity

router = APIRouter(prefix="/api/mappings", tags=["mappings"])


@router.post("", response_model=MappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(data: MappingCreate):
    """Create a new field mapping."""
    mappings = get_mappings_collection()
    
    mapping_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    doc = {
        "mappingId": mapping_id,
        "projectId": data.projectId,
        "sourceName": data.sourceName,
        "targetName": data.targetName,
        "sourceSchema": [s.model_dump() for s in data.sourceSchema],
        "targetSchema": [s.model_dump() for s in data.targetSchema],
        "fieldMappings": [],
        "createdAt": now,
        "updatedAt": now,
        "mappingStatus": "incomplete"
    }
    
    await mappings.insert_one(doc)
    
    await log_activity(
        action="mapping_created",
        message=f"Mapping created: {data.sourceName} -> {data.targetName}",
        category="convert",
        project_id=data.projectId
    )
    
    return MappingResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.get("", response_model=MappingListResponse)
async def list_mappings(projectId: str):
    """List all mappings for a project."""
    mappings = get_mappings_collection()
    
    cursor = mappings.find({"projectId": projectId}).sort("createdAt", -1)
    
    mapping_list = []
    async for doc in cursor:
        mapping_list.append(MappingResponse(**{k: v for k, v in doc.items() if k != "_id"}))
    
    return MappingListResponse(
        mappings=mapping_list,
        total=len(mapping_list)
    )


@router.get("/{mapping_id}", response_model=MappingResponse)
async def get_mapping(mapping_id: str):
    """Get a mapping by ID."""
    mappings = get_mappings_collection()
    
    doc = await mappings.find_one({"mappingId": mapping_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return MappingResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.put("/{mapping_id}", response_model=MappingResponse)
async def update_mapping(mapping_id: str, data: MappingUpdate):
    """Update a mapping."""
    mappings = get_mappings_collection()
    
    update_doc = {"updatedAt": datetime.utcnow()}
    
    if data.fieldMappings is not None:
        update_doc["fieldMappings"] = [fm.model_dump() for fm in data.fieldMappings]
        
        # Calculate mapping status
        if len(data.fieldMappings) == 0:
            update_doc["mappingStatus"] = "incomplete"
        else:
            all_validated = all(fm.isValidated for fm in data.fieldMappings)
            update_doc["mappingStatus"] = "validated" if all_validated else "complete"
    
    if data.sourceName is not None:
        update_doc["sourceName"] = data.sourceName
    
    if data.targetName is not None:
        update_doc["targetName"] = data.targetName
    
    result = await mappings.update_one(
        {"mappingId": mapping_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    await log_activity(
        action="mapping_updated",
        message=f"Mapping updated",
        category="convert"
    )
    
    doc = await mappings.find_one({"mappingId": mapping_id})
    return MappingResponse(**{k: v for k, v in doc.items() if k != "_id"})


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(mapping_id: str):
    """Delete a mapping."""
    mappings = get_mappings_collection()
    
    result = await mappings.delete_one({"mappingId": mapping_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")


@router.post("/{mapping_id}/suggest", response_model=list[MappingSuggestion])
async def suggest_mappings(mapping_id: str):
    """Get AI-suggested field mappings."""
    mappings = get_mappings_collection()
    
    doc = await mappings.find_one({"mappingId": mapping_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    suggestions = []
    
    source_schema = doc.get("sourceSchema", [])
    target_schema = doc.get("targetSchema", [])
    
    # Simple name-based matching
    source_fields = {}
    for field in source_schema:
        name = field.get("name", "").lower()
        source_fields[name] = field
    
    for target_field in target_schema:
        target_name = target_field.get("name", "").lower()
        
        # Exact match
        if target_name in source_fields:
            suggestions.append(MappingSuggestion(
                sourceField=source_fields[target_name].get("path", source_fields[target_name].get("name")),
                targetField=target_field.get("path", target_field.get("name")),
                confidence=1.0,
                reason="Exact name match",
                suggestedTransformation="direct"
            ))
            continue
        
        # Partial match
        for source_name, source_field in source_fields.items():
            if target_name in source_name or source_name in target_name:
                suggestions.append(MappingSuggestion(
                    sourceField=source_field.get("path", source_field.get("name")),
                    targetField=target_field.get("path", target_field.get("name")),
                    confidence=0.7,
                    reason="Partial name match",
                    suggestedTransformation="direct"
                ))
                break
            
            # Type-based matching
            if source_field.get("type") == target_field.get("type"):
                suggestions.append(MappingSuggestion(
                    sourceField=source_field.get("path", source_field.get("name")),
                    targetField=target_field.get("path", target_field.get("name")),
                    confidence=0.3,
                    reason="Same data type",
                    suggestedTransformation="direct"
                ))
    
    # Sort by confidence
    suggestions.sort(key=lambda x: x.confidence, reverse=True)
    
    return suggestions[:20]  # Return top 20 suggestions
