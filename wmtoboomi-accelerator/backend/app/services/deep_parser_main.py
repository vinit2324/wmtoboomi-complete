"""
Deep Parser Engine - Main Parser
Unified parser for webMethods packages

Combines:
- Package extraction
- Manifest parsing
- node.ndf parsing
- flow.xml parsing
- Pipeline analysis
- Complexity calculation
"""

import os
import re
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Generator
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
import logging
import json

from app.services.deep_parser_core import (
    ServiceType, AdapterType, ParsedService, ParsedDocumentType,
    ServiceSignature, PipelineVariable, DocumentField,
    NodeNDFParser, AdapterConfigParser
)
from app.services.deep_parser_flow import (
    FlowXMLParser, PipelineAnalyzer, ComplexityAnalyzer, FlowStep
)
from app.services.wmpublic_master import get_catalog

logger = logging.getLogger(__name__)


# =============================================================================
# MANIFEST PARSER
# =============================================================================

@dataclass
class ManifestInfo:
    """Parsed manifest information"""
    package_name: str = ""
    version: str = ""
    build: str = ""
    requires: List[str] = field(default_factory=list)
    startup_services: List[str] = field(default_factory=list)
    shutdown_services: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)


class ManifestParser:
    """Parser for webMethods manifest.v3 files"""
    
    def parse(self, content: str) -> ManifestInfo:
        """Parse manifest content"""
        manifest = ManifestInfo()
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Section markers
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue
            
            # Key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Map to manifest fields
                if key.lower() == 'name':
                    manifest.package_name = value
                elif key.lower() == 'version':
                    manifest.version = value
                elif key.lower() == 'build':
                    manifest.build = value
                elif key.lower() == 'requires' or current_section == 'requires':
                    if value:
                        manifest.requires.append(value)
                elif key.lower() == 'startup' or current_section == 'startup':
                    if value:
                        manifest.startup_services.append(value)
                elif key.lower() == 'shutdown' or current_section == 'shutdown':
                    if value:
                        manifest.shutdown_services.append(value)
                else:
                    manifest.properties[key] = value
            
            # Handle property format without =
            elif current_section == 'requires':
                manifest.requires.append(line)
        
        return manifest


# =============================================================================
# PACKAGE STRUCTURE ANALYZER
# =============================================================================

@dataclass
class PackageFile:
    """Represents a file in the package"""
    relative_path: str
    full_path: str
    file_type: str  # 'ndf', 'flow', 'java', 'xml', etc.
    service_type: Optional[ServiceType] = None
    namespace: str = ""
    service_name: str = ""


class PackageStructureAnalyzer:
    """Analyzes webMethods package structure"""
    
    # File patterns
    FILE_PATTERNS = {
        'node.ndf': 'ndf',
        'flow.xml': 'flow',
        '.java': 'java',
        'java.frag': 'java_compiled',
        '.xml': 'xml',
        'manifest.v3': 'manifest',
    }
    
    # Service type detection patterns
    SERVICE_PATTERNS = {
        ServiceType.FLOW_SERVICE: ['flow.xml'],
        ServiceType.JAVA_SERVICE: ['java.frag', '.java'],
        ServiceType.ADAPTER_SERVICE: ['adapter', 'jdbc', 'sap', 'http'],
        ServiceType.DOCUMENT_TYPE: ['document', 'doctype', 'rec'],
        ServiceType.MAP_SERVICE: ['map'],
    }
    
    def analyze_directory(self, root_path: str) -> List[PackageFile]:
        """Analyze extracted package directory"""
        files = []
        root = Path(root_path)
        
        for file_path in root.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(root))
                pf = self._classify_file(rel_path, str(file_path))
                if pf:
                    files.append(pf)
        
        return files
    
    def _classify_file(self, rel_path: str, full_path: str) -> Optional[PackageFile]:
        """Classify a file by type"""
        filename = os.path.basename(rel_path)
        
        # Determine file type
        file_type = 'unknown'
        for pattern, ftype in self.FILE_PATTERNS.items():
            if pattern in filename.lower():
                file_type = ftype
                break
        
        # Skip unknown types
        if file_type == 'unknown':
            return None
        
        # Extract namespace and service name from path
        # Pattern: ns/folder/subfolder/ServiceName/node.ndf
        parts = rel_path.replace('\\', '/').split('/')
        
        namespace = ""
        service_name = ""
        
        # Find ns folder
        ns_idx = -1
        for i, part in enumerate(parts):
            if part == 'ns':
                ns_idx = i
                break
        
        if ns_idx >= 0 and len(parts) > ns_idx + 2:
            # Namespace is everything between ns and the service folder
            namespace_parts = parts[ns_idx + 1:-1]
            namespace = '.'.join(namespace_parts[:-1]) if len(namespace_parts) > 1 else ''
            service_name = namespace_parts[-1] if namespace_parts else ''
        
        # Detect service type from path
        service_type = self._detect_service_type(rel_path, full_path)
        
        return PackageFile(
            relative_path=rel_path,
            full_path=full_path,
            file_type=file_type,
            service_type=service_type,
            namespace=namespace,
            service_name=service_name
        )
    
    def _detect_service_type(self, rel_path: str, full_path: str) -> Optional[ServiceType]:
        """Detect service type from path and content hints"""
        path_lower = rel_path.lower()
        
        # Check for flow.xml presence
        if 'flow.xml' in path_lower:
            return ServiceType.FLOW_SERVICE
        
        # Check for Java service
        if 'java.frag' in path_lower or path_lower.endswith('.java'):
            return ServiceType.JAVA_SERVICE
        
        # Check for adapter indicators
        for adapter_hint in ['adapter', 'jdbc', 'sap']:
            if adapter_hint in path_lower:
                return ServiceType.ADAPTER_SERVICE
        
        # Check for document type
        if 'rec' in path_lower or 'document' in path_lower:
            return ServiceType.DOCUMENT_TYPE
        
        # Default to unknown, will be determined from node.ndf
        return None


