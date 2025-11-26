"""Conversion API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from pathlib import Path
from app.database import db
from app.services.boomi_converter import convert_service
from app.services.file_extractor import get_service_source_files
import httpx
import base64

router = APIRouter(prefix="/api/conversions", tags=["conversions"])

@router.post("/convert")
async def convert_component(data: dict):
    """Convert a webMethods component to Boomi"""
    
    project_id = data.get('projectId')
    service_name = data.get('serviceName')
    
    print(f"[CONVERT] Project: {project_id}, Service: {service_name}")
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Search in services
    service = None
    all_services = project.get('parsedData', {}).get('services', [])
    for svc in all_services:
        if svc.get('name') == service_name:
            service = svc
            break
    
    # If not found in services, search in documents
    if not service:
        all_documents = project.get('parsedData', {}).get('documents', [])
        for doc in all_documents:
            if doc.get('name') == service_name:
                service = doc
                service['type'] = 'DocumentType'  # Ensure type is set
                break
    
    # If still not found, try partial match
    if not service:
        for svc in all_services:
            if service_name in svc.get('name', '') or svc.get('name', '').endswith(service_name):
                service = svc
                print(f"[CONVERT] Found by partial match: {svc.get('name')}")
                break
    
    if not service:
        print(f"[CONVERT] Service not found: {service_name}")
        print(f"[CONVERT] Available services: {[s.get('name') for s in all_services[:10]]}")
        print(f"[CONVERT] Available documents: {[d.get('name') for d in project.get('parsedData', {}).get('documents', [])[:10]]}")
        raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")
    
    print(f"[CONVERT] Found service: {service.get('name')} of type {service.get('type')}")
    
    result = convert_service(service)
    
    conversion = {
        "conversionId": str(datetime.utcnow().timestamp()),
        "projectId": project_id,
        "serviceName": service_name,
        "serviceType": service.get('type', 'Unknown'),
        "componentType": result['componentType'],
        "boomiXml": result['boomiXml'],
        "automationLevel": result['automationLevel'],
        "convertedAt": datetime.utcnow(),
        "status": "converted"
    }
    
    await db.conversions.insert_one(conversion)
    
    return result

@router.post("/push-to-boomi")
async def push_to_boomi(data: dict):
    """Push converted component to Boomi"""
    
    project_id = data.get('projectId')
    component_xml = data.get('componentXml')
    component_name = data.get('componentName')
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    customer = await db.customers.find_one({"customerId": project.get('customerId')})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    boomi_settings = customer.get('settings', {}).get('boomi', {})
    account_id = boomi_settings.get('accountId')
    username = boomi_settings.get('username')
    api_token = boomi_settings.get('apiToken')
    
    if not all([account_id, username, api_token]):
        raise HTTPException(status_code=400, detail="Boomi credentials not configured for this customer")
    
    url = f"https://api.boomi.com/api/rest/v1/{account_id}/Component"
    
    auth_string = f"BOOMI_TOKEN.{username}:{api_token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/xml"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=component_xml, headers=headers, timeout=30.0)
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": "Component pushed to Boomi successfully",
                    "componentId": "generated-by-boomi",
                    "componentUrl": f"https://platform.boomi.com/AtomSphere.html#build;componentId=..."
                }
            else:
                return {
                    "success": False,
                    "message": f"Boomi API error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Push failed: {str(e)}"
            }

@router.get("/view-source/{project_id}")
async def view_source(project_id: str, service_name: str):
    """Get actual source file contents for a service"""
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find service
    service = None
    all_services = project.get('parsedData', {}).get('services', [])
    for svc in all_services:
        if svc.get('name') == service_name:
            service = svc
            break
    
    if not service:
        all_documents = project.get('parsedData', {}).get('documents', [])
        for doc in all_documents:
            if doc.get('name') == service_name:
                service = doc
                break
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get the uploaded package path
    package_filename = project.get('packageInfo', {}).get('fileName')
    if not package_filename:
        package_filename = f"{project['packageName']}.zip"
    
    package_path = Path("uploads") / package_filename
    
    if not package_path.exists():
        return {
            "service": {
                "name": service.get('name'),
                "type": service.get('type'),
                "path": service.get('path', '')
            },
            "files": {}
        }
    
    # Extract actual file contents
    service_path = service.get('path', '')
    files = get_service_source_files(str(package_path), service_path)
    
    return {
        "service": {
            "name": service.get('name'),
            "type": service.get('type'),
            "path": service_path
        },
        "files": files
    }

@router.get("/list/{project_id}")
async def list_conversions(project_id: str):
    """List all conversions for a project"""
    
    conversions = []
    async for conv in db.conversions.find({"projectId": project_id}).sort("convertedAt", -1):
        conv["_id"] = str(conv["_id"])
        conversions.append(conv)
    
    return {
        "conversions": conversions,
        "total": len(conversions)
    }
