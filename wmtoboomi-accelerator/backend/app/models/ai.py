"""
AI Assistant data models.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class AIMessage(BaseModel):
    """AI chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = None


class AIRequest(BaseModel):
    """Request to AI assistant."""
    projectId: Optional[str] = None
    customerId: str
    message: str
    conversationHistory: list[AIMessage] = []
    includeContext: bool = True


class AIResponse(BaseModel):
    """Response from AI assistant."""
    message: str
    suggestions: list[str] = []
    codeSnippets: list[dict] = []
    relatedServices: list[str] = []


class GroovyGenerationRequest(BaseModel):
    """Request to generate Groovy from Java."""
    javaCode: str
    serviceName: str
    description: str = ""


class GroovyGenerationResponse(BaseModel):
    """Response with generated Groovy code."""
    groovyCode: str
    notes: list[str] = []
    manualReviewRequired: bool = True


class WMPublicMappingRequest(BaseModel):
    """Request to map wMPublic service to Boomi."""
    serviceName: str  # e.g., "pub.string:concat"
    context: str = ""


class WMPublicMappingResponse(BaseModel):
    """Response with Boomi equivalent."""
    boomiEquivalent: str
    boomiShape: str
    configuration: dict = {}
    notes: list[str] = []
