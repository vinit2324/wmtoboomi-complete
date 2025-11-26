"""
Mapping data models for visual field mapping.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class FieldMapping(BaseModel):
    """Individual field mapping."""
    id: str
    sourceField: str
    sourceType: str = "string"
    targetField: str
    targetType: str = "string"
    transformation: Literal["direct", "format", "concat", "lookup", "custom"] = "direct"
    transformationLogic: Optional[str] = None
    isMapped: bool = True
    isValidated: bool = False
    notes: str = ""


class SchemaField(BaseModel):
    """Schema field definition."""
    name: str
    path: str
    type: str
    isArray: bool = False
    isRequired: bool = False
    children: list["SchemaField"] = []


SchemaField.model_rebuild()


class MappingCreate(BaseModel):
    """Request model for creating a mapping."""
    projectId: str
    sourceName: str
    targetName: str
    sourceSchema: list[SchemaField] = []
    targetSchema: list[SchemaField] = []


class MappingUpdate(BaseModel):
    """Request model for updating a mapping."""
    fieldMappings: list[FieldMapping] = []
    sourceName: Optional[str] = None
    targetName: Optional[str] = None


class MappingResponse(BaseModel):
    """Response model for mapping data."""
    mappingId: str
    projectId: str
    sourceName: str
    targetName: str
    sourceSchema: list[SchemaField] = []
    targetSchema: list[SchemaField] = []
    fieldMappings: list[FieldMapping] = []
    createdAt: datetime
    updatedAt: datetime
    mappingStatus: str = "incomplete"  # incomplete, complete, validated


class MappingListResponse(BaseModel):
    """Response model for list of mappings."""
    mappings: list[MappingResponse]
    total: int


class MappingSuggestion(BaseModel):
    """AI-suggested field mapping."""
    sourceField: str
    targetField: str
    confidence: float
    reason: str
    suggestedTransformation: str = "direct"
