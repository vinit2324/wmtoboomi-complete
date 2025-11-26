"""
AI Assistant API routes.
"""
from fastapi import APIRouter, HTTPException

from app.models import (
    AIRequest,
    AIResponse,
    GroovyGenerationRequest,
    GroovyGenerationResponse,
    WMPublicMappingRequest,
    WMPublicMappingResponse,
)
from app.services import AIService, CustomerService, ProjectService, log_activity

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=AIResponse)
async def chat(request: AIRequest):
    """Send a message to the AI assistant."""
    # Get customer settings
    customer = await CustomerService.get(request.customerId)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.settings.llm.apiKey and customer.settings.llm.provider != "ollama":
        raise HTTPException(status_code=400, detail="LLM not configured for this customer")
    
    # Get project context if requested
    project_context = None
    if request.projectId and request.includeContext:
        project = await ProjectService.get_project(request.projectId)
        if project and project.parsedData:
            project_context = project.parsedData
    
    await log_activity(
        action="ai_chat",
        message=f"AI chat request",
        category="ai",
        customer_id=request.customerId,
        project_id=request.projectId
    )
    
    return await AIService.chat(
        settings=customer.settings.llm,
        request=request,
        project_context=project_context
    )


@router.post("/generate-groovy", response_model=GroovyGenerationResponse)
async def generate_groovy(customerId: str, request: GroovyGenerationRequest):
    """Generate Groovy script from Java code."""
    # Get customer settings
    customer = await CustomerService.get(customerId)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.settings.llm.apiKey and customer.settings.llm.provider != "ollama":
        raise HTTPException(status_code=400, detail="LLM not configured for this customer")
    
    await log_activity(
        action="groovy_generation",
        message=f"Generating Groovy for: {request.serviceName}",
        category="ai",
        customer_id=customerId
    )
    
    return await AIService.generate_groovy(
        settings=customer.settings.llm,
        request=request
    )


@router.post("/map-wmpublic", response_model=WMPublicMappingResponse)
async def map_wm_public(customerId: str, request: WMPublicMappingRequest):
    """Map wMPublic service to Boomi equivalent."""
    # Get customer settings
    customer = await CustomerService.get(customerId)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.settings.llm.apiKey and customer.settings.llm.provider != "ollama":
        raise HTTPException(status_code=400, detail="LLM not configured for this customer")
    
    await log_activity(
        action="wmpublic_mapping",
        message=f"Mapping wMPublic service: {request.serviceName}",
        category="ai",
        customer_id=customerId
    )
    
    return await AIService.map_wm_public(
        settings=customer.settings.llm,
        request=request
    )
