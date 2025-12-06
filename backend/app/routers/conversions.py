"""Conversion API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.database import db
import httpx
import base64

router = APIRouter(prefix="/api/conversions", tags=["conversions"])


def decrypt_api_token(encrypted_token: str) -> str:
    """Safely decrypt API token using cryptography directly"""
    if not encrypted_token:
        return ""
    try:
        # Import and use cryptography directly to avoid Pydantic issues
        from cryptography.fernet import Fernet
        import os
        
        encryption_key = os.getenv("ENCRYPTION_KEY", "")
        if not encryption_key:
            # No encryption key means token might be plaintext
            return encrypted_token
        
        fernet = Fernet(encryption_key.encode())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"[DECRYPT] Decryption issue: {e}, using token as-is")
        # If decryption fails, return the token as-is (might be plaintext)
        return encrypted_token


@router.post("/convert")
async def convert_component(data: dict):
    """Convert a webMethods component to Boomi"""
    from app.services.boomi_converter import convert_service
    
    project_id = data.get('projectId')
    service_name = data.get('serviceName')
    
    print(f"[CONVERT] Project: {project_id}, Service: {service_name}")
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
                service['type'] = 'DocumentType'
                break
    
    if not service:
        for svc in all_services:
            if service_name in svc.get('name', '') or svc.get('name', '').endswith(service_name):
                service = svc
                break
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")
    
    print(f"[CONVERT] Service type: {service.get('type')}, Name: {service.get('name')}")
    print(f"[CONVERT] Fields count: {len(service.get('fields', []))}")
    
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
    
    print(f"[PUSH] Starting push for project: {project_id}, component: {component_name}")
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    customer_id = project.get('customerId')
    customer = await db.customers.find_one({"customerId": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    boomi_settings = customer.get('settings', {}).get('boomi', {})
    account_id = boomi_settings.get('accountId', '')
    username = boomi_settings.get('username', '')
    encrypted_token = boomi_settings.get('apiToken', '')
    
    print(f"[PUSH] Account: {account_id}, Username: {username}, Token present: {bool(encrypted_token)}")
    
    # Decrypt the API token
    api_token = decrypt_api_token(encrypted_token)
    
    if not account_id or not username or not api_token:
        raise HTTPException(status_code=400, detail="Boomi credentials not configured")
    
    url = f"https://api.boomi.com/api/rest/v1/{account_id}/Component"
    
    auth_string = f"BOOMI_TOKEN.{username}:{api_token}"
    auth_b64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/xml",
        "Accept": "application/json"
    }
    
    print(f"[PUSH] Calling Boomi API: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=component_xml, headers=headers, timeout=30.0)
            
            print(f"[PUSH] Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    component_id = response_data.get('componentId', 'created')
                except:
                    component_id = 'created'
                
                return {
                    "success": True,
                    "message": "Component pushed to Boomi successfully",
                    "componentId": component_id,
                    "componentUrl": f"https://platform.boomi.com/AtomSphere.html#build;accountId={account_id}"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed - check Boomi credentials"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "message": "Access denied - check account permissions"
                }
            else:
                error_text = response.text[:500] if response.text else "Unknown error"
                print(f"[PUSH] Error response: {error_text}")
                return {
                    "success": False,
                    "message": f"Boomi API error: {response.status_code} - {error_text}"
                }
        except Exception as e:
            print(f"[PUSH] Exception: {str(e)}")
            return {
                "success": False,
                "message": f"Push failed: {str(e)}"
            }


@router.get("/list/{project_id}")
async def list_conversions(project_id: str):
    """List all conversions for a project"""
    conversions = await db.conversions.find({"projectId": project_id}).to_list(100)
    for conv in conversions:
        if '_id' in conv:
            del conv['_id']
    return {"conversions": conversions, "total": len(conversions)}


@router.get("/{conversion_id}")
async def get_conversion(conversion_id: str):
    """Get a specific conversion"""
    conversion = await db.conversions.find_one({"conversionId": conversion_id})
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if '_id' in conversion:
        del conversion['_id']
    return conversion