# =============================================================================
# MAIN DEEP PARSER
# =============================================================================

@dataclass
class PackageParseResult:
    """Complete parse result for a package"""
    manifest: ManifestInfo = field(default_factory=ManifestInfo)
    services: List[ParsedService] = field(default_factory=list)
    document_types: List[ParsedDocumentType] = field(default_factory=list)
    files: List[PackageFile] = field(default_factory=list)
    
    # Statistics
    total_services: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    total_flow_verbs: Dict[str, int] = field(default_factory=dict)
    total_wmpublic_calls: int = 0
    total_custom_calls: int = 0
    unique_wmpublic_services: List[str] = field(default_factory=list)
    
    # Complexity summary
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    estimated_total_hours: float = 0
    overall_automation_potential: int = 0
    
    # Issues/warnings
    parse_errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)


class DeepParser:
    """
    Main parser for webMethods packages.
    
    Combines all parsing functionality:
    - Extract ZIP
    - Parse manifest
    - Parse all services (node.ndf + flow.xml)
    - Analyze complexity
    - Track pipeline state
    """
    
    def __init__(self):
        self.manifest_parser = ManifestParser()
        self.structure_analyzer = PackageStructureAnalyzer()
        self.ndf_parser = NodeNDFParser()
        self.flow_parser = FlowXMLParser()
        self.adapter_parser = AdapterConfigParser()
        self.pipeline_analyzer = PipelineAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.wmpublic_catalog = get_catalog()
        
        self._temp_dir: Optional[str] = None
        self._extract_path: Optional[str] = None
    
    @contextmanager
    def parse_package(self, zip_path: str) -> Generator[PackageParseResult, None, None]:
        """
        Parse a webMethods package ZIP file.
        Use as context manager to ensure cleanup.
        """
        result = PackageParseResult()
        
        try:
            # Create temp directory
            self._temp_dir = tempfile.mkdtemp(prefix='wm_parse_')
            
            # Extract ZIP
            self._extract_path = self._extract_zip(zip_path)
            
            # Analyze structure
            result.files = self.structure_analyzer.analyze_directory(self._extract_path)
            
            # Parse manifest
            manifest_path = self._find_manifest()
            if manifest_path:
                result.manifest = self._parse_manifest(manifest_path)
            
            # Parse all services
            result.services, result.document_types = self._parse_all_services(result.files)
            
            # Calculate statistics
            self._calculate_statistics(result)
            
            yield result
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            result.parse_errors.append({
                'type': 'general',
                'message': str(e)
            })
            yield result
            
        finally:
            # Cleanup
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
    
    def _extract_zip(self, zip_path: str) -> str:
        """Extract ZIP file to temp directory"""
        extract_path = os.path.join(self._temp_dir, 'extracted')
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_path)
        
        # Find actual package root (sometimes nested)
        for item in os.listdir(extract_path):
            item_path = os.path.join(extract_path, item)
            if os.path.isdir(item_path):
                # Check if this looks like package root (has ns/ or manifest.v3)
                if (os.path.exists(os.path.join(item_path, 'ns')) or
                    os.path.exists(os.path.join(item_path, 'manifest.v3'))):
                    return item_path
        
        return extract_path
    
    def _find_manifest(self) -> Optional[str]:
        """Find manifest.v3 file"""
        for root, dirs, files in os.walk(self._extract_path):
            if 'manifest.v3' in files:
                return os.path.join(root, 'manifest.v3')
        return None
    
    def _parse_manifest(self, path: str) -> ManifestInfo:
        """Parse manifest file"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.manifest_parser.parse(content)
        except Exception as e:
            logger.warning(f"Manifest parse error: {e}")
            return ManifestInfo()
    
    def _parse_all_services(self, files: List[PackageFile]) -> Tuple[List[ParsedService], List[ParsedDocumentType]]:
        """Parse all services from package files"""
        services = []
        documents = []
        
        # Group files by service
        service_files: Dict[str, Dict[str, PackageFile]] = {}
        
        for pf in files:
            key = f"{pf.namespace}.{pf.service_name}" if pf.namespace else pf.service_name
            if key not in service_files:
                service_files[key] = {}
            service_files[key][pf.file_type] = pf
        
        # Parse each service
        for service_key, file_dict in service_files.items():
            try:
                # Parse node.ndf first
                ndf_file = file_dict.get('ndf')
                if not ndf_file:
                    continue
                
                service, doc_type = self._parse_service(
                    service_key, 
                    ndf_file,
                    file_dict.get('flow'),
                    file_dict.get('java') or file_dict.get('java_compiled')
                )
                
                if service:
                    services.append(service)
                if doc_type:
                    documents.append(doc_type)
                    
            except Exception as e:
                logger.warning(f"Error parsing {service_key}: {e}")
        
        return services, documents
    
    def _parse_service(self, service_key: str, 
                       ndf_file: PackageFile,
                       flow_file: Optional[PackageFile] = None,
                       java_file: Optional[PackageFile] = None) -> Tuple[Optional[ParsedService], Optional[ParsedDocumentType]]:
        """Parse a single service"""
        
        # Read node.ndf
        with open(ndf_file.full_path, 'rb') as f:
            ndf_content = f.read()
        
        # Parse node.ndf
        ndf_xml, parse_method = self.ndf_parser.parse(ndf_content)
        
        if ndf_xml is None:
            logger.warning(f"Could not parse node.ndf for {service_key}")
            return None, None
        
        # Determine service type
        service_type = self._determine_service_type(ndf_xml, ndf_file, flow_file)
        
        # Handle Document Type
        if service_type == ServiceType.DOCUMENT_TYPE:
            doc_type = self._parse_document_type(service_key, ndf_xml, ndf_content)
            return None, doc_type
        
        # Create service
        service = ParsedService(
            name=ndf_file.service_name or service_key.split('.')[-1],
            full_path=service_key,
            type=service_type,
            package_name=ndf_file.namespace or service_key.split('.')[0],
            raw_ndf=self.ndf_parser.decoded_content
        )
        
        # Parse signature
        service.signature = self.ndf_parser.parse_service_signature(ndf_xml)
        
        # Parse flow.xml if present
        if flow_file and service_type == ServiceType.FLOW_SERVICE:
            self._parse_flow_service(service, flow_file)
        
        # Handle adapter service
        if service_type == ServiceType.ADAPTER_SERVICE:
            self._parse_adapter_service(service, ndf_xml, ndf_content)
        
        # Handle Java service
        if service_type == ServiceType.JAVA_SERVICE and java_file:
            self._parse_java_service(service, java_file)
        
        # Calculate complexity
        complexity_result = self.complexity_analyzer.calculate(service)
        service.complexity_score = complexity_result['score']
        service.complexity_level = complexity_result['level']
        service.complexity_factors = complexity_result['factors']
        
        return service, None
    
    def _determine_service_type(self, ndf_xml, ndf_file: PackageFile, 
                               flow_file: Optional[PackageFile]) -> ServiceType:
        """Determine service type from parsed data"""
        
        # If flow.xml exists, it's a flow service
        if flow_file:
            return ServiceType.FLOW_SERVICE
        
        # Check ndf_file's detected type
        if ndf_file.service_type:
            return ndf_file.service_type
        
        # Check XML content for hints
        xml_str = self.ndf_parser.decoded_content.lower()
        
        if 'adapterservice' in xml_str or 'adapter' in xml_str:
            return ServiceType.ADAPTER_SERVICE
        if 'javaservice' in xml_str or 'java.frag' in xml_str:
            return ServiceType.JAVA_SERVICE
        if 'doctype' in xml_str or 'record' in xml_str:
            return ServiceType.DOCUMENT_TYPE
        if 'mapservice' in xml_str:
            return ServiceType.MAP_SERVICE
        
        return ServiceType.UNKNOWN
    
    def _parse_flow_service(self, service: ParsedService, flow_file: PackageFile):
        """Parse flow.xml and enrich service"""
        try:
            with open(flow_file.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                flow_content = f.read()
            
            service.raw_flow_xml = flow_content
            
            # Parse flow
            steps, verb_counts = self.flow_parser.parse(flow_content)
            service.flow_steps = steps
            service.verb_counts = verb_counts
            
            # Extract service invocations
            wmpublic, custom = self.flow_parser.extract_service_invocations(steps)
            service.wmpublic_calls = wmpublic
            service.custom_calls = custom
            
            # Collect all invocations
            service.service_invocations = []
            self._collect_invocations(steps, service.service_invocations)
            
        except Exception as e:
            logger.warning(f"Flow parse error for {service.name}: {e}")
    
    def _collect_invocations(self, steps: List[FlowStep], invocations: List):
        """Recursively collect all service invocations"""
        for step in steps:
            if step.service_invocation:
                invocations.append(step.service_invocation)
            self._collect_invocations(step.children, invocations)
            for branch in step.branches:
                self._collect_invocations(branch.steps, invocations)
    
    def _parse_adapter_service(self, service: ParsedService, ndf_xml, ndf_content: bytes):
        """Parse adapter service configuration"""
        content_str = ndf_content.decode('utf-8', errors='ignore')
        
        # Detect adapter type
        service.adapter_type = self.adapter_parser.detect_adapter_type(content_str)
        
        # Parse specific adapter config
        if service.adapter_type == AdapterType.JDBC:
            service.adapter_config = self.adapter_parser.parse_jdbc_adapter(ndf_xml, content_str)
        elif service.adapter_type == AdapterType.HTTP:
            service.adapter_config = self.adapter_parser.parse_http_adapter(ndf_xml, content_str)
        elif service.adapter_type == AdapterType.SAP:
            service.adapter_config = self.adapter_parser.parse_sap_adapter(ndf_xml, content_str)
        else:
            service.adapter_config = {'type': service.adapter_type.value}
    
    def _parse_java_service(self, service: ParsedService, java_file: PackageFile):
        """Parse Java service"""
        try:
            with open(java_file.full_path, 'rb') as f:
                content = f.read()
            
            # Try to decode
            try:
                java_content = content.decode('utf-8')
            except:
                java_content = "[Binary content - java.frag]"
            
            service.adapter_config = {
                'type': 'Java',
                'source_file': java_file.relative_path,
                'is_compiled': java_file.file_type == 'java_compiled'
            }
            
        except Exception as e:
            logger.warning(f"Java service parse error: {e}")
    
    def _parse_document_type(self, service_key: str, ndf_xml, 
                            ndf_content: bytes) -> ParsedDocumentType:
        """Parse document type definition"""
        doc = ParsedDocumentType(
            name=service_key.split('.')[-1],
            full_path=service_key,
            package_name='.'.join(service_key.split('.')[:-1]),
            raw_ndf=self.ndf_parser.decoded_content
        )
        
        # Extract fields
        doc.fields = self.ndf_parser.parse_document_type(ndf_xml)
        
        return doc
    
    def _calculate_statistics(self, result: PackageParseResult):
        """Calculate aggregate statistics"""
        
        result.total_services = len(result.services)
        
        # Count by type
        result.by_type = {}
        for svc in result.services:
            type_name = svc.type.value
            result.by_type[type_name] = result.by_type.get(type_name, 0) + 1
        
        # Aggregate verb counts
        result.total_flow_verbs = {}
        for svc in result.services:
            for verb, count in svc.verb_counts.items():
                result.total_flow_verbs[verb] = result.total_flow_verbs.get(verb, 0) + count
        
        # Count invocations
        all_wmpublic = []
        all_custom = []
        for svc in result.services:
            all_wmpublic.extend(svc.wmpublic_calls)
            all_custom.extend(svc.custom_calls)
        
        result.total_wmpublic_calls = len(all_wmpublic)
        result.total_custom_calls = len(all_custom)
        result.unique_wmpublic_services = list(set(all_wmpublic))
        
        # Complexity distribution
        result.complexity_distribution = {'low': 0, 'medium': 0, 'high': 0}
        total_hours = 0
        total_automation = 0
        
        for svc in result.services:
            level = svc.complexity_level
            result.complexity_distribution[level] = result.complexity_distribution.get(level, 0) + 1
            
            estimate = self.complexity_analyzer.estimate_conversion_hours(svc)
            total_hours += estimate['estimated_hours']
            total_automation += estimate['automation_percentage']
        
        result.estimated_total_hours = round(total_hours, 1)
        if result.total_services > 0:
            result.overall_automation_potential = round(total_automation / result.total_services)
    
    # File access methods for document viewer
    def get_file_tree(self, extract_path: str = None) -> Dict:
        """Get file tree for document viewer"""
        path = extract_path or self._extract_path
        if not path:
            return {}
        
        return self._build_file_tree(path)
    
    def _build_file_tree(self, root_path: str, prefix: str = "") -> Dict:
        """Build file tree recursively"""
        tree = {
            'name': os.path.basename(root_path) or 'Package',
            'type': 'directory',
            'children': []
        }
        
        try:
            items = sorted(os.listdir(root_path))
            for item in items:
                item_path = os.path.join(root_path, item)
                
                if os.path.isdir(item_path):
                    child = self._build_file_tree(item_path, f"{prefix}/{item}")
                    tree['children'].append(child)
                else:
                    tree['children'].append({
                        'name': item,
                        'type': 'file',
                        'path': f"{prefix}/{item}".lstrip('/'),
                        'size': os.path.getsize(item_path)
                    })
        except Exception as e:
            logger.warning(f"Error building file tree: {e}")
        
        return tree
    
    def get_file_content(self, file_path: str) -> Tuple[str, str]:
        """Get file content with type detection"""
        full_path = os.path.join(self._extract_path, file_path)
        
        if not os.path.exists(full_path):
            return "File not found", "text/plain"
        
        # Determine content type
        filename = os.path.basename(file_path).lower()
        
        if filename == 'node.ndf':
            # Parse and pretty-print node.ndf
            with open(full_path, 'rb') as f:
                content = f.read()
            xml, _ = self.ndf_parser.parse(content)
            if xml is not None:
                return etree.tostring(xml, pretty_print=True, encoding='unicode'), 'application/xml'
            return self.ndf_parser.decoded_content or "[Could not decode]", 'text/plain'
        
        elif filename == 'flow.xml' or filename.endswith('.xml'):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Pretty-print XML
                try:
                    from lxml import etree
                    tree = etree.fromstring(content.encode())
                    return etree.tostring(tree, pretty_print=True, encoding='unicode'), 'application/xml'
                except:
                    return content, 'application/xml'
            except:
                return "[Could not read file]", 'text/plain'
        
        elif filename.endswith('.java'):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(), 'text/x-java'
        
        elif filename == 'java.frag':
            return "[Compiled Java bytecode - cannot display]", 'text/plain'
        
        else:
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(), 'text/plain'
            except:
                return "[Binary file]", 'application/octet-stream'


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def parse_package_quick(zip_path: str) -> Dict[str, Any]:
    """Quick parse that returns dict (for JSON serialization)"""
    parser = DeepParser()
    
    with parser.parse_package(zip_path) as result:
        return {
            'manifest': asdict(result.manifest),
            'total_services': result.total_services,
            'by_type': result.by_type,
            'total_flow_verbs': result.total_flow_verbs,
            'total_wmpublic_calls': result.total_wmpublic_calls,
            'unique_wmpublic_services': result.unique_wmpublic_services,
            'complexity_distribution': result.complexity_distribution,
            'estimated_total_hours': result.estimated_total_hours,
            'overall_automation_potential': result.overall_automation_potential,
            'services': [
                {
                    'name': s.name,
                    'full_path': s.full_path,
                    'type': s.type.value,
                    'complexity_level': s.complexity_level,
                    'complexity_score': s.complexity_score,
                    'verb_counts': s.verb_counts,
                    'wmpublic_calls': len(s.wmpublic_calls),
                    'custom_calls': len(s.custom_calls),
                }
                for s in result.services
            ],
            'document_types': [
                {
                    'name': d.name,
                    'full_path': d.full_path,
                    'field_count': len(d.fields),
                }
                for d in result.document_types
            ],
            'parse_errors': result.parse_errors,
            'warnings': result.warnings,
        }


__all__ = [
    'DeepParser',
    'PackageParseResult',
    'ManifestInfo',
    'parse_package_quick',
]
