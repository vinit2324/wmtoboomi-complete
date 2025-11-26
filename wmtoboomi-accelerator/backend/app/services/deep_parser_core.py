"""
Deep Parser Engine - Part 1
Core structures and node.ndf binary XML parsing

This is the foundation of the migration accelerator.
Handles Software AG's proprietary formats.
"""

import os
import re
import struct
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from lxml import etree
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class ServiceType(str, Enum):
    """Types of webMethods services"""
    FLOW_SERVICE = "FlowService"
    JAVA_SERVICE = "JavaService"
    ADAPTER_SERVICE = "AdapterService"
    MAP_SERVICE = "MapService"
    DOCUMENT_TYPE = "DocumentType"
    SPECIFICATION = "Specification"
    TRIGGER = "Trigger"
    UNKNOWN = "Unknown"


class FlowVerb(str, Enum):
    """The 9 webMethods flow verbs"""
    MAP = "MAP"
    BRANCH = "BRANCH"
    LOOP = "LOOP"
    REPEAT = "REPEAT"
    SEQUENCE = "SEQUENCE"
    INVOKE = "INVOKE"
    EXIT = "EXIT"
    TRY = "TRY"          # Try block
    CATCH = "CATCH"       # Catch block
    FINALLY = "FINALLY"   # Finally block


class AdapterType(str, Enum):
    """Types of adapters"""
    JDBC = "JDBC"
    SAP = "SAP"
    HTTP = "HTTP"
    JMS = "JMS"
    FTP = "FTP"
    SFTP = "SFTP"
    FILE = "File"
    MAIL = "Mail"
    SOAP = "SOAP"
    REST = "REST"
    UNKNOWN = "Unknown"


@dataclass
class PipelineVariable:
    """Represents a variable in the pipeline"""
    name: str
    path: str
    type: str
    is_array: bool = False
    is_required: bool = False
    is_optional: bool = False
    default_value: Optional[str] = None
    source: str = ""  # Which step added this to pipeline
    children: List['PipelineVariable'] = field(default_factory=list)


@dataclass
class ServiceInvocation:
    """Represents a call to another service"""
    service_name: str
    package: str
    full_path: str
    is_wmpublic: bool
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FlowStep:
    """Represents a single step in a flow service"""
    verb: FlowVerb
    name: str
    label: str = ""
    comment: str = ""
    enabled: bool = True
    line_number: int = 0
    
    # For INVOKE
    service_invocation: Optional[ServiceInvocation] = None
    
    # For MAP
    mappings: List[Dict[str, str]] = field(default_factory=list)
    set_values: List[Dict[str, str]] = field(default_factory=list)
    drop_values: List[str] = field(default_factory=list)
    
    # For BRANCH
    switch_variable: str = ""
    branches: List['BranchCase'] = field(default_factory=list)
    evaluate_labels: bool = True
    
    # For LOOP
    loop_variable: str = ""
    loop_array: str = ""
    loop_counter: str = ""
    
    # For SEQUENCE
    exit_on: str = "FAILURE"  # FAILURE, SUCCESS, DONE
    
    # Nested children
    children: List['FlowStep'] = field(default_factory=list)


@dataclass
class BranchCase:
    """A case in a BRANCH step"""
    label: str
    is_default: bool = False
    steps: List[FlowStep] = field(default_factory=list)


@dataclass 
class DocumentField:
    """A field in a Document Type"""
    name: str
    path: str
    type: str  # string, integer, document, documentList, object, etc.
    is_array: bool = False
    is_required: bool = False
    min_occurs: int = 0
    max_occurs: int = 1  # -1 for unbounded
    default_value: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    children: List['DocumentField'] = field(default_factory=list)


@dataclass
class ServiceSignature:
    """Input/output signature of a service"""
    inputs: List[PipelineVariable] = field(default_factory=list)
    outputs: List[PipelineVariable] = field(default_factory=list)
    input_validators: List[Dict] = field(default_factory=list)
    output_validators: List[Dict] = field(default_factory=list)


