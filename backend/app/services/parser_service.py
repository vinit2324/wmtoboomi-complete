"""
webMethods package parser service.
Parses manifest.v3, node.ndf (binary XML), and flow.xml files.
"""
import os
import re
import zipfile
import tempfile
import shutil
from typing import Optional, Tuple
from pathlib import Path
import xmltodict
from lxml import etree

from app.models import (
    ParsedData,
    ParsedManifest,
    ParsedService,
    ParsedDocument,
    ParsedEdiSchema,
    FlowVerbStats,
    ServiceInvocation,
    ServiceStats,
    PackageInfo,
    FileTreeNode,
)


class WebMethodsParser:
    """Parser for webMethods packages."""
    
    # The 9 flow verbs in webMethods
    FLOW_VERBS = {
        'MAP': 'map',
        'BRANCH': 'branch',
        'LOOP': 'loop',
        'REPEAT': 'repeat',
        'SEQUENCE': 'sequence',
        'EXIT': 'exit',
    }
    
    # Try/Catch/Finally variations
    TRY_CATCH_PATTERNS = ['TRYCATCH', 'TRY-CATCH', 'TRY_CATCH']
    TRY_FINALLY_PATTERNS = ['TRYFINALLY', 'TRY-FINALLY', 'TRY_FINALLY']
    CATCH_PATTERNS = ['CATCH']
    FINALLY_PATTERNS = ['FINALLY']
    
    def __init__(self, package_path: str):
        """Initialize parser with package path."""
        self.package_path = package_path
        self.extract_dir = None
        self.package_name = ""
        
    def __enter__(self):
        """Extract package on enter."""
        self.extract_dir = tempfile.mkdtemp(prefix="wm_parse_")
        
        with zipfile.ZipFile(self.package_path, 'r') as zf:
            zf.extractall(self.extract_dir)
        
        # Find package name from directory structure
        for item in os.listdir(self.extract_dir):
            item_path = os.path.join(self.extract_dir, item)
            if os.path.isdir(item_path):
                self.package_name = item
                break
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on exit."""
        if self.extract_dir and os.path.exists(self.extract_dir):
            shutil.rmtree(self.extract_dir, ignore_errors=True)
    
    def parse(self) -> Tuple[PackageInfo, ParsedData]:
        """Parse the entire package."""
        # Parse manifest
        manifest = self._parse_manifest()
        
        # Initialize counters
        services = []
        documents = []
        edi_schemas = []
        flow_verb_stats = FlowVerbStats()
        service_stats = ServiceStats()
        wm_public_count = 0
        custom_java_count = 0
        wm_public_services = {}
        
        # Walk through the namespace directory
        ns_dir = os.path.join(self.extract_dir, "ns")
        if not os.path.exists(ns_dir):
            # Try with package name
            ns_dir = os.path.join(self.extract_dir, self.package_name, "ns")
        
        if os.path.exists(ns_dir):
            for root, dirs, files in os.walk(ns_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, ns_dir)
                    
                    if file == "node.ndf":
                        # Parse node.ndf to determine service type
                        service_info = self._parse_node_ndf(file_path, rel_path)
                        if service_info:
                            if service_info.type == "DocumentType":
                                doc = self._extract_document_type(service_info)
                                documents.append(doc)
                                service_stats.document += 1
                            else:
                                services.append(service_info)
                                # Update service type counts
                                if service_info.type == "FlowService":
                                    service_stats.flow += 1
                                elif service_info.type == "JavaService":
                                    service_stats.java += 1
                                elif service_info.type == "AdapterService":
                                    service_stats.adapter += 1
                                elif service_info.type == "MapService":
                                    service_stats.map += 1
                    
                    elif file == "flow.xml":
                        # Parse flow.xml for flow services
                        flow_data = self._parse_flow_xml(file_path)
                        if flow_data:
                            verbs, invocations = flow_data
                            
                            # Update flow verb stats
                            flow_verb_stats.map += verbs.get('map', 0)
                            flow_verb_stats.branch += verbs.get('branch', 0)
                            flow_verb_stats.loop += verbs.get('loop', 0)
                            flow_verb_stats.repeat += verbs.get('repeat', 0)
                            flow_verb_stats.sequence += verbs.get('sequence', 0)
                            flow_verb_stats.tryCatch += verbs.get('tryCatch', 0)
                            flow_verb_stats.tryFinally += verbs.get('tryFinally', 0)
                            flow_verb_stats.catch += verbs.get('catch', 0)
                            flow_verb_stats.finally_ += verbs.get('finally', 0)
                            flow_verb_stats.exit += verbs.get('exit', 0)
                            
                            # Track wMPublic calls
                            for inv in invocations:
                                if inv['package'].startswith(('pub.', 'wm.', 'pub:', 'wm:')):
                                    wm_public_count += inv['count']
                                    svc_name = f"{inv['package']}:{inv['service']}" if ':' not in inv['service'] else inv['service']
                                    wm_public_services[svc_name] = wm_public_services.get(svc_name, 0) + inv['count']
                                else:
                                    custom_java_count += inv['count']
                            
                            # Update the corresponding service with flow data
                            service_name = os.path.dirname(rel_path)
                            for svc in services:
                                if svc.name == service_name or svc.path == service_name:
                                    svc.flowVerbs = FlowVerbStats(**verbs)
                                    svc.serviceInvocations = [
                                        ServiceInvocation(**inv) for inv in invocations
                                    ]
                                    break
        
        # Update service stats total
        service_stats.total = (
            service_stats.flow + 
            service_stats.java + 
            service_stats.adapter + 
            service_stats.map + 
            service_stats.document
        )
        
        # Create package info
        file_size = os.path.getsize(self.package_path)
        file_name = os.path.basename(self.package_path)
        
        package_info = PackageInfo(
            fileName=file_name,
            fileSize=file_size,
            services=service_stats,
            flowVerbStats=flow_verb_stats,
            wMPublicCallCount=wm_public_count,
            customJavaCallCount=custom_java_count
        )
        
        # Create parsed data
        parsed_data = ParsedData(
            manifest=manifest,
            services=services,
            documents=documents,
            ediSchemas=edi_schemas
        )
        
        return package_info, parsed_data
    
    def _parse_manifest(self) -> ParsedManifest:
        """Parse manifest.v3 file."""
        manifest = ParsedManifest()
        
        # Look for manifest.v3
        manifest_path = os.path.join(self.extract_dir, "manifest.v3")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(self.extract_dir, self.package_name, "manifest.v3")
        
        if not os.path.exists(manifest_path):
            manifest.packageName = self.package_name
            return manifest
        
        try:
            with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse as properties-like format
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'name':
                        manifest.packageName = value
                    elif key == 'version':
                        manifest.version = value
                    elif key.startswith('requires.'):
                        manifest.dependencies.append(value)
                    elif key.startswith('startup.'):
                        manifest.startupServices.append(value)
                    elif key.startswith('shutdown.'):
                        manifest.shutdownServices.append(value)
            
            if not manifest.packageName:
                manifest.packageName = self.package_name
                
        except Exception as e:
            manifest.packageName = self.package_name
            
        return manifest
    
    def _parse_node_ndf(self, file_path: str, rel_path: str) -> Optional[ParsedService]:
        """Parse node.ndf file (binary XML format)."""
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Try to parse as XML first
            xml_content = self._convert_binary_xml(content)
            
            if not xml_content:
                return None
            
            # Parse XML
            try:
                root = etree.fromstring(xml_content.encode() if isinstance(xml_content, str) else xml_content)
            except etree.XMLSyntaxError:
                # Try with recovery mode
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(xml_content.encode() if isinstance(xml_content, str) else xml_content, parser)
            
            # Determine service type from node type
            service_type = self._determine_service_type(root, rel_path)
            service_name = os.path.dirname(rel_path).replace('/', ':').replace('\\', ':')
            
            # Extract input/output signatures
            input_sig = self._extract_signature(root, 'input')
            output_sig = self._extract_signature(root, 'output')
            
            # Detect adapters
            adapters = self._detect_adapters(root)
            
            return ParsedService(
                type=service_type,
                name=service_name,
                path=rel_path,
                inputSignature=input_sig,
                outputSignature=output_sig,
                adapters=adapters,
                rawXml=xml_content[:5000] if xml_content else None  # Store first 5KB for reference
            )
            
        except Exception as e:
            # Return basic info even if parsing fails
            service_name = os.path.dirname(rel_path).replace('/', ':').replace('\\', ':')
            return ParsedService(
                type="FlowService",  # Default assumption
                name=service_name,
                path=rel_path
            )
    
    def _convert_binary_xml(self, content: bytes) -> Optional[str]:
        """Convert binary XML (node.ndf) to readable XML string."""
        # Try to decode directly first
        for encoding in ['utf-8', 'utf-16', 'latin-1', 'iso-8859-1']:
            try:
                decoded = content.decode(encoding)
                
                # Check if it looks like XML
                if '<?xml' in decoded or '<Values' in decoded or '<node' in decoded:
                    # Clean up any binary garbage
                    decoded = self._clean_xml_string(decoded)
                    return decoded
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Try to find XML content within binary
        try:
            # Look for XML declaration or root element
            xml_start = -1
            for marker in [b'<?xml', b'<Values', b'<node', b'<record']:
                pos = content.find(marker)
                if pos >= 0 and (xml_start == -1 or pos < xml_start):
                    xml_start = pos
            
            if xml_start >= 0:
                xml_content = content[xml_start:]
                
                # Try to decode
                for encoding in ['utf-8', 'utf-16', 'latin-1']:
                    try:
                        decoded = xml_content.decode(encoding, errors='ignore')
                        decoded = self._clean_xml_string(decoded)
                        return decoded
                    except:
                        continue
        except:
            pass
        
        # Last resort: filter to ASCII printable + common XML chars
        try:
            filtered = bytes(b for b in content if 32 <= b < 127 or b in [9, 10, 13])
            decoded = filtered.decode('ascii', errors='ignore')
            if '<' in decoded and '>' in decoded:
                return self._clean_xml_string(decoded)
        except:
            pass
        
        return None
    
    def _clean_xml_string(self, xml_str: str) -> str:
        """Clean up XML string, removing invalid characters."""
        # Remove null bytes and other control characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_str)
        
        # Find the end of XML content (last > character)
        last_close = cleaned.rfind('>')
        if last_close > 0:
            cleaned = cleaned[:last_close + 1]
        
        return cleaned
    
    def _determine_service_type(self, root: etree._Element, rel_path: str) -> str:
        """Determine service type from node.ndf XML."""
        # Check element attributes and structure
        nsmap = root.nsmap
        
        # Look for type indicators
        node_type = root.get('type', '').lower()
        
        # Check for specific markers in path
        path_lower = rel_path.lower()
        
        if 'flow' in path_lower or node_type == 'flow':
            return "FlowService"
        elif 'adapter' in path_lower or 'jdbc' in path_lower or 'sap' in path_lower:
            return "AdapterService"
        elif 'java' in path_lower or node_type == 'java':
            return "JavaService"
        elif 'map' in path_lower and 'service' in path_lower:
            return "MapService"
        elif 'doctype' in path_lower or 'document' in path_lower:
            return "DocumentType"
        
        # Check XML structure
        xml_str = etree.tostring(root, encoding='unicode')
        xml_lower = xml_str.lower()
        
        if 'svc_type="flow"' in xml_lower or 'flowservice' in xml_lower:
            return "FlowService"
        elif 'svc_type="java"' in xml_lower or 'javaservice' in xml_lower:
            return "JavaService"
        elif 'adapter' in xml_lower:
            return "AdapterService"
        elif 'documenttype' in xml_lower or 'rectype' in xml_lower:
            return "DocumentType"
        
        # Default to FlowService
        return "FlowService"
    
    def _extract_signature(self, root: etree._Element, sig_type: str) -> Optional[dict]:
        """Extract input or output signature from node.ndf."""
        try:
            sig = {}
            
            # Look for sig_in or sig_out elements
            sig_element = root.find(f'.//{sig_type}')
            if sig_element is None:
                sig_element = root.find(f'.//sig_{sig_type[:2]}')
            
            if sig_element is not None:
                # Extract field definitions
                for field in sig_element.iter():
                    if field.get('name'):
                        sig[field.get('name')] = {
                            'type': field.get('type', 'string'),
                            'required': field.get('required', 'false') == 'true'
                        }
            
            return sig if sig else None
        except:
            return None
    
    def _detect_adapters(self, root: etree._Element) -> list[str]:
        """Detect adapter types from node.ndf."""
        adapters = []
        
        xml_str = etree.tostring(root, encoding='unicode').lower()
        
        adapter_types = [
            ('jdbc', 'JDBC'),
            ('sap', 'SAP'),
            ('http', 'HTTP'),
            ('jms', 'JMS'),
            ('ftp', 'FTP'),
            ('sftp', 'SFTP'),
            ('file', 'File'),
            ('email', 'Email'),
            ('soap', 'SOAP'),
            ('rest', 'REST'),
        ]
        
        for pattern, adapter_name in adapter_types:
            if pattern in xml_str:
                adapters.append(adapter_name)
        
        return adapters
    
    def _extract_document_type(self, service: ParsedService) -> ParsedDocument:
        """Extract document type information from a parsed service."""
        return ParsedDocument(
            name=service.name,
            path=service.path,
            fields=[],  # Would need deeper parsing of node.ndf
            nestedStructures=[],
            isArray=False,
            dataType="document"
        )
    
    def _parse_flow_xml(self, file_path: str) -> Optional[Tuple[dict, list]]:
        """Parse flow.xml to extract flow verbs and service invocations."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse XML
            try:
                root = etree.fromstring(content.encode())
            except etree.XMLSyntaxError:
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(content.encode(), parser)
            
            # Count flow verbs
            verbs = {
                'map': 0,
                'branch': 0,
                'loop': 0,
                'repeat': 0,
                'sequence': 0,
                'tryCatch': 0,
                'tryFinally': 0,
                'catch': 0,
                'finally': 0,
                'exit': 0,
            }
            
            # Service invocations
            invocations = []
            invocation_map = {}  # For deduplication
            
            # Parse all elements
            for element in root.iter():
                tag = element.tag.upper() if element.tag else ''
                
                # Check for flow verbs
                if tag == 'MAP' or 'MAP' in tag:
                    verbs['map'] += 1
                elif tag == 'BRANCH' or 'BRANCH' in tag:
                    verbs['branch'] += 1
                elif tag == 'LOOP' or 'LOOP' in tag:
                    verbs['loop'] += 1
                elif tag == 'REPEAT' or 'REPEAT' in tag:
                    verbs['repeat'] += 1
                elif tag == 'SEQUENCE' or 'SEQUENCE' in tag:
                    verbs['sequence'] += 1
                elif any(p in tag for p in self.TRY_CATCH_PATTERNS):
                    verbs['tryCatch'] += 1
                elif any(p in tag for p in self.TRY_FINALLY_PATTERNS):
                    verbs['tryFinally'] += 1
                elif tag == 'CATCH' or any(p in tag for p in self.CATCH_PATTERNS):
                    verbs['catch'] += 1
                elif tag == 'FINALLY' or any(p in tag for p in self.FINALLY_PATTERNS):
                    verbs['finally'] += 1
                elif tag == 'EXIT' or 'EXIT' in tag:
                    verbs['exit'] += 1
                
                # Check for service invocations
                service_attr = element.get('SERVICE') or element.get('service')
                if service_attr:
                    parts = service_attr.split(':')
                    if len(parts) >= 2:
                        pkg = parts[0]
                        svc = ':'.join(parts[1:])
                    else:
                        pkg = 'custom'
                        svc = service_attr
                    
                    key = f"{pkg}:{svc}"
                    if key in invocation_map:
                        invocation_map[key]['count'] += 1
                    else:
                        invocation_map[key] = {
                            'package': pkg,
                            'service': svc,
                            'count': 1
                        }
            
            invocations = list(invocation_map.values())
            
            return verbs, invocations
            
        except Exception as e:
            return None
    
    def get_file_tree(self) -> FileTreeNode:
        """Get file tree for document viewer."""
        root_name = os.path.basename(self.package_path)
        
        def build_tree(path: str, name: str) -> FileTreeNode:
            full_path = path
            rel_path = os.path.relpath(full_path, self.extract_dir)
            
            if os.path.isdir(full_path):
                children = []
                try:
                    for item in sorted(os.listdir(full_path)):
                        child_path = os.path.join(full_path, item)
                        children.append(build_tree(child_path, item))
                except PermissionError:
                    pass
                
                return FileTreeNode(
                    name=name,
                    path=rel_path,
                    type="folder",
                    children=children
                )
            else:
                _, ext = os.path.splitext(name)
                size = os.path.getsize(full_path)
                
                return FileTreeNode(
                    name=name,
                    path=rel_path,
                    type="file",
                    extension=ext.lower(),
                    size=size
                )
        
        return build_tree(self.extract_dir, root_name)
    
    def get_file_content(self, rel_path: str) -> Tuple[str, str]:
        """Get file content for viewer. Returns (content, content_type)."""
        full_path = os.path.join(self.extract_dir, rel_path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return "", "text/plain"
        
        _, ext = os.path.splitext(rel_path)
        ext = ext.lower()
        
        # Determine content type
        content_types = {
            '.xml': 'application/xml',
            '.ndf': 'application/xml',
            '.v3': 'text/plain',
            '.java': 'text/x-java',
            '.frag': 'text/x-java',
            '.properties': 'text/plain',
            '.json': 'application/json',
            '.txt': 'text/plain',
        }
        content_type = content_types.get(ext, 'text/plain')
        
        try:
            # For .ndf files, try to convert binary XML
            if ext == '.ndf':
                with open(full_path, 'rb') as f:
                    content = f.read()
                xml_content = self._convert_binary_xml(content)
                if xml_content:
                    # Pretty print XML
                    try:
                        parser = etree.XMLParser(recover=True, remove_blank_text=True)
                        tree = etree.fromstring(xml_content.encode(), parser)
                        return etree.tostring(tree, pretty_print=True, encoding='unicode'), 'application/xml'
                    except:
                        return xml_content, 'application/xml'
                return "[Binary content - could not parse]", 'text/plain'
            
            # For flow.xml, read and highlight verbs
            if 'flow.xml' in rel_path.lower():
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Pretty print XML
                try:
                    parser = etree.XMLParser(recover=True, remove_blank_text=True)
                    tree = etree.fromstring(content.encode(), parser)
                    return etree.tostring(tree, pretty_print=True, encoding='unicode'), 'application/xml'
                except:
                    return content, 'application/xml'
            
            # Regular text files
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(), content_type
                
        except Exception as e:
            return f"[Error reading file: {str(e)}]", 'text/plain'
