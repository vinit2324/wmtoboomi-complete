"""
Conversion data models for webMethods to Boomi component conversion.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class BoomiComponentInfo(BaseModel):
    """Information about a pushed Boomi component."""
    componentId: str = ""
    componentUrl: str = ""
    folderPath: str = ""
    pushedAt: Optional[datetime] = None
    pushedBy: str = ""


class ValidationError(BaseModel):
    """Validation error detail."""
    severity: Literal["error", "warning", "info"]
    message: str
    location: str = ""


class ManualReviewItem(BaseModel):
    """Item requiring manual review."""
    type: str
    name: str
    reason: str


class ValidationResult(BaseModel):
    """Validation results for a conversion."""
    isValid: bool = True
    automationLevel: str = "0%"
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []
    manualReviewItems: list[ManualReviewItem] = []
    estimatedManualEffort: str = "0 hours"


class ConversionCreate(BaseModel):
    """Request model for creating a conversion."""
    projectId: str
    sourceName: str
    sourceType: Literal["FlowService", "DocumentType", "AdapterService", "JavaService", "MapService"]


class ConversionResponse(BaseModel):
    """Response model for conversion data."""
    conversionId: str
    projectId: str
    customerId: str
    componentType: Literal["profile.xml", "profile.json", "profile.edi", "profile.flat", "process", "map", "connector"]
    sourceType: Literal["FlowService", "DocumentType", "AdapterService", "JavaService", "MapService"]
    sourceName: str
    targetName: str
    convertedAt: datetime
    status: Literal["pending", "converting", "converted", "validated", "pushed", "failed"]
    complexity: Literal["low", "medium", "high"]
    automationLevel: str
    boomiXml: Optional[str] = None
    boomiComponent: Optional[BoomiComponentInfo] = None
    validation: Optional[ValidationResult] = None
    conversionNotes: list[str] = []
    errorMessage: Optional[str] = None


class ConversionListResponse(BaseModel):
    """Response model for list of conversions."""
    conversions: list[ConversionResponse]
    total: int


class PushToBoomiRequest(BaseModel):
    """Request to push conversion to Boomi."""
    conversionId: str


class PushToBoomiResponse(BaseModel):
    """Response from pushing to Boomi."""
    success: bool
    componentId: Optional[str] = None
    componentUrl: Optional[str] = None
    message: str
