"""
PRODUCTION webMethods Parser - Built for REAL packages
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

class DocumentTypeParser:
    """Parse webMethods Document Types (Records)"""
    
    @staticmethod
    def parse_schema(zf: zipfile.ZipFile, schema_path: str) -> List[Dict]:
        """Parse schema.ndf to extract fields"""
        fields = []
        
        try:
            content = zf.read(schema_path)
            text = content.decode('utf-8', errors='ignore')
            root = ET.fromstring(text)
            
            # Parse children recursively
            fields = DocumentTypeParser._parse_children(root, "")
            
        except Exception as e:
            print(f"   Schema parse error: {e}")
        
        return fields
    
    @staticmethod
    def _parse_children(element: ET.Element, prefix: str) -> List[Dict]:
        """Recursively parse field structure"""
        fields = []
        
        children_elem = element.find(".//record[@name='children']")
        if children_elem is None:
            return fields
        
        for record in children_elem.findall("record"):
            field_name = record.get("name", "unknown")
            full_name = f"{prefix}.{field_name}" if prefix else field_name
            
            # Check if it's a field or nested record
            node_type_elem = record.find("value[@name='node_type']")
            if node_type_elem is not None and node_type_elem.text == "field":
                # It's a field
                field_type_elem = record.find("value[@name='field_type']")
                field_type = field_type_elem.text if field_type_elem is not None else "string"
                
                required_elem = record.find("value[@name='required']")
                required = required_elem.text == "true" if required_elem is not None else False
                
                fields.append({
                    "name": full_name,
                    "type": field_type,
                    "required": required
                })
            elif node_type_elem is not None and node_type_elem.text == "record":
                # It's a nested record - recurse
                nested_fields = DocumentTypeParser._parse_children(record, full_name)
                fields.extend(nested_fields)
        
        return fields


class NodeNDFParser:
    """Parse node.ndf files"""
    
    @staticmethod
    def parse(content: bytes) -> Dict[str, Any]:
        """Parse node.ndf content"""
        result = {
            'type': 'Unknown',
            'name': '',
            'inputs': [],
            'outputs': [],
            'properties': {},
            'isDocumentType': False
        }
        
        try:
            text = content.decode('utf-8', errors='ignore')
            root = ET.fromstring(text)
            
            # Check if document type
            is_doc_elem = root.find("value[@name='isDocumentType']")
            if is_doc_elem is not None and is_doc_elem.text == 'true':
                result['type'] = 'DocumentType'
                result['isDocumentType'] = True
            
            # Get node type
            node_type_elem = root.find("value[@name='node_type']")
            if node_type_elem is not None:
                node_type = node_type_elem.text.lower()
                if 'flow' in node_type and not result['isDocumentType']:
                    result['type'] = 'FlowService'
                elif 'java' in node_type:
                    result['type'] = 'JavaService'
                elif 'adapter' in node_type:
                    result['type'] = 'AdapterService'
                elif 'record' in node_type and not result['isDocumentType']:
                    result['type'] = 'DocumentType'
            
            # Get name
            name_elem = root.find("value[@name='name']")
            if name_elem is not None:
                result['name'] = name_elem.text
            
        except:
            # Fallback to regex
            text = content.decode('utf-8', errors='ignore')
            if 'isDocumentType' in text and 'true' in text:
                result['type'] = 'DocumentType'
                result['isDocumentType'] = True
        
        return result


class FlowXMLParser:
    """Parse flow.xml files"""
    
    FLOW_VERBS = ['INVOKE', 'MAP', 'BRANCH', 'LOOP', 'REPEAT', 'SEQUENCE', 'EXIT']
    
    @staticmethod
    def parse(content: bytes) -> Dict[str, Any]:
        """Parse flow.xml"""
        result = {
            'steps': [],
            'invocations': [],
            'complexity': 'low',
            'verbStats': {
                'map': 0, 'branch': 0, 'loop': 0, 'repeat': 0,
                'sequence': 0, 'invoke': 0, 'exit': 0
            }
        }
        
        try:
            text = content.decode('utf-8', errors='ignore')
            root = ET.fromstring(text)
            
            for elem in root.iter():
                if elem.tag in FlowXMLParser.FLOW_VERBS:
                    step = {'type': elem.tag, 'name': elem.get('NAME', elem.tag.lower())}
                    
                    if elem.tag == 'INVOKE':
                        service = elem.get('SERVICE', '')
                        step['service'] = service
                        result['invocations'].append(service)
                        result['verbStats']['invoke'] += 1
                    elif elem.tag == 'MAP':
                        result['verbStats']['map'] += 1
                    elif elem.tag == 'BRANCH':
                        result['verbStats']['branch'] += 1
                    elif elem.tag == 'LOOP':
                        result['verbStats']['loop'] += 1
                    elif elem.tag == 'REPEAT':
                        result['verbStats']['repeat'] += 1
                    elif elem.tag == 'SEQUENCE':
                        result['verbStats']['sequence'] += 1
                    elif elem.tag == 'EXIT':
                        result['verbStats']['exit'] += 1
                    
                    result['steps'].append(step)
        except:
            pass
        
        total = len(result['steps'])
        result['complexity'] = 'low' if total < 5 else 'medium' if total < 15 else 'high'
        
        return result


class WebMethodsPackageParser:
    """Complete package parser"""
    
    def __init__(self, package_path: str):
        self.package_path = package_path
        
    def parse(self) -> Dict[str, Any]:
        """Parse package"""
        
        result = {
            'packageName': Path(self.package_path).stem,
            'services': [],
            'documents': [],
            'dependencies': [],
            'manifest': {'version': 'unknown', 'dependencies': []},
            'statistics': {
                'totalServices': 0, 'flowServices': 0, 'javaServices': 0,
                'adapterServices': 0, 'documentTypes': 0, 'dependencies': 0,
                'complexity': {'low': 0, 'medium': 0, 'high': 0}
            }
        }
        
        try:
            with zipfile.ZipFile(self.package_path, 'r') as zf:
                file_list = zf.namelist()
                print(f"\n{'='*80}")
                print(f"📦 Package: {len(file_list)} files")
                
                # Find ALL node.ndf (case-insensitive)
                ndf_files = [f for f in file_list if f.lower().endswith('node.ndf')]
                print(f"🔍 Found {len(ndf_files)} node.ndf files")
                
                for ndf_file in ndf_files:
                    service = self._parse_service(zf, ndf_file, file_list)
                    if service:
                        if service['type'] == 'DocumentType':
                            result['documents'].append(service)
                            result['statistics']['documentTypes'] += 1
                            print(f"   📄 DOC: {service['name']} ({len(service.get('fields', []))} fields)")
                        else:
                            result['services'].append(service)
                            result['statistics']['totalServices'] += 1
                            
                            if service['type'] == 'FlowService':
                                result['statistics']['flowServices'] += 1
                                comp = service.get('complexity', 'low')
                                result['statistics']['complexity'][comp] += 1
                                print(f"   âœ… FLOW: {service['name']} ({comp}, {len(service.get('flowSteps', []))} steps)")
                            elif service['type'] == 'JavaService':
                                result['statistics']['javaServices'] += 1
                                print(f"   â˜• JAVA: {service['name']}")
                            elif service['type'] == 'AdapterService':
                                result['statistics']['adapterServices'] += 1
                                print(f"   🔌 ADAPTER: {service['name']}")
                
                print(f"\n✅ TOTAL: {result['statistics']['totalServices']} services, {result['statistics']['documentTypes']} documents")
                print(f"{'='*80}\n")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _parse_service(self, zf: zipfile.ZipFile, ndf_path: str, file_list: List[str]) -> Optional[Dict]:
        """Parse single service/document"""
        
        try:
            service_dir = str(Path(ndf_path).parent)
            service_name = Path(ndf_path).parent.name
            
            ndf_content = zf.read(ndf_path)
            ndf_data = NodeNDFParser.parse(ndf_content)
            
            service = {
                'type': ndf_data['type'],
                'name': ndf_data.get('name') or service_name,
                'path': service_dir,
                'flowSteps': [],
                'serviceInvocations': [],
                'complexity': 'low',
                'fields': []
            }
            
            # If DocumentType, parse schema.ndf
            if service['type'] == 'DocumentType':
                schema_path = f"{service_dir}/schema.ndf"
                if schema_path in file_list:
                    service['fields'] = DocumentTypeParser.parse_schema(zf, schema_path)
            
            # If FlowService, parse flow.xml
            elif service['type'] == 'FlowService':
                flow_path = f"{service_dir}/flow.xml"
                if flow_path in file_list:
                    flow_data = FlowXMLParser.parse(zf.read(flow_path))
                    service['flowSteps'] = flow_data['steps']
                    service['serviceInvocations'] = flow_data['invocations']
                    service['complexity'] = flow_data['complexity']
                    service['verbStats'] = flow_data['verbStats']
            
            return service
            
        except Exception as e:
            print(f"   ❌ Error parsing {ndf_path}: {e}")
            return None


def parse_webmethods_package(package_path: str) -> Dict[str, Any]:
    """Main entry point"""
    parser = WebMethodsPackageParser(package_path)
    return parser.parse()
