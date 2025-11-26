"""Integration analysis routes"""
from fastapi import APIRouter, HTTPException
from app.database import db
from app.services.integration_analyzer import analyze_integrations

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

@router.get("/{project_id}")
async def get_integrations(project_id: str):
    """Get integration patterns for a project"""
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Analyze integrations
    analysis = analyze_integrations(project['parsedData'])
    
    return analysis

@router.get("/{project_id}/{integration_name}/steps")
async def get_integration_steps(project_id: str, integration_name: str):
    """Get implementation steps for specific integration"""
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    analysis = analyze_integrations(project['parsedData'])
    
    # Find the integration
    integration = None
    for integ in analysis['integrations']:
        if integ['name'] == integration_name:
            integration = integ
            break
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {
        'integration': integration,
        'steps': integration.get('boomiSteps', [])
    }
