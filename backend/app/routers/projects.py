"""Projects API routes - ENHANCED to handle REAL webMethods packages like Michael Kors
Handles: Flow Service signatures, REST Resources, REST Descriptors, empty rec_fields
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from datetime import datetime
from pathlib import Path
import zipfile
import re
import xml.etree.ElementTree as ET
from app.database import db

router = APIRouter(prefix="/api/projects", tags=["projects"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _map_wm_type(field_type: str, node_type: str = "") -> str:
    """Map webMethods type to standard type"""
    if node_type == "record": 
        return "record"
    ft = (field_type or "").lower()
    if "string" in ft: return "string"
    elif "int" in ft or "long" in ft: return "integer"
    elif "double" in ft or "float" in ft: return "double"
    elif "boolean" in ft: return "boolean"
    elif "date" in ft: return "datetime"
    return "string"


def parse_node_ndf_fields(content: bytes) -> list:
    """Parse rec_fields from node.ndf"""
    fields = []
    try:
        root = ET.fromstring(content.decode('utf-8', errors='ignore'))
        rec_fields = root.find(".//array[@name='rec_fields']")
        if rec_fields is not None:
            for record in rec_fields.findall("record"):
                field = _parse_rec_field(record)
                if field:
                    fields.append(field)
    except Exception as e:
        print(f"[NODE] Error: {e}")
    return fields


def _parse_rec_field(record: ET.Element) -> dict:
    """Parse a single rec_field record recursively"""
    field_name, field_type, field_dim = "", "string", 0
    children = []
    
    for value in record.findall("value"):
        n, t = value.get("name", ""), value.text or ""
        if n == "field_name": field_name = t
        elif n == "field_type": field_type = t
        elif n == "field_dim": field_dim = int(t) if t.isdigit() else 0
    
    # Parse nested rec_fields
    nested_rec_fields = record.find("array[@name='rec_fields']")
    if nested_rec_fields is not None:
        for nested_record in nested_rec_fields.findall("record"):
            child = _parse_rec_field(nested_record)
            if child:
                children.append(child)
    
    if field_name and field_name not in ["node_type", "isDocumentType", "packageName"]:
        return {
            "name": field_name, 
            "type": _map_wm_type(field_type, ""), 
            "required": False, 
            "is_array": field_dim > 0, 
            "children": children
        }
    return None


def parse_service_signature(content: bytes) -> dict:
    """Parse flow service signatures (sig_in, sig_out) from node.ndf
    This is CRITICAL for packages like Michael Kors where fields are in service signatures
    """
    result = {'inputs': [], 'outputs': [], 'type': 'Unknown', 'name': ''}
    
    try:
        text = content.decode('utf-8', errors='ignore')
        root = ET.fromstring(text)
        
        # Get service type
        svc_type_elem = root.find(".//value[@name='svc_type']")
        if svc_type_elem is not None:
            svc_type = svc_type_elem.text or ''
            if svc_type == 'flow':
                result['type'] = 'FlowService'
            elif svc_type == 'java':
                result['type'] = 'JavaService'
        
        # Get node type for REST resources
        node_type_elem = root.find(".//value[@name='node_type']")
        if node_type_elem is not None:
            node_type = node_type_elem.text or ''
            if node_type == 'restResource':
                result['type'] = 'RESTResource'
            elif node_type == 'restDescriptor':
                result['type'] = 'RESTDescriptor'
            elif node_type == 'record':
                result['type'] = 'DocumentType'
        
        # Get name
        name_elem = root.find(".//value[@name='node_nsName']")
        if name_elem is not None and name_elem.text:
            result['name'] = name_elem.text
        
        # Parse svc_sig -> sig_in (inputs)
        sig_in = root.find(".//record[@name='svc_sig']//record[@name='sig_in']")
        if sig_in is not None:
            sig_in_fields = sig_in.find("array[@name='rec_fields']")
            if sig_in_fields is not None:
                for record in sig_in_fields.findall("record"):
                    field = _parse_rec_field(record)
                    if field:
                        result['inputs'].append(field)
        
        # Parse svc_sig -> sig_out (outputs)
        sig_out = root.find(".//record[@name='svc_sig']//record[@name='sig_out']")
        if sig_out is not None:
            sig_out_fields = sig_out.find("array[@name='rec_fields']")
            if sig_out_fields is not None:
                for record in sig_out_fields.findall("record"):
                    field = _parse_rec_field(record)
                    if field:
                        result['outputs'].append(field)
        
        # Parse REST Resource operations
        rest_resource = root.find(".//record[@name='restResource']")
        if rest_resource is not None:
            operations = rest_resource.find("array[@name='operations']")
            if operations is not None:
                result['restOperations'] = []
                for op in operations.findall("record"):
                    url_elem = op.find("value[@name='urlTemplate']")
                    svc_elem = op.find("value[@name='serviceName']")
                    methods_arr = op.find("array[@name='httpMethods']")
                    http_methods = []
                    if methods_arr is not None:
                        for m in methods_arr.findall("value"):
                            if m.text:
                                http_methods.append(m.text)
                    result['restOperations'].append({
                        'url': url_elem.text if url_elem is not None else '',
                        'service': svc_elem.text if svc_elem is not None else '',
                        'methods': http_methods
                    })
        
        # Parse REST Descriptor parameters
        rest_resources = root.find(".//record[@name='restResources']")
        if rest_resources is not None:
            result['restEndpoints'] = []
            for path_record in rest_resources.findall("record"):
                path_name = path_record.get("name", "")
                operations = path_record.find("record[@name='operations']")
                if operations is not None:
                    for method_record in operations.findall("record"):
                        method = method_record.get("name", "")
                        params = method_record.find("record[@name='parameters']")
                        endpoint_params = []
                        if params is not None:
                            for param in params.findall("record"):
                                param_name_elem = param.find("value[@name='name']")
                                param_type_elem = param.find("value[@name='type']")
                                param_source_elem = param.find("value[@name='source']")
                                if param_name_elem is not None:
                                    endpoint_params.append({
                                        'name': param_name_elem.text or '',
                                        'type': param_type_elem.text if param_type_elem is not None else 'STRING',
                                        'source': param_source_elem.text if param_source_elem is not None else 'QUERY'
                                    })
                        result['restEndpoints'].append({
                            'path': path_name,
                            'method': method,
                            'parameters': endpoint_params
                        })
    
    except Exception as e:
        print(f"[SIG] Error: {e}")
    
    return result


def parse_schema_ndf(content: bytes) -> list:
    """Parse schema.ndf to extract document fields"""
    fields = []
    try:
        text = content.decode('utf-8', errors='ignore')
        root = ET.fromstring(text)
        children = root.find(".//record[@name='children']")
        if children is None:
            for record in root.findall("record"):
                name = record.get("name", "")
                if name and name not in ["$node", "children"]:
                    field = _parse_schema_record(record)
                    if field:
                        fields.append(field)
        else:
            for record in children.findall("record"):
                field = _parse_schema_record(record)
                if field:
                    fields.append(field)
    except Exception as e:
        print(f"[SCHEMA] Error: {e}")
    return fields


def _parse_schema_record(record: ET.Element) -> dict:
    """Parse a schema record"""
    field_name = record.get("name", "")
    if not field_name or field_name in ["$node", "children", ""] or field_name.startswith("_"):
        return None
    
    node_type, field_type, is_array, children = "", "string", False, []
    
    for elem in record:
        if elem.tag == "value":
            name = elem.get("name", "")
            text = elem.text or ""
            if name == "node_type": node_type = text
            elif name == "field_type": field_type = text
            elif name == "isArray": is_array = text.lower() == "true"
        elif elem.tag == "record" and elem.get("name") == "children":
            for cr in elem.findall("record"):
                c = _parse_schema_record(cr)
                if c: children.append(c)
    
    return {
        "name": field_name, 
        "type": _map_wm_type(field_type, node_type), 
        "required": False, 
        "is_array": is_array, 
        "children": children
    }


def parse_flow_xml(content: bytes) -> dict:
    """Parse flow.xml for flow steps and service invocations"""
    result = {
        'steps': [],
        'invocations': [],
        'verbStats': {'map': 0, 'branch': 0, 'loop': 0, 'repeat': 0, 'sequence': 0, 'invoke': 0, 'exit': 0}
    }
    
    try:
        text = content.decode('utf-8', errors='ignore')
        
        # Count flow verbs
        for tag in ['MAP', 'BRANCH', 'LOOP', 'REPEAT', 'SEQUENCE', 'EXIT']:
            count = len(re.findall(f'<{tag}[\\s>]', text, re.IGNORECASE))
            result['verbStats'][tag.lower()] = count
            for _ in range(count):
                result['steps'].append({'type': tag, 'name': tag.lower()})
        
        # Find service invocations (INVOKE tags)
        invoke_pattern = r'<INVOKE[^>]*SERVICE="([^"]*)"'
        invokes = re.findall(invoke_pattern, text)
        for svc in invokes:
            result['invocations'].append({'service': svc, 'type': 'invoke'})
            result['verbStats']['invoke'] += 1
            result['steps'].append({'type': 'INVOKE', 'name': svc, 'service': svc})
        
    except Exception as e:
        print(f"[FLOW] Error: {e}")
    
    return result


def parse_webmethods_package(zip_path: str) -> dict:
    """Enhanced parser for REAL webMethods packages
    
    Handles:
    - Flow Services with svc_sig (sig_in/sig_out)
    - REST Resources
    - REST Descriptors  
    - Document Types (both rec_fields and schema.ndf)
    - Java Services
    - Empty rec_fields (creates profile from service signatures)
    """
    result = {
        'services': [], 
        'documents': [], 
        'restResources': [],
        'manifest': {}, 
        'dependencies': [], 
        'statistics': {}
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            
            flow_files = [f for f in file_list if f.endswith('flow.xml') and not f.endswith('.bak')]
            java_files = [f for f in file_list if f.endswith('java.frag')]
            node_files = [f for f in file_list if f.endswith('node.ndf')]
            schema_files = [f for f in file_list if f.endswith('schema.ndf')]
            
            print(f"[PARSE] Files: {len(file_list)}, flow: {len(flow_files)}, java: {len(java_files)}, node: {len(node_files)}, schema: {len(schema_files)}")
            
            # Build schema map for quick lookup
            schema_map = {sf.rsplit('/', 1)[0] if '/' in sf else '': sf for sf in schema_files}
            
            # Track what we've processed
            processed_paths = set()
            flow_paths = set(f.replace('/flow.xml', '') for f in flow_files)
            java_paths = set(f.replace('/java.frag', '') for f in java_files)
            
            # ============================================
            # STEP 1: Parse Flow Services (with signatures)
            # ============================================
            for ff in flow_files:
                path = ff.replace('/flow.xml', '')
                processed_paths.add(path)
                
                # Parse flow.xml for steps
                flow_content = zf.read(ff)
                flow_data = parse_flow_xml(flow_content)
                
                # Parse node.ndf for service signature
                ndf_path = path + '/node.ndf'
                inputs, outputs = [], []
                if ndf_path in file_list:
                    ndf_content = zf.read(ndf_path)
                    sig_data = parse_service_signature(ndf_content)
                    inputs = sig_data.get('inputs', [])
                    outputs = sig_data.get('outputs', [])
                
                service = {
                    'name': path,
                    'type': 'FlowService',
                    'path': path,
                    'flowSteps': flow_data['steps'],
                    'stepCount': len(flow_data['steps']),
                    'verbStats': flow_data['verbStats'],
                    'invocations': flow_data['invocations'],
                    'inputs': inputs,
                    'outputs': outputs,
                    'inputCount': len(inputs),
                    'outputCount': len(outputs)
                }
                result['services'].append(service)
                print(f"[PARSE] FlowService: {path}, steps: {len(flow_data['steps'])}, inputs: {len(inputs)}, outputs: {len(outputs)}")
                
                # Create input/output profiles from service signature
                if inputs:
                    result['documents'].append({
                        'name': f"{path}/InputSignature",
                        'type': 'ServiceInput',
                        'path': path,
                        'fields': inputs,
                        'fieldCount': len(inputs),
                        'source': 'flow_service_signature'
                    })
                if outputs:
                    result['documents'].append({
                        'name': f"{path}/OutputSignature",
                        'type': 'ServiceOutput',
                        'path': path,
                        'fields': outputs,
                        'fieldCount': len(outputs),
                        'source': 'flow_service_signature'
                    })
            
            # ============================================
            # STEP 2: Parse Java Services
            # ============================================
            for jf in java_files:
                path = jf.replace('/java.frag', '')
                processed_paths.add(path)
                
                # Parse node.ndf for service signature
                ndf_path = path + '/node.ndf'
                inputs, outputs = [], []
                if ndf_path in file_list:
                    ndf_content = zf.read(ndf_path)
                    sig_data = parse_service_signature(ndf_content)
                    inputs = sig_data.get('inputs', [])
                    outputs = sig_data.get('outputs', [])
                
                result['services'].append({
                    'name': path, 
                    'type': 'JavaService', 
                    'path': path, 
                    'flowSteps': [], 
                    'stepCount': 0,
                    'inputs': inputs,
                    'outputs': outputs
                })
            
            # ============================================
            # STEP 3: Parse remaining node.ndf files
            # ============================================
            for nf in node_files:
                nf_path = nf.replace('/node.ndf', '')
                nf_folder = nf.rsplit('/', 1)[0] if '/' in nf else ''
                
                # Skip if already processed as flow/java
                if nf_path in processed_paths:
                    continue
                
                content = zf.read(nf)
                text = content.decode('utf-8', errors='ignore')
                sig_data = parse_service_signature(content)
                detected_type = sig_data.get('type', 'Unknown')
                
                # ---- REST Resource ----
                if detected_type == 'RESTResource':
                    rest_ops = sig_data.get('restOperations', [])
                    result['restResources'].append({
                        'name': nf_path,
                        'type': 'RESTResource',
                        'path': nf_path,
                        'operations': rest_ops
                    })
                    print(f"[PARSE] RESTResource: {nf_path}, operations: {len(rest_ops)}")
                    processed_paths.add(nf_path)
                    continue
                
                # ---- REST Descriptor ----
                if detected_type == 'RESTDescriptor':
                    endpoints = sig_data.get('restEndpoints', [])
                    # Extract all parameters as fields for profile creation
                    all_params = []
                    for ep in endpoints:
                        for param in ep.get('parameters', []):
                            if not any(p['name'] == param['name'] for p in all_params):
                                all_params.append({
                                    'name': param['name'],
                                    'type': 'string',
                                    'required': False,
                                    'is_array': False,
                                    'children': [],
                                    'source': param.get('source', 'QUERY')
                                })
                    
                    result['restResources'].append({
                        'name': nf_path,
                        'type': 'RESTDescriptor',
                        'path': nf_path,
                        'endpoints': endpoints,
                        'parameters': all_params
                    })
                    
                    # Also create a document/profile from the parameters
                    if all_params:
                        result['documents'].append({
                            'name': f"{nf_path}/APIParameters",
                            'type': 'RESTParameters',
                            'path': nf_path,
                            'fields': all_params,
                            'fieldCount': len(all_params),
                            'source': 'rest_descriptor'
                        })
                    
                    print(f"[PARSE] RESTDescriptor: {nf_path}, endpoints: {len(endpoints)}, params: {len(all_params)}")
                    processed_paths.add(nf_path)
                    continue
                
                # ---- Document Type ----
                is_doc = (
                    detected_type == 'DocumentType' or
                    any(x in nf_path.lower() for x in ['document', 'doc', 'record', 'canonical', 'type', 'doctype']) or 
                    ('isDocumentType' in text and 'true' in text.lower()) or
                    'field_type' in text and 'record' in text
                )
                
                if is_doc:
                    fields = []
                    
                    # Try schema.ndf first
                    if nf_folder in schema_map:
                        fields = parse_schema_ndf(zf.read(schema_map[nf_folder]))
                    
                    # Try schema.ndf in same folder
                    if not fields:
                        ps = nf.replace('node.ndf', 'schema.ndf')
                        if ps in file_list:
                            fields = parse_schema_ndf(zf.read(ps))
                    
                    # Try rec_fields in node.ndf
                    if not fields:
                        fields = parse_node_ndf_fields(content)
                    
                    # If still no fields, check if there's an associated service with signature
                    if not fields:
                        assoc_match = re.search(r'assocdoctypename["\s>]*[^<]*<value[^>]*>([^<]+)', text)
                        if assoc_match:
                            assoc_doc = assoc_match.group(1)
                            print(f"[PARSE] Document {nf_path} references: {assoc_doc}")
                    
                    result['documents'].append({
                        'name': nf_path, 
                        'type': 'DocumentType', 
                        'path': nf_path, 
                        'fields': fields, 
                        'fieldCount': len(fields)
                    })
                    print(f"[PARSE] Document: {nf_path}, fields: {len(fields)}")
                    processed_paths.add(nf_path)
            
            # ============================================
            # STEP 4: Parse manifest.v3
            # ============================================
            manifest_files = [f for f in file_list if f.endswith('manifest.v3')]
            if manifest_files:
                try:
                    manifest_content = zf.read(manifest_files[0]).decode('utf-8', errors='ignore')
                    for line in manifest_content.split('\n'):
                        if '=' in line:
                            key, val = line.split('=', 1)
                            result['manifest'][key.strip()] = val.strip()
                except:
                    pass
            
            # ============================================
            # STEP 5: Calculate statistics
            # ============================================
            result['statistics'] = {
                'totalFiles': len(file_list),
                'flowServices': len([s for s in result['services'] if s['type'] == 'FlowService']),
                'javaServices': len([s for s in result['services'] if s['type'] == 'JavaService']),
                'documentTypes': len([d for d in result['documents'] if d['type'] == 'DocumentType']),
                'serviceInputs': len([d for d in result['documents'] if d['type'] == 'ServiceInput']),
                'serviceOutputs': len([d for d in result['documents'] if d['type'] == 'ServiceOutput']),
                'restResources': len(result['restResources']),
                'totalFields': sum(len(d.get('fields', [])) for d in result['documents'])
            }
            
            print(f"[PARSE] Complete: {result['statistics']}")
    
    except Exception as e:
        print(f"[PARSE] Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return result


@router.post("")
async def upload_package(file: UploadFile = File(...), customerId: str = Form(...)):
    """Upload and parse webMethods package"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip")
    
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    parsed_data = parse_webmethods_package(str(file_path))
    
    all_svcs = parsed_data.get('services', [])
    all_docs = parsed_data.get('documents', [])
    rest_resources = parsed_data.get('restResources', [])
    
    flow_count = sum(1 for s in all_svcs if s.get('type') == 'FlowService')
    java_count = sum(1 for s in all_svcs if s.get('type') == 'JavaService')
    adapter_count = sum(1 for s in all_svcs if s.get('type') == 'AdapterService')
    doc_count = len([d for d in all_docs if d.get('type') == 'DocumentType'])
    total_fields = sum(len(d.get('fields', [])) for d in all_docs)
    
    # Build packageInfo structure
    package_info = {
        "fileName": file.filename,
        "fileSize": len(content),
        "services": {
            "total": len(all_svcs),
            "flow": flow_count,
            "java": java_count,
            "adapter": adapter_count,
            "map": 0,
            "document": doc_count,
            "rest": len(rest_resources)
        },
        "flowVerbStats": {"map": 0, "branch": 0, "loop": 0, "repeat": 0, "sequence": 0, "tryCatch": 0, "exit": 0, "invoke": 0},
        "wMPublicCallCount": 0,
        "customJavaCallCount": java_count
    }
    
    # Count flow verbs
    for svc in all_svcs:
        verb_stats = svc.get('verbStats', {})
        for verb, count in verb_stats.items():
            if verb in package_info["flowVerbStats"]:
                package_info["flowVerbStats"][verb] += count
        
        # Also count from flowSteps for backward compatibility
        for step in svc.get('flowSteps', []):
            st = step.get('type', '').lower()
            if st in package_info["flowVerbStats"]:
                package_info["flowVerbStats"][st] += 1
    
    project = {
        "projectId": str(datetime.utcnow().timestamp()),
        "customerId": customerId,
        "packageName": file.filename.replace('.zip', ''),
        "fileName": file.filename,
        "fileSize": len(content),
        "uploadedAt": datetime.utcnow(),
        "status": "parsed",
        "parsedData": parsed_data,
        "packageInfo": package_info,
        "statistics": {
            "totalServices": len(all_svcs),
            "flowServices": flow_count,
            "javaServices": java_count,
            "adapterServices": adapter_count,
            "documentTypes": doc_count,
            "restResources": len(rest_resources),
            "totalFields": total_fields
        }
    }
    
    await db.projects.insert_one(project)
    
    print(f"[UPLOAD] Saved: {len(all_svcs)} services, {len(all_docs)} documents, {len(rest_resources)} REST resources, {total_fields} total fields")
    
    return {
        "projectId": project["projectId"],
        "customerId": customerId,
        "packageName": project["packageName"],
        "status": "parsed",
        "packageInfo": package_info,
        "statistics": project["statistics"],
        "parsedData": parsed_data
    }


@router.get("")
async def list_projects():
    """List all projects"""
    projects = []
    async for p in db.projects.find().sort("uploadedAt", -1):
        projects.append({
            "projectId": p.get("projectId"),
            "customerId": p.get("customerId"),
            "packageName": p.get("packageName"),
            "uploadedAt": p.get("uploadedAt"),
            "status": p.get("status"),
            "packageInfo": p.get("packageInfo", {}),
            "statistics": p.get("statistics", {})
        })
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get single project"""
    p = await db.projects.find_one({"projectId": project_id})
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "projectId": p.get("projectId"),
        "customerId": p.get("customerId"),
        "packageName": p.get("packageName"),
        "uploadedAt": p.get("uploadedAt"),
        "status": p.get("status"),
        "packageInfo": p.get("packageInfo", {}),
        "statistics": p.get("statistics", {}),
        "parsedData": p.get("parsedData", {})
    }


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete project"""
    result = await db.projects.delete_one({"projectId": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}
