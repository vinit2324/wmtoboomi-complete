"""
Project management API routes.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import PlainTextResponse

from app.models import (
    ProjectResponse,
    ProjectListResponse,
    FileTreeNode,
)
from app.services import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def upload_package(
    file: UploadFile = File(...),
    customerId: str = Form(...)
):
    """Upload a webMethods package ZIP file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")
    
    # Read file content
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    return await ProjectService.create_project(
        customer_id=customerId,
        file_name=file.filename,
        file_content=content
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(customerId: Optional[str] = None):
    """List all projects, optionally filtered by customer."""
    return await ProjectService.list_projects(customerId)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a project by ID."""
    project = await ProjectService.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/parse", response_model=ProjectResponse)
async def parse_project(project_id: str):
    """Parse uploaded webMethods package."""
    try:
        return await ProjectService.parse_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@router.post("/{project_id}/analyze", response_model=ProjectResponse)
async def analyze_project(project_id: str):
    """Analyze parsed project."""
    try:
        return await ProjectService.analyze_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Delete a project and its files."""
    success = await ProjectService.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}/files", response_model=FileTreeNode)
async def get_file_tree(project_id: str):
    """Get file tree for document viewer."""
    tree = await ProjectService.get_file_tree(project_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Project or package not found")
    return tree


@router.get("/{project_id}/files/{file_path:path}")
async def get_file_content(project_id: str, file_path: str):
    """Get file content for document viewer."""
    content, content_type = await ProjectService.get_file_content(project_id, file_path)
    
    if not content and content_type == "text/plain":
        raise HTTPException(status_code=404, detail="File not found")
    
    return PlainTextResponse(content=content, media_type=content_type)
