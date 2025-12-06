"""Project data models for Pydantic"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FlowVerbStats(BaseModel):
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
    package: str = ""
    service: str = ""
    count: int = 1


class ServiceStats(BaseModel):
    total: int = 0
    flow: int = 0
    adapter: int = 0
    java: int = 0
    map: int = 0
    document: int = 0


class PackageInfo(BaseModel):
    fileName: str = ""
    fileSize: int = 0
    services: ServiceStats = Field(default_factory=ServiceStats)
    flowVerbStats: FlowVerbStats = Field(default_factory=FlowVerbStats)
    wMPublicCallCount: int = 0
    customJavaCallCount: int = 0


class ParsedService(BaseModel):
    type: str = "FlowService"
    name: str = ""
    path: str = ""
    flowVerbs: Optional[FlowVerbStats] = None
    serviceInvocations: list = []
    pipelineComplexity: str = "low"
    adapters: list = []
    inputSignature: Optional[dict] = None
    outputSignature: Optional[dict] = None
    rawXml: Optional[str] = None
    flowSteps: list = []
    stepCount: int = 0


class ParsedDocument(BaseModel):
    name: str = ""
    path: str = ""
    fields: list = []
    nestedStructures: list = []
    isArray: bool = False
    dataType: str = "document"


class ParsedEdiSchema(BaseModel):
    name: str = ""
    path: str = ""
    type: str = "X12"
    transactionSet: str = ""
    segments: list = []


class ParsedManifest(BaseModel):
    packageName: str = ""
    version: str = ""
    dependencies: list = []
    startupServices: list = []
    shutdownServices: list = []
    requires: list = []


class ParsedData(BaseModel):
    manifest: ParsedManifest = Field(default_factory=ParsedManifest)
    services: list = []
    documents: list = []
    ediSchemas: list = []


class DependencyInfo(BaseModel):
    serviceName: str = ""
    dependsOn: list = []
    dependedBy: list = []


class ComplexityAnalysis(BaseModel):
    overall: str = "low"
    score: float = 0.0
    factors: dict = {}


class MigrationWave(BaseModel):
    waveNumber: int = 1
    services: list = []
    estimatedHours: float = 0.0
    dependencies: list = []


class AnalysisResults(BaseModel):
    dependencies: list = []
    complexity: ComplexityAnalysis = Field(default_factory=ComplexityAnalysis)
    estimatedHours: float = 0.0
    migrationWaves: list = []
    automationPotential: str = "0%"
    wMPublicServices: dict = {}


class ProjectCreate(BaseModel):
    customerId: str


class ProjectResponse(BaseModel):
    projectId: str
    customerId: str
    packageName: str
    uploadedAt: datetime
    status: str = "uploaded"
    packageInfo: PackageInfo = Field(default_factory=PackageInfo)
    parsedData: Optional[ParsedData] = None
    analysis: Optional[AnalysisResults] = None
    errorMessage: Optional[str] = None


class ProjectListResponse(BaseModel):
    projects: list = []
    total: int = 0


class FileTreeNode(BaseModel):
    name: str = ""
    path: str = ""
    type: str = "file"
    children: list = []
    size: Optional[int] = None
    extension: Optional[str] = None