@dataclass
class ParsedService:
    """Complete parsed representation of a service"""
    name: str
    full_path: str
    type: ServiceType
    package_name: str
    
    # From node.ndf
    signature: ServiceSignature = field(default_factory=ServiceSignature)
    properties: Dict[str, str] = field(default_factory=dict)
    acl: Dict[str, List[str]] = field(default_factory=dict)
    
    # From flow.xml (for Flow Services)
    flow_steps: List[FlowStep] = field(default_factory=list)
    service_invocations: List[ServiceInvocation] = field(default_factory=list)
    
    # Statistics
    verb_counts: Dict[str, int] = field(default_factory=dict)
    wmpublic_calls: List[str] = field(default_factory=list)
    custom_calls: List[str] = field(default_factory=list)
    
    # Adapter info (for Adapter Services)
    adapter_type: Optional[AdapterType] = None
    adapter_config: Dict[str, Any] = field(default_factory=dict)
    
    # Complexity assessment
    complexity_score: int = 0
    complexity_level: str = "low"
    complexity_factors: Dict[str, int] = field(default_factory=dict)
    
    # Raw content
    raw_ndf: Optional[str] = None
    raw_flow_xml: Optional[str] = None


@dataclass
class ParsedDocumentType:
    """Parsed Document Type"""
    name: str
    full_path: str
    package_name: str
    fields: List[DocumentField] = field(default_factory=list)
    is_specification: bool = False
    properties: Dict[str, str] = field(default_factory=dict)
    raw_ndf: Optional[str] = None


# =============================================================================
# NODE.NDF PARSER
# =============================================================================

