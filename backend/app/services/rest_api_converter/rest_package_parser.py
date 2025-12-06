"""
REST Package Parser
===================
Parses webMethods REST API packages extracting:
- REST resource definitions (restv2.cnf/restv2.rad)
- Service signatures (node.ndf)
- Java service code (java.frag)
- Flow service logic (flow.xml)
- Global variables
- Package dependencies

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import zipfile
import re
import xml.etree.ElementTree as ET
import logging
import subprocess
import tempfile
import os
import shutil

logger = logging.getLogger(__name__)


@dataclass
class SignatureField:
    """Field in service signature"""
    name: str
    field_type: str = "string"
    is_array: bool = False
    is_optional: bool = True
    children: List['SignatureField'] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = {
            'name': self.name,
            'type': self.field_type,
            'isArray': self.is_array,
            'isOptional': self.is_optional
        }
        if self.children:
            result['children'] = [c.to_dict() for c in self.children]
        return result


@dataclass
class ServiceSignature:
    """Input/output signatures from node.ndf"""
    service_name: str
    inputs: List[SignatureField] = field(default_factory=list)
    outputs: List[SignatureField] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'serviceName': self.service_name,
            'inputs': [f.to_dict() for f in self.inputs],
            'outputs': [f.to_dict() for f in self.outputs]
        }


@dataclass
class RESTOperation:
    """REST API operation (endpoint)"""
    path: str
    method: str
    service_name: str
    parameters: List[Dict] = field(default_factory=list)
    consumes: str = "application/json"
    produces: str = "application/json"
    
    def to_dict(self) -> Dict:
        return {
            'path': self.path,
            'method': self.method,
            'serviceName': self.service_name,
            'parameters': self.parameters,
            'consumes': self.consumes,
            'produces': self.produces
        }


@dataclass
class RESTResource:
    """REST resource with base path and operations"""
    name: str
    base_path: str
    version: str = ""
    operations: List[RESTOperation] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'basePath': self.base_path,
            'version': self.version,
            'operations': [o.to_dict() for o in self.operations]
        }


@dataclass
class JavaService:
    """Java service with source code"""
    name: str
    path: str
    code: str
    method_name: str = ""
    referenced_variables: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'path': self.path,
            'code': self.code,
            'methodName': self.method_name,
            'referencedVariables': self.referenced_variables
        }


@dataclass
class FlowService:
    """Flow service with invocations and complexity"""
    name: str
    path: str
    invocations: List[str] = field(default_factory=list)
    has_http_invoke: bool = False
    complexity: str = "medium"
    map_count: int = 0
    branch_count: int = 0
    loop_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'path': self.path,
            'invocations': self.invocations,
            'hasHttpInvoke': self.has_http_invoke,
            'complexity': self.complexity,
            'mapCount': self.map_count,
            'branchCount': self.branch_count,
            'loopCount': self.loop_count
        }


@dataclass
class GlobalVariable:
    """Global variable with value and source"""
    name: str
    value: str = ""
    source: str = ""
    is_sensitive: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value if not self.is_sensitive else '',
            'source': self.source,
            'isSensitive': self.is_sensitive
        }


@dataclass
class RESTPackageData:
    """Complete parsed package data"""
    package_name: str
    package_type: str = "REST_API"
    rest_resources: List[RESTResource] = field(default_factory=list)
    service_signatures: Dict[str, ServiceSignature] = field(default_factory=dict)
    java_services: List[JavaService] = field(default_factory=list)
    flow_services: List[FlowService] = field(default_factory=list)
    global_variables: List[GlobalVariable] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'packageName': self.package_name,
            'packageType': self.package_type,
            'restResources': [r.to_dict() for r in self.rest_resources],
            'serviceSignatures': {k: v.to_dict() for k, v in self.service_signatures.items()},
            'javaServices': [j.to_dict() for j in self.java_services],
            'flowServices': [f.to_dict() for f in self.flow_services],
            'globalVariables': [g.to_dict() for g in self.global_variables],
            'dependencies': self.dependencies,
            'statistics': self.get_statistics()
        }
    
    def get_statistics(self) -> Dict:
        return {
            'restResourceCount': len(self.rest_resources),
            'restOperationCount': sum(len(r.operations) for r in self.rest_resources),
            'javaServiceCount': len(self.java_services),
            'flowServiceCount': len(self.flow_services),
            'globalVariableCount': len(self.global_variables),
            'signatureCount': len(self.service_signatures)
        }


class RESTPackageParser:
    """
    Parses webMethods REST API packages from ZIP files.
    """
    
    SENSITIVE_PATTERNS = ['key', 'secret', 'password', 'token', 'auth', 'credential', 'pwd']
    
    INTERNAL_FIELDS = ['node_type', 'is_public', 'isDocumentType', 'packageName', 'field_type']
    
    TYPE_MAPPING = {
        'string': 'string',
        'java.lang.String': 'string',
        'int': 'number',
        'integer': 'number',
        'java.lang.Integer': 'number',
        'long': 'number',
        'java.lang.Long': 'number',
        'double': 'number',
        'java.lang.Double': 'number',
        'float': 'number',
        'java.lang.Float': 'number',
        'boolean': 'boolean',
        'java.lang.Boolean': 'boolean',
        'date': 'date',
        'java.util.Date': 'datetime',
        'object': 'object',
        'java.lang.Object': 'object',
        'IData': 'object',
        'com.wm.data.IData': 'object',
        'record': 'object',
        'recref': 'object'
    }
    
    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self.temp_dir = None
        self.package_name = ""
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def parse(self) -> RESTPackageData:
        """Parse the complete package"""
        logger.info(f"Parsing REST API package: {self.zip_path}")
        
        # Extract ZIP
        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            zf.extractall(self.temp_dir)
        
        # Find package name from manifest
        self.package_name = self._find_package_name()
        
        # Parse all components
        rest_resources = self._parse_rest_resources()
        signatures = self._parse_all_signatures()
        java_services = self._parse_java_services()
        flow_services = self._parse_flow_services()
        global_variables = self._extract_global_variables(java_services)
        dependencies = self._parse_dependencies()
        
        return RESTPackageData(
            package_name=self.package_name,
            package_type="REST_API",
            rest_resources=rest_resources,
            service_signatures=signatures,
            java_services=java_services,
            flow_services=flow_services,
            global_variables=global_variables,
            dependencies=dependencies
        )
    
    def _find_package_name(self) -> str:
        """Find package name from manifest.v3 or directory structure"""
        # Try manifest.v3
        for root, dirs, files in os.walk(self.temp_dir):
            if 'manifest.v3' in files:
                manifest_path = os.path.join(root, 'manifest.v3')
                try:
                    tree = ET.parse(manifest_path)
                    root_elem = tree.getroot()
                    name = root_elem.get('name') or root_elem.get('packageName')
                    if name:
                        return name
                except:
                    pass
                
                # Try regex
                try:
                    with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        match = re.search(r'name="([^"]+)"', content)
                        if match:
                            return match.group(1)
                except:
                    pass
        
        # Fallback to directory name
        for item in os.listdir(self.temp_dir):
            item_path = os.path.join(self.temp_dir, item)
            if os.path.isdir(item_path) and item not in ['ns', '__MACOSX']:
                return item
        
        return "UnknownPackage"
    
    def _parse_rest_resources(self) -> List[RESTResource]:
        """Parse REST resource definitions from restv2.cnf/restv2.rad files"""
        resources = []
        
        for root, dirs, files in os.walk(self.temp_dir):
            for filename in files:
                if filename in ['restv2.cnf', 'restv2.rad']:
                    filepath = os.path.join(root, filename)
                    try:
                        resource = self._parse_rest_config(filepath)
                        if resource:
                            resources.append(resource)
                    except Exception as e:
                        logger.warning(f"Error parsing {filepath}: {e}")
        
        return resources
    
    def _parse_rest_config(self, filepath: str) -> Optional[RESTResource]:
        """Parse a single REST config file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return None
        
        # Try XML parsing first
        try:
            root = ET.fromstring(content)
            return self._parse_rest_xml(root, filepath)
        except ET.ParseError:
            pass
        
        # Fallback to regex parsing
        return self._parse_rest_regex(content, filepath)
    
    def _parse_rest_xml(self, root: ET.Element, filepath: str) -> Optional[RESTResource]:
        """Parse REST config as XML"""
        operations = []
        base_path = ""
        version = ""
        
        # Look for resource definition
        for elem in root.iter():
            if 'basePath' in elem.attrib:
                base_path = elem.attrib['basePath']
            if 'version' in elem.attrib:
                version = elem.attrib['version']
            
            # Look for operations
            if elem.tag in ['operation', 'method', 'resource']:
                path = elem.get('path', elem.get('uri', ''))
                method = elem.get('method', elem.get('httpMethod', 'GET')).upper()
                service = elem.get('service', elem.get('serviceName', ''))
                
                if path or service:
                    operations.append(RESTOperation(
                        path=path,
                        method=method,
                        service_name=service
                    ))
        
        if operations or base_path:
            resource_name = Path(filepath).parent.name
            return RESTResource(
                name=resource_name,
                base_path=base_path,
                version=version,
                operations=operations
            )
        
        return None
    
    def _parse_rest_regex(self, content: str, filepath: str) -> Optional[RESTResource]:
        """Parse REST config using regex patterns"""
        operations = []
        
        # Common patterns in webMethods REST config
        patterns = [
            r'path\s*[=:]\s*["\']([^"\']+)["\'].*?method\s*[=:]\s*["\']([^"\']+)["\']',
            r'uri\s*[=:]\s*["\']([^"\']+)["\'].*?httpMethod\s*[=:]\s*["\']([^"\']+)["\']',
            r'<operation\s+path="([^"]+)"[^>]*method="([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                path, method = match[0], match[1].upper()
                operations.append(RESTOperation(
                    path=path,
                    method=method,
                    service_name=""
                ))
        
        # Extract base path
        base_match = re.search(r'basePath\s*[=:]\s*["\']([^"\']+)["\']', content)
        base_path = base_match.group(1) if base_match else ""
        
        if operations or base_path:
            resource_name = Path(filepath).parent.name
            return RESTResource(
                name=resource_name,
                base_path=base_path,
                operations=operations
            )
        
        return None
    
    def _parse_all_signatures(self) -> Dict[str, ServiceSignature]:
        """Parse all service signatures from node.ndf files"""
        signatures = {}
        
        for root, dirs, files in os.walk(self.temp_dir):
            if 'node.ndf' in files:
                ndf_path = os.path.join(root, 'node.ndf')
                service_name = Path(root).name
                
                try:
                    sig = self._parse_node_ndf(ndf_path, service_name)
                    if sig:
                        signatures[service_name] = sig
                except Exception as e:
                    logger.warning(f"Error parsing signature {ndf_path}: {e}")
        
        return signatures
    
    def _parse_node_ndf(self, filepath: str, service_name: str) -> Optional[ServiceSignature]:
        """Parse node.ndf file for service signature"""
        try:
            # Read file - may be binary XML
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Try to decode as text
            try:
                text_content = content.decode('utf-8')
            except:
                text_content = content.decode('latin-1', errors='ignore')
            
            # Check if binary XML (starts with specific bytes)
            if content[:4] in [b'\x00\x00\x00\x00', b'\xff\xff\xff\xff'] or not text_content.strip().startswith('<'):
                text_content = self._convert_binary_xml(filepath)
            
            if not text_content:
                return None
            
            # Parse XML
            root = ET.fromstring(text_content)
            
            inputs = []
            outputs = []
            
            # Find sig_in and sig_out
            for elem in root.iter():
                if elem.tag == 'record' or 'record' in elem.tag.lower():
                    record_name = elem.get('name', '')
                    if 'sig_in' in record_name.lower() or record_name == 'svc_in':
                        inputs = self._parse_signature_fields(elem)
                    elif 'sig_out' in record_name.lower() or record_name == 'svc_out':
                        outputs = self._parse_signature_fields(elem)
            
            # Alternative: look for Input/Output markers
            if not inputs and not outputs:
                for elem in root.iter():
                    elem_name = elem.get('name', '')
                    if elem_name in ['Input', 'input', 'sig_in']:
                        inputs = self._parse_signature_fields(elem)
                    elif elem_name in ['Output', 'output', 'sig_out']:
                        outputs = self._parse_signature_fields(elem)
            
            return ServiceSignature(
                service_name=service_name,
                inputs=inputs,
                outputs=outputs
            )
            
        except Exception as e:
            logger.debug(f"Error parsing node.ndf {filepath}: {e}")
            return None
    
    def _convert_binary_xml(self, filepath: str) -> str:
        """Convert binary XML to text XML using available tools"""
        # Try using xmllint or other tools
        try:
            result = subprocess.run(
                ['xmllint', '--format', filepath],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.decode('utf-8', errors='ignore')
        except:
            pass
        
        # Manual binary XML conversion for webMethods format
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Skip binary header and find XML start
            xml_start = data.find(b'<?xml')
            if xml_start == -1:
                xml_start = data.find(b'<Values')
            if xml_start == -1:
                xml_start = data.find(b'<record')
            
            if xml_start >= 0:
                return data[xml_start:].decode('utf-8', errors='ignore')
        except:
            pass
        
        return ""
    
    def _parse_signature_fields(self, elem: ET.Element) -> List[SignatureField]:
        """Parse signature fields from XML element"""
        fields = []
        
        for child in elem:
            field_name = child.get('name', '')
            
            # Skip internal fields
            if field_name in self.INTERNAL_FIELDS or not field_name:
                continue
            
            field_type = child.get('type', child.tag)
            field_type = self.TYPE_MAPPING.get(field_type, 'string')
            
            is_array = child.get('dim', '0') != '0' or child.get('field_dim', '0') != '0'
            
            # Parse children for nested structures
            children = []
            if field_type == 'object' or child.tag in ['record', 'recref']:
                children = self._parse_signature_fields(child)
            
            fields.append(SignatureField(
                name=field_name,
                field_type=field_type,
                is_array=is_array,
                children=children
            ))
        
        return fields
    
    def _parse_java_services(self) -> List[JavaService]:
        """Parse all Java services from java.frag files"""
        services = []
        
        for root, dirs, files in os.walk(self.temp_dir):
            if 'java.frag' in files:
                frag_path = os.path.join(root, 'java.frag')
                service_name = Path(root).name
                
                try:
                    with open(frag_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    # Extract method name
                    method_match = re.search(
                        r'public\s+static\s+(?:final\s+)?void\s+(\w+)\s*\(',
                        code
                    )
                    method_name = method_match.group(1) if method_match else service_name
                    
                    # Extract referenced global variables
                    var_refs = self._extract_variable_references(code)
                    
                    services.append(JavaService(
                        name=service_name,
                        path=frag_path,
                        code=code,
                        method_name=method_name,
                        referenced_variables=var_refs
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing Java service {frag_path}: {e}")
        
        return services
    
    def _extract_variable_references(self, code: str) -> List[str]:
        """Extract global variable references from Java code"""
        patterns = [
            r'GlobalVariables\.getString\s*\(\s*["\']([^"\']+)["\']',
            r'GlobalVariables\.getValue\s*\(\s*["\']([^"\']+)["\']',
            r'getGlobalVariable\s*\(\s*["\']([^"\']+)["\']',
            r'ServerAPI\.getGlobalVariableValue\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        refs = []
        for pattern in patterns:
            matches = re.findall(pattern, code)
            refs.extend(matches)
        
        return list(set(refs))
    
    def _parse_flow_services(self) -> List[FlowService]:
        """Parse all Flow services from flow.xml files"""
        services = []
        
        for root, dirs, files in os.walk(self.temp_dir):
            if 'flow.xml' in files:
                flow_path = os.path.join(root, 'flow.xml')
                service_name = Path(root).name
                
                try:
                    with open(flow_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Parse flow structure
                    invocations = re.findall(r'SERVICE="([^"]+)"', content)
                    invocations += re.findall(r'service="([^"]+)"', content)
                    
                    # Check for HTTP invoke
                    has_http = 'pub.client:http' in content or 'pub.client.http' in content
                    
                    # Count flow steps for complexity
                    map_count = len(re.findall(r'<MAP\s', content, re.IGNORECASE))
                    branch_count = len(re.findall(r'<BRANCH\s', content, re.IGNORECASE))
                    loop_count = len(re.findall(r'<LOOP\s', content, re.IGNORECASE))
                    loop_count += len(re.findall(r'<REPEAT\s', content, re.IGNORECASE))
                    
                    total_steps = map_count + branch_count + loop_count
                    complexity = 'low' if total_steps < 5 else 'high' if total_steps > 15 else 'medium'
                    
                    services.append(FlowService(
                        name=service_name,
                        path=flow_path,
                        invocations=list(set(invocations)),
                        has_http_invoke=has_http,
                        complexity=complexity,
                        map_count=map_count,
                        branch_count=branch_count,
                        loop_count=loop_count
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing flow service {flow_path}: {e}")
        
        return services
    
    def _extract_global_variables(self, java_services: List[JavaService]) -> List[GlobalVariable]:
        """Extract all global variables from Java services"""
        variables = []
        seen = set()
        
        for java_svc in java_services:
            for var_name in java_svc.referenced_variables:
                if var_name not in seen:
                    seen.add(var_name)
                    is_sensitive = any(p in var_name.lower() for p in self.SENSITIVE_PATTERNS)
                    variables.append(GlobalVariable(
                        name=var_name,
                        source=f"java_service:{java_svc.name}",
                        is_sensitive=is_sensitive
                    ))
            
            # Also extract hardcoded values that should be externalized
            hardcoded = self._extract_hardcoded_values(java_svc.code)
            for name, value in hardcoded.items():
                if name not in seen:
                    seen.add(name)
                    is_sensitive = any(p in name.lower() for p in self.SENSITIVE_PATTERNS)
                    variables.append(GlobalVariable(
                        name=name,
                        value=value if not is_sensitive else "",
                        source="hardcoded",
                        is_sensitive=is_sensitive
                    ))
        
        return variables
    
    def _extract_hardcoded_values(self, code: str) -> Dict[str, str]:
        """Extract hardcoded values that should be externalized"""
        values = {}
        
        # URLs
        url_match = re.search(r'["\']?(https?://[^"\'<>\s]+)["\']?', code)
        if url_match:
            values['baseURL'] = url_match.group(1)
        
        # API keys (common patterns)
        key_patterns = [
            (r'api[_-]?key\s*[=:]\s*["\']([^"\']+)["\']', 'apiKey'),
            (r'apiKey\s*[=:]\s*["\']([^"\']+)["\']', 'apiKey'),
            (r'version\s*[=:]\s*["\']([^"\']+)["\']', 'version'),
            (r'timeout\s*[=:]\s*(\d+)', 'timeout'),
        ]
        
        for pattern, name in key_patterns:
            match = re.search(pattern, code, re.IGNORECASE)
            if match and name not in values:
                values[name] = match.group(1)
        
        return values
    
    def _parse_dependencies(self) -> List[str]:
        """Parse package dependencies from manifest.v3"""
        dependencies = []
        
        for root, dirs, files in os.walk(self.temp_dir):
            if 'manifest.v3' in files:
                manifest_path = os.path.join(root, 'manifest.v3')
                try:
                    with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find requires/dependencies
                    dep_matches = re.findall(r'requires\s*=\s*"([^"]+)"', content)
                    for dep in dep_matches:
                        dependencies.extend(dep.split(','))
                    
                    dep_matches = re.findall(r'<requires[^>]*package="([^"]+)"', content)
                    dependencies.extend(dep_matches)
                    
                except Exception as e:
                    logger.warning(f"Error parsing dependencies: {e}")
        
        return list(set(d.strip() for d in dependencies if d.strip()))


def parse_rest_api_package(zip_path: str) -> Dict[str, Any]:
    """
    Factory function to parse REST API package.
    
    Args:
        zip_path: Path to webMethods package ZIP
        
    Returns:
        Parsed package data as dictionary
    """
    with RESTPackageParser(zip_path) as parser:
        package_data = parser.parse()
        return package_data.to_dict()
