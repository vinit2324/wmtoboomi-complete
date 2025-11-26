"""
Project data models for webMethods package parsing and analysis.
"""
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class FlowVerbStats(BaseModel):
    """Statistics for flow verb usage."""
    map: int = 0
    branch: int = 0
    loop: int = 0
    repeat: int = 0
    sequence: int = 0
    tryCatch: int = 0
    tryFinally: int = 0
    catch: int = 0
    finally_: int = Field(0, alias="finally")
    exit: int = 0
    
    class Config:
        populate_by_name = True


class ServiceInvocation(BaseModel):
    """Reference to a service invocation."""
    package: str
    service: str
    count: int = 1


class ServiceStats(BaseModel):
    """Statistics for services in a package."""
    total: int = 0
    flow: int = 0
    adapter: int = 0
    java: int = 0
    map: int = 0
    document: int = 0


class PackageInfo(BaseModel):
    """Information about the uploaded package."""
    fileName: str
    fileSize: int
    services: ServiceStats = Field(default_factory=ServiceStats)
    flowVerbStats: FlowVerbStats = Field(default_factory=FlowVerbStats)
    wMPublicCallCount: int = 0
    customJavaCallCount: int = 0


class ParsedService(BaseModel):
    """Parsed service data."""
    type: Literal["FlowService", "JavaService", "AdapterService", "MapService", "DocumentType"]
    name: str
    path: str
    flowVerbs: Optional[FlowVerbStats] = None
    serviceInvocations: list[ServiceInvocation] = []
    pipelineComplexity: Literal["low", "medium", "high"] = "low"
    adapters: list[str] = []
    inputSignature: Optional[dict] = None
    outputSignature: Optional[dict] = None
    rawXml: Optional[str] = None


class ParsedDocument(BaseModel):
    """Parsed document type data."""
    name: str
    path: str
    fields: list[dict] = []
    nestedStructures: list[str] = []
    isArray: bool = False
    dataType: str = "document"


class ParsedEdiSchema(BaseModel):
    """Parsed EDI schema data."""
    name: str
    path: str
    type: Literal["X12", "EDIFACT"] = "X12"
    transactionSet: str = ""
    segments: list[dict] = []


class ParsedManifest(BaseModel):
    """Parsed manifest.v3 data."""
    packageName: str = ""
    version: str = ""
    dependencies: list[str] = []
    startupServices: list[str] = []
    shutdownServices: list[str] = []
    requires: list[dict] = []


class ParsedData(BaseModel):
    """Complete parsed package data."""
    manifest: ParsedManifest = Field(default_factory=ParsedManifest)
    services: list[ParsedService] = []
    documents: list[ParsedDocument] = []
    ediSchemas: list[ParsedEdiSchema] = []


class DependencyInfo(BaseModel):
    """Service dependency information."""
    serviceName: str
    dependsOn: list[str] = []
    dependedBy: list[str] = []


class ComplexityAnalysis(BaseModel):
    """Complexity analysis results."""
    overall: Literal["low", "medium", "high"] = "low"
    score: float = 0.0
    factors: dict = {}


class MigrationWave(BaseModel):
    """Migration wave grouping."""
    waveNumber: int
    services: list[str]
    estimatedHours: float
    dependencies: list[str] = []


class AnalysisResults(BaseModel):
    """Complete analysis results."""
    dependencies: list[DependencyInfo] = []
    complexity: ComplexityAnalysis = Field(default_factory=ComplexityAnalysis)
    estimatedHours: float = 0.0
    migrationWaves: list[MigrationWave] = []
    automationPotential: str = "0%"
    wMPublicServices: dict[str, int] = {}  # service -> count


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    customerId: str


class ProjectResponse(BaseModel):
    """Response model for project data."""
    projectId: str
    customerId: str
    packageName: str
    uploadedAt: datetime
    status: Literal["uploaded", "parsing", "parsed", "analyzing", "analyzed", "failed"]
    packageInfo: PackageInfo
    parsedData: Optional[ParsedData] = None
    analysis: Optional[AnalysisResults] = None
    errorMessage: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response model for list of projects."""
    projects: list[ProjectResponse]
    total: int


class FileTreeNode(BaseModel):
    """File tree node for document viewer."""
    name: str
    path: str
    type: Literal["file", "folder"]
    children: list["FileTreeNode"] = []
    size: Optional[int] = None
    extension: Optional[str] = None


FileTreeNode.model_rebuild()
