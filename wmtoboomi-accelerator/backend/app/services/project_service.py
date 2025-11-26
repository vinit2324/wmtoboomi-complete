"""
Project service for webMethods package upload and management.
"""
import os
import uuid
import shutil
import zipfile
from datetime import datetime
from typing import Optional, Tuple
import aiofiles

from app.database import get_projects_collection
from app.config import get_settings
from app.models import (
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    PackageInfo,
    ServiceStats,
    FlowVerbStats,
    ParsedData,
    AnalysisResults,
    FileTreeNode,
)
from app.services.parser_service import WebMethodsParser
from app.services.analysis_service import AnalysisService
from app.services.logging_service import log_activity


class ProjectService:
    """Service for managing migration projects."""
    
    @staticmethod
    def _get_upload_path(project_id: str) -> str:
        """Get upload directory path for a project."""
        settings = get_settings()
        return os.path.join(settings.upload_dir, project_id)
    
    @staticmethod
    async def create_project(
        customer_id: str,
        file_name: str,
        file_content: bytes
    ) -> ProjectResponse:
        """Create a new project and upload package."""
        projects = get_projects_collection()
        
        project_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create upload directory
        upload_path = ProjectService._get_upload_path(project_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save uploaded file
        package_path = os.path.join(upload_path, file_name)
        async with aiofiles.open(package_path, 'wb') as f:
            await f.write(file_content)
        
        # Get file size
        file_size = len(file_content)
        
        # Extract package name from filename
        package_name = os.path.splitext(file_name)[0]
        
        # Create initial project document
        doc = {
            "projectId": project_id,
            "customerId": customer_id,
            "packageName": package_name,
            "uploadedAt": now,
            "status": "uploaded",
            "packagePath": package_path,
            "packageInfo": PackageInfo(
                fileName=file_name,
                fileSize=file_size,
                services=ServiceStats(),
                flowVerbStats=FlowVerbStats(),
                wMPublicCallCount=0,
                customJavaCallCount=0
            ).model_dump(),
            "parsedData": None,
            "analysis": None,
            "errorMessage": None
        }
        
        await projects.insert_one(doc)
        
        await log_activity(
            action="package_uploaded",
            message=f"Package uploaded: {file_name}",
            category="upload",
            customer_id=customer_id,
            project_id=project_id,
            fileName=file_name,
            fileSize=file_size
        )
        
        return ProjectService._doc_to_response(doc)
    
    @staticmethod
    async def parse_project(project_id: str) -> ProjectResponse:
        """Parse uploaded webMethods package."""
        projects = get_projects_collection()
        
        # Get project
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            raise ValueError("Project not found")
        
        # Update status to parsing
        await projects.update_one(
            {"projectId": project_id},
            {"$set": {"status": "parsing"}}
        )
        
        try:
            package_path = doc.get("packagePath")
            if not package_path or not os.path.exists(package_path):
                raise ValueError("Package file not found")
            
            await log_activity(
                action="parsing_started",
                message="Starting package parsing",
                category="parse",
                customer_id=doc.get("customerId"),
                project_id=project_id
            )
            
            # Parse package
            with WebMethodsParser(package_path) as parser:
                package_info, parsed_data = parser.parse()
            
            # Update project with parsed data
            await projects.update_one(
                {"projectId": project_id},
                {
                    "$set": {
                        "status": "parsed",
                        "packageInfo": package_info.model_dump(),
                        "parsedData": parsed_data.model_dump(),
                        "errorMessage": None
                    }
                }
            )
            
            await log_activity(
                action="parsing_completed",
                message=f"Parsed {package_info.services.total} services, {len(parsed_data.documents)} documents",
                category="parse",
                customer_id=doc.get("customerId"),
                project_id=project_id,
                services=package_info.services.model_dump(),
                flowVerbs=package_info.flowVerbStats.model_dump()
            )
            
            # Get updated document
            doc = await projects.find_one({"projectId": project_id})
            return ProjectService._doc_to_response(doc)
            
        except Exception as e:
            await projects.update_one(
                {"projectId": project_id},
                {
                    "$set": {
                        "status": "failed",
                        "errorMessage": str(e)
                    }
                }
            )
            
            await log_activity(
                action="parsing_failed",
                message=f"Parsing failed: {str(e)}",
                category="parse",
                level="error",
                customer_id=doc.get("customerId"),
                project_id=project_id
            )
            
            doc = await projects.find_one({"projectId": project_id})
            return ProjectService._doc_to_response(doc)
    
    @staticmethod
    async def analyze_project(project_id: str) -> ProjectResponse:
        """Analyze parsed project."""
        projects = get_projects_collection()
        
        # Get project
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            raise ValueError("Project not found")
        
        if not doc.get("parsedData"):
            raise ValueError("Project not parsed yet")
        
        # Update status
        await projects.update_one(
            {"projectId": project_id},
            {"$set": {"status": "analyzing"}}
        )
        
        try:
            await log_activity(
                action="analysis_started",
                message="Starting project analysis",
                category="analyze",
                customer_id=doc.get("customerId"),
                project_id=project_id
            )
            
            # Perform analysis
            parsed_data = ParsedData(**doc["parsedData"])
            analysis = AnalysisService.analyze(parsed_data)
            
            # Update project with analysis
            await projects.update_one(
                {"projectId": project_id},
                {
                    "$set": {
                        "status": "analyzed",
                        "analysis": analysis.model_dump()
                    }
                }
            )
            
            await log_activity(
                action="analysis_completed",
                message=f"Analysis complete. Complexity: {analysis.complexity.overall}, Est. hours: {analysis.estimatedHours}",
                category="analyze",
                customer_id=doc.get("customerId"),
                project_id=project_id,
                complexity=analysis.complexity.overall,
                estimatedHours=analysis.estimatedHours,
                automationPotential=analysis.automationPotential
            )
            
            # Get updated document
            doc = await projects.find_one({"projectId": project_id})
            return ProjectService._doc_to_response(doc)
            
        except Exception as e:
            await projects.update_one(
                {"projectId": project_id},
                {"$set": {"status": "parsed"}}  # Revert to parsed status
            )
            
            await log_activity(
                action="analysis_failed",
                message=f"Analysis failed: {str(e)}",
                category="analyze",
                level="error",
                customer_id=doc.get("customerId"),
                project_id=project_id
            )
            
            raise
    
    @staticmethod
    async def get_project(project_id: str) -> Optional[ProjectResponse]:
        """Get a project by ID."""
        projects = get_projects_collection()
        
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            return None
        
        return ProjectService._doc_to_response(doc)
    
    @staticmethod
    async def list_projects(customer_id: Optional[str] = None) -> ProjectListResponse:
        """List all projects, optionally filtered by customer."""
        projects = get_projects_collection()
        
        query = {}
        if customer_id:
            query["customerId"] = customer_id
        
        cursor = projects.find(query).sort("uploadedAt", -1)
        
        project_list = []
        async for doc in cursor:
            project_list.append(ProjectService._doc_to_response(doc))
        
        return ProjectListResponse(
            projects=project_list,
            total=len(project_list)
        )
    
    @staticmethod
    async def delete_project(project_id: str) -> bool:
        """Delete a project and its files."""
        projects = get_projects_collection()
        
        # Get project
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            return False
        
        # Delete upload directory
        upload_path = ProjectService._get_upload_path(project_id)
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path, ignore_errors=True)
        
        # Delete from database
        result = await projects.delete_one({"projectId": project_id})
        
        if result.deleted_count > 0:
            await log_activity(
                action="project_deleted",
                message=f"Project deleted: {doc.get('packageName')}",
                category="system",
                customer_id=doc.get("customerId"),
                project_id=project_id
            )
            return True
        
        return False
    
    @staticmethod
    async def get_file_tree(project_id: str) -> Optional[FileTreeNode]:
        """Get file tree for document viewer."""
        projects = get_projects_collection()
        
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            return None
        
        package_path = doc.get("packagePath")
        if not package_path or not os.path.exists(package_path):
            return None
        
        with WebMethodsParser(package_path) as parser:
            return parser.get_file_tree()
    
    @staticmethod
    async def get_file_content(project_id: str, file_path: str) -> Tuple[str, str]:
        """Get file content for document viewer."""
        projects = get_projects_collection()
        
        doc = await projects.find_one({"projectId": project_id})
        if not doc:
            return "", "text/plain"
        
        package_path = doc.get("packagePath")
        if not package_path or not os.path.exists(package_path):
            return "", "text/plain"
        
        with WebMethodsParser(package_path) as parser:
            return parser.get_file_content(file_path)
    
    @staticmethod
    def _doc_to_response(doc: dict) -> ProjectResponse:
        """Convert MongoDB document to ProjectResponse."""
        return ProjectResponse(
            projectId=doc["projectId"],
            customerId=doc["customerId"],
            packageName=doc["packageName"],
            uploadedAt=doc["uploadedAt"],
            status=doc["status"],
            packageInfo=PackageInfo(**doc["packageInfo"]) if doc.get("packageInfo") else PackageInfo(
                fileName="",
                fileSize=0,
                services=ServiceStats(),
                flowVerbStats=FlowVerbStats(),
                wMPublicCallCount=0,
                customJavaCallCount=0
            ),
            parsedData=ParsedData(**doc["parsedData"]) if doc.get("parsedData") else None,
            analysis=AnalysisResults(**doc["analysis"]) if doc.get("analysis") else None,
            errorMessage=doc.get("errorMessage")
        )