class NodeNDFParser:
    """
    Parser for webMethods node.ndf files.
    
    node.ndf files use a binary XML format that's specific to Software AG.
    This parser attempts multiple strategies to extract the data:
    1. Try standard XML parsing (sometimes works)
    2. Try binary XML detection and extraction
    3. Fall back to regex-based extraction
    """
    
    # Known byte sequences in node.ndf
    BINARY_XML_MARKERS = [
        b'\x00\x00\x00',    # Common separator
        b'\xff\xff',        # Tag marker
        b'IData',           # IData signature
        b'record',          # Record marker
        b'field',           # Field marker
    ]
    
    # Common encodings to try
    ENCODINGS = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 
                 'latin-1', 'iso-8859-1', 'cp1252']
    
    def __init__(self):
        self.raw_content: bytes = b''
        self.decoded_content: str = ''
        self.parse_method: str = 'unknown'
    
    def parse(self, content: bytes) -> Tuple[Optional[etree._Element], str]:
        """
        Parse node.ndf content and return XML element tree.
        Returns tuple of (parsed_xml, parse_method)
        """
        self.raw_content = content
        
        # Strategy 1: Try direct XML parsing
        xml, method = self._try_xml_parse(content)
        if xml is not None:
            return xml, method
        
        # Strategy 2: Try binary extraction
        xml, method = self._try_binary_extraction(content)
        if xml is not None:
            return xml, method
        
        # Strategy 3: Try decoding and cleaning
        xml, method = self._try_decode_and_clean(content)
        if xml is not None:
            return xml, method
        
        # Strategy 4: Create minimal structure from regex
        xml, method = self._extract_with_regex(content)
        return xml, method
    
    def _try_xml_parse(self, content: bytes) -> Tuple[Optional[etree._Element], str]:
        """Try direct XML parsing"""
        for encoding in self.ENCODINGS:
            try:
                decoded = content.decode(encoding)
                # Find XML-like content
                start = decoded.find('<?xml')
                if start == -1:
                    start = decoded.find('<Values')
                if start == -1:
                    start = decoded.find('<record')
                
                if start >= 0:
                    xml_content = decoded[start:]
                    # Clean null bytes
                    xml_content = xml_content.replace('\x00', '')
                    # Try to parse
                    root = etree.fromstring(xml_content.encode('utf-8'))
                    self.decoded_content = xml_content
                    return root, f'xml_direct_{encoding}'
            except Exception:
                continue
        return None, 'failed'
    
    def _try_binary_extraction(self, content: bytes) -> Tuple[Optional[etree._Element], str]:
        """Try to extract XML from binary format"""
        try:
            # Look for XML declaration or root element
            xml_patterns = [
                rb'<\?xml[^?]*\?>',
                rb'<Values[^>]*>.*</Values>',
                rb'<record[^>]*>.*</record>',
            ]
            
            for pattern in xml_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    for match in matches:
                        try:
                            # Clean the match
                            cleaned = self._clean_binary_content(match)
                            root = etree.fromstring(cleaned)
                            self.decoded_content = cleaned.decode('utf-8', errors='ignore')
                            return root, 'binary_extraction'
                        except Exception:
                            continue
        except Exception as e:
            logger.debug(f"Binary extraction failed: {e}")
        return None, 'failed'
    
    def _try_decode_and_clean(self, content: bytes) -> Tuple[Optional[etree._Element], str]:
        """Try decoding with aggressive cleaning"""
        for encoding in self.ENCODINGS:
            try:
                decoded = content.decode(encoding, errors='ignore')
                
                # Aggressive cleaning
                cleaned = self._clean_text_content(decoded)
                
                if '<' in cleaned and '>' in cleaned:
                    # Try to build valid XML
                    xml_content = self._extract_xml_structure(cleaned)
                    if xml_content:
                        root = etree.fromstring(xml_content.encode('utf-8'))
                        self.decoded_content = xml_content
                        return root, f'cleaned_{encoding}'
            except Exception:
                continue
        return None, 'failed'
    
    def _extract_with_regex(self, content: bytes) -> Tuple[Optional[etree._Element], str]:
        """Extract data using regex patterns"""
        try:
            decoded = content.decode('utf-8', errors='ignore')
            decoded = self._clean_text_content(decoded)
            
            # Extract key-value pairs
            data = {}
            
            # Service name
            name_match = re.search(r'svc_name["\s]*[=:]\s*["\']?([^"\'<>\s]+)', decoded, re.IGNORECASE)
            if name_match:
                data['name'] = name_match.group(1)
            
            # Service type
            type_match = re.search(r'svc_type["\s]*[=:]\s*["\']?([^"\'<>\s]+)', decoded, re.IGNORECASE)
            if type_match:
                data['type'] = type_match.group(1)
            
            # Signature fields
            sig_pattern = r'<field[^>]*name=["\']([^"\']+)["\'][^>]*type=["\']([^"\']+)["\']'
            fields = re.findall(sig_pattern, decoded, re.IGNORECASE)
            data['fields'] = fields
            
            # Build minimal XML
            xml_str = self._build_minimal_xml(data)
            root = etree.fromstring(xml_str.encode('utf-8'))
            self.decoded_content = xml_str
            return root, 'regex_extraction'
            
        except Exception as e:
            logger.warning(f"Regex extraction failed: {e}")
            return None, 'failed'
    
    def _clean_binary_content(self, content: bytes) -> bytes:
        """Clean binary content for XML parsing"""
        # Remove null bytes
        cleaned = content.replace(b'\x00', b'')
        # Remove other control characters (except newlines, tabs)
        cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', cleaned)
        return cleaned
    
    def _clean_text_content(self, content: str) -> str:
        """Clean decoded text content"""
        # Remove null characters
        cleaned = content.replace('\x00', '')
        # Remove other control characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned)
        # Normalize whitespace around tags
        cleaned = re.sub(r'\s+<', '<', cleaned)
        cleaned = re.sub(r'>\s+', '>', cleaned)
        return cleaned
    
    def _extract_xml_structure(self, content: str) -> Optional[str]:
        """Try to extract valid XML structure from content"""
        # Find root element
        root_patterns = [
            (r'<Values[^>]*>.*</Values>', 'Values'),
            (r'<record[^>]*>.*</record>', 'record'),
            (r'<node[^>]*>.*</node>', 'node'),
        ]
        
        for pattern, root_name in root_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                xml_content = match.group(0)
                # Ensure well-formed
                try:
                    etree.fromstring(xml_content.encode('utf-8'))
                    return xml_content
                except Exception:
                    # Try to fix common issues
                    xml_content = self._fix_xml_issues(xml_content)
                    try:
                        etree.fromstring(xml_content.encode('utf-8'))
                        return xml_content
                    except Exception:
                        continue
        return None
    
    def _fix_xml_issues(self, content: str) -> str:
        """Try to fix common XML issues"""
        # Fix unclosed tags
        content = re.sub(r'<([a-zA-Z][a-zA-Z0-9]*)\s+([^>]*)(?<!/)>(?!</\1>)$', 
                        r'<\1 \2/>', content)
        # Fix attribute values without quotes
        content = re.sub(r'(\s[a-zA-Z]+)=([^"\'\s>]+)', r'\1="\2"', content)
        return content
    
    def _build_minimal_xml(self, data: Dict) -> str:
        """Build minimal XML from extracted data"""
        fields_xml = ""
        for name, ftype in data.get('fields', []):
            fields_xml += f'    <field name="{name}" type="{ftype}"/>\n'
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<node>
    <name>{data.get('name', 'unknown')}</name>
    <type>{data.get('type', 'unknown')}</type>
    <signature>
{fields_xml}    </signature>
</node>"""
    
    def parse_service_signature(self, xml: etree._Element) -> ServiceSignature:
        """Extract service signature (inputs/outputs) from parsed XML"""
        signature = ServiceSignature()
        
        # Look for sig_in (inputs) and sig_out (outputs)
        for element in xml.iter():
            tag = element.tag.lower() if element.tag else ''
            
            # Input signature
            if 'sig_in' in tag or 'input' in tag or (tag == 'record' and element.get('name') == 'svc_sig'):
                signature.inputs = self._extract_fields(element, 'input')
            
            # Output signature
            if 'sig_out' in tag or 'output' in tag:
                signature.outputs = self._extract_fields(element, 'output')
        
        return signature
    
    def _extract_fields(self, element: etree._Element, source: str, path_prefix: str = "") -> List[PipelineVariable]:
        """Extract fields from an XML element"""
        fields = []
        
        for child in element:
            tag = child.tag.lower() if child.tag else ''
            name = child.get('name', '')
            
            if not name and child.text:
                name = child.text.strip()
            
            if not name:
                continue
            
            field_type = child.get('type', 'string')
            if not field_type:
                # Infer type from tag
                if 'record' in tag or 'document' in tag:
                    field_type = 'document'
                elif 'array' in tag or 'list' in tag:
                    field_type = 'documentList'
                else:
                    field_type = 'string'
            
            path = f"{path_prefix}/{name}" if path_prefix else name
            
            var = PipelineVariable(
                name=name,
                path=path,
                type=field_type,
                is_array='list' in field_type.lower() or 'array' in field_type.lower(),
                source=source
            )
            
            # Recurse for nested structures
            if len(child) > 0:
                var.children = self._extract_fields(child, source, path)
            
            fields.append(var)
        
        return fields
    
    def parse_document_type(self, xml: etree._Element) -> List[DocumentField]:
        """Extract Document Type field definitions"""
        fields = []
        
        # Look for field definitions
        for element in xml.iter():
            tag = element.tag.lower() if element.tag else ''
            
            if 'field' in tag or 'record' in tag:
                field = self._parse_document_field(element)
                if field:
                    fields.append(field)
        
        return fields
    
    def _parse_document_field(self, element: etree._Element, path_prefix: str = "") -> Optional[DocumentField]:
        """Parse a single document field"""
        name = element.get('name', '')
        if not name:
            # Try to get name from child elements
            for child in element:
                if child.tag and 'name' in child.tag.lower():
                    name = child.text or ''
                    break
        
        if not name:
            return None
        
        field_type = element.get('type', 'string')
        path = f"{path_prefix}/{name}" if path_prefix else name
        
        # Determine array status
        is_array = False
        max_occurs = 1
        if 'list' in field_type.lower() or 'array' in field_type.lower():
            is_array = True
            max_occurs = -1
        if element.get('dim') or element.get('maxOccurs'):
            dim = element.get('dim') or element.get('maxOccurs')
            if dim and dim != '1':
                is_array = True
                max_occurs = -1 if dim in ['*', 'unbounded'] else int(dim)
        
        field = DocumentField(
            name=name,
            path=path,
            type=field_type,
            is_array=is_array,
            is_required=element.get('required', '').lower() == 'true',
            min_occurs=int(element.get('minOccurs', 0)),
            max_occurs=max_occurs,
            default_value=element.get('default')
        )
        
        # Parse nested fields
        for child in element:
            child_field = self._parse_document_field(child, path)
            if child_field:
                field.children.append(child_field)
        
        return field


# =============================================================================
# ADAPTER CONFIGURATION PARSER
# =============================================================================

class AdapterConfigParser:
    """Parser for adapter service configurations"""
    
    def parse_jdbc_adapter(self, xml: etree._Element, raw_content: str) -> Dict[str, Any]:
        """Parse JDBC adapter configuration"""
        config = {
            'type': 'JDBC',
            'connection_alias': '',
            'catalog': '',
            'schema': '',
            'table': '',
            'sql': '',
            'sql_type': '',  # SELECT, INSERT, UPDATE, DELETE, CALL
            'parameters': [],
            'columns': [],
            'joins': [],
            'where_clauses': [],
            'order_by': [],
        }
        
        # Extract from XML
        for elem in xml.iter():
            tag = elem.tag.lower() if elem.tag else ''
            text = elem.text or ''
            
            if 'alias' in tag or 'connection' in tag:
                config['connection_alias'] = text
            elif 'catalog' in tag:
                config['catalog'] = text
            elif 'schema' in tag:
                config['schema'] = text
            elif 'table' in tag:
                config['table'] = text
            elif 'sql' in tag:
                config['sql'] = text
        
        # Extract SQL from raw content if not found
        if not config['sql']:
            sql_patterns = [
                r'SELECT\s+.+?\s+FROM\s+.+?(?:WHERE|ORDER|GROUP|;|$)',
                r'INSERT\s+INTO\s+.+?(?:VALUES|SELECT|;|$)',
                r'UPDATE\s+.+?\s+SET\s+.+?(?:WHERE|;|$)',
                r'DELETE\s+FROM\s+.+?(?:WHERE|;|$)',
                r'CALL\s+.+?\(.*?\)',
            ]
            for pattern in sql_patterns:
                match = re.search(pattern, raw_content, re.IGNORECASE | re.DOTALL)
                if match:
                    config['sql'] = match.group(0).strip()
                    break
        
        # Analyze SQL complexity
        if config['sql']:
            sql_upper = config['sql'].upper()
            if 'SELECT' in sql_upper:
                config['sql_type'] = 'SELECT'
            elif 'INSERT' in sql_upper:
                config['sql_type'] = 'INSERT'
            elif 'UPDATE' in sql_upper:
                config['sql_type'] = 'UPDATE'
            elif 'DELETE' in sql_upper:
                config['sql_type'] = 'DELETE'
            elif 'CALL' in sql_upper or 'EXEC' in sql_upper:
                config['sql_type'] = 'CALL'
            
            # Detect JOINs
            join_matches = re.findall(r'(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+(\w+)', 
                                     config['sql'], re.IGNORECASE)
            config['joins'] = [(j[0] or 'INNER', j[1]) for j in join_matches]
            
            # Detect WHERE complexity
            where_match = re.search(r'WHERE\s+(.+?)(?:ORDER|GROUP|HAVING|;|$)', 
                                   config['sql'], re.IGNORECASE | re.DOTALL)
            if where_match:
                where_clause = where_match.group(1)
                config['where_clauses'] = re.split(r'\s+AND\s+|\s+OR\s+', where_clause, flags=re.IGNORECASE)
        
        return config
    
    def parse_http_adapter(self, xml: etree._Element, raw_content: str) -> Dict[str, Any]:
        """Parse HTTP adapter configuration"""
        config = {
            'type': 'HTTP',
            'url': '',
            'method': 'GET',
            'headers': {},
            'auth_type': '',
            'timeout': 30000,
        }
        
        for elem in xml.iter():
            tag = elem.tag.lower() if elem.tag else ''
            text = elem.text or ''
            
            if 'url' in tag or 'endpoint' in tag:
                config['url'] = text
            elif 'method' in tag:
                config['method'] = text.upper()
            elif 'timeout' in tag:
                try:
                    config['timeout'] = int(text)
                except ValueError:
                    pass
        
        return config
    
    def parse_sap_adapter(self, xml: etree._Element, raw_content: str) -> Dict[str, Any]:
        """Parse SAP adapter configuration"""
        config = {
            'type': 'SAP',
            'connection': '',
            'bapi_name': '',
            'rfc_name': '',
            'idoc_type': '',
            'parameters': [],
        }
        
        for elem in xml.iter():
            tag = elem.tag.lower() if elem.tag else ''
            text = elem.text or ''
            
            if 'connection' in tag or 'destination' in tag:
                config['connection'] = text
            elif 'bapi' in tag:
                config['bapi_name'] = text
            elif 'rfc' in tag:
                config['rfc_name'] = text
            elif 'idoc' in tag:
                config['idoc_type'] = text
        
        return config
    
    def detect_adapter_type(self, content: str) -> AdapterType:
        """Detect adapter type from content"""
        content_lower = content.lower()
        
        if 'jdbc' in content_lower or 'database' in content_lower or 'sql' in content_lower:
            return AdapterType.JDBC
        elif 'sap' in content_lower or 'bapi' in content_lower or 'rfc' in content_lower:
            return AdapterType.SAP
        elif 'http' in content_lower and 'soap' not in content_lower:
            return AdapterType.HTTP
        elif 'soap' in content_lower or 'wsdl' in content_lower:
            return AdapterType.SOAP
        elif 'jms' in content_lower or 'queue' in content_lower or 'topic' in content_lower:
            return AdapterType.JMS
        elif 'sftp' in content_lower:
            return AdapterType.SFTP
        elif 'ftp' in content_lower:
            return AdapterType.FTP
        elif 'mail' in content_lower or 'smtp' in content_lower or 'imap' in content_lower:
            return AdapterType.MAIL
        elif 'file' in content_lower or 'disk' in content_lower:
            return AdapterType.FILE
        elif 'rest' in content_lower:
            return AdapterType.REST
        
        return AdapterType.UNKNOWN
