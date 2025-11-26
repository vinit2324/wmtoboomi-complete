"""
Conversion API routes.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List

from app.models import (
    ConversionCreate,
    ConversionResponse,
    ConversionListResponse,
    PushToBoomiRequest,
    PushToBoomiResponse,
    ParsedService,
)
from app.services import ConversionService, BoomiAPIService, CustomerService, ProjectService

router = APIRouter(prefix="/api/conversions", tags=["conversions"])


class ConvertAllRequest(BaseModel):
    """Request to convert all services in a project."""
    projectId: str
    customerId: str


class ConvertAllResponse(BaseModel):
    """Response from converting all services."""
    conversions: List[ConversionResponse]
    successful: int
    failed: int


@router.post("", response_model=ConversionResponse, status_code=status.HTTP_201_CREATED)
async def convert_service(data: ConversionCreate):
    """Convert a single webMethods service to Boomi component."""
    # Get project to find the service
    project = await ProjectService.get_project(data.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.parsedData:
        raise HTTPException(status_code=400, detail="Project not parsed yet")
    
    # Find the service
    service = None
    for svc in project.parsedData.services:
        if svc.name == data.sourceName:
            service = svc
            break
    
    # Also check documents
    if not service:
        for doc in project.parsedData.documents:
            if doc.name == data.sourceName:
                # Convert document to service-like object for conversion
                service = ParsedService(
                    type="DocumentType",
                    name=doc.name,
                    path=doc.path
                )
                break
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found in project")
    
    return await ConversionService.convert_service(
        project_id=data.projectId,
        customer_id=project.customerId,
        service=service
    )


@router.post("/convert-all", response_model=ConvertAllResponse)
async def convert_all_services(data: ConvertAllRequest):
    """Convert all services in a project."""
    project = await ProjectService.get_project(data.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.parsedData:
        raise HTTPException(status_code=400, detail="Project not parsed yet")
    
    conversions = []
    successful = 0
    failed = 0
    
    # Convert all services
    for service in project.parsedData.services:
        try:
            conversion = await ConversionService.convert_service(
                project_id=data.projectId,
                customer_id=data.customerId,
                service=service
            )
            conversions.append(conversion)
            if conversion.status != "failed":
                successful += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
    
    # Convert all documents
    for doc in project.parsedData.documents:
        try:
            service = ParsedService(
                type="DocumentType",
                name=doc.name,
                path=doc.path
            )
            conversion = await ConversionService.convert_service(
                project_id=data.projectId,
                customer_id=data.customerId,
                service=service
            )
            conversions.append(conversion)
            if conversion.status != "failed":
                successful += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
    
    return ConvertAllResponse(
        conversions=conversions,
        successful=successful,
        failed=failed
    )


@router.get("", response_model=ConversionListResponse)
async def list_conversions(projectId: str):
    """List all conversions for a project."""
    return await ConversionService.list_conversions(projectId)


@router.get("/{conversion_id}", response_model=ConversionResponse)
async def get_conversion(conversion_id: str):
    """Get a conversion by ID."""
    conversion = await ConversionService.get_conversion(conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    return conversion


@router.post("/{conversion_id}/push", response_model=PushToBoomiResponse)
async def push_to_boomi(conversion_id: str):
    """Push converted component to Boomi."""
    # Get conversion
    conversion = await ConversionService.get_conversion(conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    if not conversion.boomiXml:
        raise HTTPException(status_code=400, detail="No Boomi XML generated")
    
    # Get customer settings
    customer = await CustomerService.get(conversion.customerId)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Push to Boomi
    success, message, component_info = await BoomiAPIService.create_component(
        settings=customer.settings.boomi,
        xml_content=conversion.boomiXml,
        customer_id=conversion.customerId,
        project_id=conversion.projectId
    )
    
    if success and component_info:
        # Update conversion with Boomi info
        await ConversionService.update_conversion_status(
            conversion_id=conversion_id,
            status="pushed",
            boomi_info=component_info.model_dump()
        )
        
        return PushToBoomiResponse(
            success=True,
            componentId=component_info.componentId,
            componentUrl=component_info.componentUrl,
            message=message
        )
    else:
        await ConversionService.update_conversion_status(
            conversion_id=conversion_id,
            status="failed"
        )
        
        return PushToBoomiResponse(
            success=False,
            message=message
        )


@router.post("/push-all")
async def push_all_to_boomi(projectId: str, customerId: str):
    """Push all converted components to Boomi."""
    # Get all conversions for project
    conversions_response = await ConversionService.list_conversions(projectId)
    
    # Get customer settings
    customer = await CustomerService.get(customerId)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    results = []
    successful = 0
    failed = 0
    
    for conversion in conversions_response.conversions:
        if conversion.status in ["converted", "validated"] and conversion.boomiXml:
            success, message, component_info = await BoomiAPIService.create_component(
                settings=customer.settings.boomi,
                xml_content=conversion.boomiXml,
                customer_id=customerId,
                project_id=projectId
            )
            
            if success and component_info:
                await ConversionService.update_conversion_status(
                    conversion_id=conversion.conversionId,
                    status="pushed",
                    boomi_info=component_info.model_dump()
                )
                successful += 1
            else:
                failed += 1
            
            results.append({
                "conversionId": conversion.conversionId,
                "sourceName": conversion.sourceName,
                "success": success,
                "message": message
            })
    
    return {
        "results": results,
        "successful": successful,
        "failed": failed,
        "total": len(results)
    }
