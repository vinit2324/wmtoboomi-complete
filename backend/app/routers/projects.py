"""Projects API routes - FIXED PARSER"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from datetime import datetime
from pathlib import Path
import zipfile
import re
from app.database import db

router = APIRouter(prefix="/api/projects", tags=["projects"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def parse_webmethods_package(zip_path: str) -> dict:
    """Parse webMethods package and extract all components"""
    
    result = {
        'services': [],
        'documents': [],
        'manifest': {},
        'dependencies': [],
        'statistics': {}
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            
            print(f"[PARSE] Total files in ZIP: {len(file_list)}")
            
            # Find all flow.xml files - these are Flow Services
            flow_xml_files = [f for f in file_list if f.endswith('flow.xml')]
            print(f"[PARSE] Found {len(flow_xml_files)} flow.xml files")
            
            # Find all java.frag files - these are Java Services
            java_frag_files = [f for f in file_list if f.endswith('java.frag')]
            print(f"[PARSE] Found {len(java_frag_files)} java.frag files")
            
            # Find all node.ndf files
            node_ndf_files = [f for f in file_list if f.endswith('node.ndf')]
            print(f"[PARSE] Found {len(node_ndf_files)} node.ndf files")
            
            # Parse Flow Services
            for flow_file in flow_xml_files:
                try:
                    # Get service path (remove /flow.xml)
                    service_path = flow_file[:-9]  # Remove '/flow.xml'
                    
                    # Read and parse flow.xml
                    content = zf.read(flow_file).decode('utf-8', errors='ignore')
                    flow_steps = parse_flow_xml(content)
                    
                    service = {
                        'name': service_path,
                        'type': 'FlowService',
                        'path': service_path,
                        'flowSteps': flow_steps,
                        'stepCount': len(flow_steps)
                    }
                    result['services'].append(service)
                    
                except Exception as e:
                    print(f"[PARSE] Error parsing {flow_file}: {e}")
            
            # Parse Java Services
            for java_file in java_frag_files:
                try:
                    service_path = java_file[:-10]  # Remove '/java.frag'
                    
                    service = {
                        'name': service_path,
                        'type': 'JavaService',
                        'path': service_path,
                        'flowSteps': [],
                        'stepCount': 0
                    }
                    result['services'].append(service)
                    
                except Exception as e:
                    print(f"[PARSE] Error parsing {java_file}: {e}")
            
            # Find Document Types (node.ndf without corresponding flow.xml or java.frag)
            flow_paths = set(f[:-9] for f in flow_xml_files)  # Remove /flow.xml
            java_paths = set(f[:-10] for f in java_frag_files)  # Remove /java.frag
            
            for ndf_file in node_ndf_files:
                ndf_path = ndf_file[:-9]  # Remove '/node.ndf'
                
                # If this path doesn't have a flow.xml or java.frag, it might be a document
                if ndf_path not in flow_paths and ndf_path not in java_paths:
                    # Check if it looks like a document (has 'document' in path or specific patterns)
                    path_lower = ndf_path.lower()
                    if 'document' in path_lower or 'doc' in path_lower or 'record' in path_lower or 'type' in path_lower:
                        try:
                            content = zf.read(ndf_file)
                            fields = parse_document_fields(content)
                            
                            doc = {
                                'name': ndf_path,
                                'type': 'DocumentType',
                                'path': ndf_path,
                                'fields': fields
                            }
                            result['documents'].append(doc)
                        except Exception as e:
                            print(f"[PARSE] Error parsing document {ndf_file}: {e}")
            
            # If no documents found by name, check for EDI schemas or other patterns
            if not result['documents']:
                for ndf_file in node_ndf_files:
                    ndf_path = ndf_file[:-9]
                    if ndf_path not in flow_paths and ndf_path not in java_paths:
                        path_lower = ndf_path.lower()
                        if 'edi' in path_lower or 'schema' in path_lower or 'canonical' in path_lower:
                            try:
                                content = zf.read(ndf_file)
                                fields = parse_document_fields(content)
                                doc = {
                                    'name': ndf_path,
                                    'type': 'DocumentType',
                                    'path': ndf_path,
                                    'fields': fields
                                }
                                result['documents'].append(doc)
                            except:
                                pass
            
            # Look for manifest
            for f in file_list:
                if 'manifest' in f.lower():
                    try:
                        content = zf.read(f).decode('utf-8', errors='ignore')
                        result['manifest'] = {'file': f, 'content': content[:500]}
                    except:
                        pass
            
            print(f"[PARSE] RESULT: {len(result['services'])} services, {len(result['documents'])} documents")
    
    except Exception as e:
        print(f"[PARSE] Critical error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return result


def parse_flow_xml(content: str) -> list:
    """Parse flow.xml and extract flow steps"""
    steps = []
    
    # Parse SEQUENCE
    for match in re.finditer(r'<SEQUENCE[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'SEQUENCE', 'name': match.group(1)})
    
    # Parse INVOKE (service calls)
    for match in re.finditer(r'<INVOKE[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'INVOKE', 'name': match.group(1)})
    
    # Parse MAP
    for match in re.finditer(r'<MAP[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'MAP', 'name': match.group(1)})
    
    # Parse BRANCH
    for match in re.finditer(r'<BRANCH[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'BRANCH', 'name': match.group(1)})
    
    # Parse LOOP
    for match in re.finditer(r'<LOOP[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'LOOP', 'name': match.group(1)})
    
    # Parse REPEAT
    for match in re.finditer(r'<REPEAT[^>]*label="([^"]*)"', content, re.IGNORECASE):
        steps.append({'type': 'REPEAT', 'name': match.group(1)})
    
    # Parse EXIT
    for match in re.finditer(r'<EXIT[^>]*', content, re.IGNORECASE):
        steps.append({'type': 'EXIT', 'name': 'exit'})
    
    # Also count without labels (some may not have labels)
    if not steps:
        # Fallback: count tags
        for tag in ['SEQUENCE', 'INVOKE', 'MAP', 'BRANCH', 'LOOP', 'REPEAT', 'EXIT']:
            count = len(re.findall(f'<{tag}[\\s>]', content, re.IGNORECASE))
            for i in range(count):
                steps.append({'type': tag, 'name': f'{tag.lower()}_{i+1}'})
    
    return steps


def parse_document_fields(content: bytes) -> list:
    """Parse node.ndf to extract document fields"""
    fields = []
    
    try:
        text = content.decode('utf-8', errors='ignore')
        
        # Look for field patterns
        # Pattern: name="fieldName" with various contexts
        names_found = set()
        
        # Look for record fields
        for match in re.finditer(r'<value\s+name="([^"]+)"', text, re.IGNORECASE):
            name = match.group(1)
            if name not in names_found and len(name) > 1:
                names_found.add(name)
                fields.append({'name': name, 'type': 'String'})
        
        # Look for field definitions
        for match in re.finditer(r'field\s+name="([^"]+)"', text, re.IGNORECASE):
            name = match.group(1)
            if name not in names_found and len(name) > 1:
                names_found.add(name)
                fields.append({'name': name, 'type': 'String'})
        
    except Exception as e:
        print(f"[PARSE] Error parsing document fields: {e}")
    
    return fields[:50]  # Limit to 50 fields


@router.post("")
async def upload_package(
    file: UploadFile = File(...),
    customerId: str = Form(...)
):
    """Upload and parse webMethods package"""
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip")
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    print(f"[UPLOAD] Saved {file.filename} ({len(content)} bytes)")
    
    # Parse package
    try:
        parsed_data = parse_webmethods_package(str(file_path))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")
    
    # Calculate stats
    all_services = parsed_data.get('services', [])
    flow_count = sum(1 for s in all_services if s.get('type') == 'FlowService')
    java_count = sum(1 for s in all_services if s.get('type') == 'JavaService')
    adapter_count = sum(1 for s in all_services if s.get('type') == 'AdapterService')
    doc_count = len(parsed_data.get('documents', []))
    
    # Calculate flow verb stats
    verb_stats = {'map': 0, 'branch': 0, 'loop': 0, 'invoke': 0, 'sequence': 0, 'repeat': 0, 'exit': 0}
    for svc in all_services:
        for step in svc.get('flowSteps', []):
            step_type = step.get('type', '').lower()
            if step_type in verb_stats:
                verb_stats[step_type] += 1
    
    print(f"[UPLOAD] Stats: {flow_count} flows, {java_count} java, {doc_count} docs")
    print(f"[UPLOAD] Verbs: {verb_stats}")
    
    # Create project document
    project = {
        "projectId": str(datetime.utcnow().timestamp()),
        "customerId": customerId,
        "packageName": file.filename.replace('.zip', ''),
        "uploadedAt": datetime.utcnow(),
        "status": "parsed",
        "packageInfo": {
            "fileName": file.filename,
            "fileSize": len(content),
            "services": {
                "total": len(all_services),
                "flow": flow_count,
                "java": java_count,
                "adapter": adapter_count,
                "document": doc_count
            },
            "flowVerbStats": verb_stats
        },
        "parsedData": parsed_data
    }
    
    # Save to MongoDB
    await db.projects.insert_one(project)
    print(f"[UPLOAD] Saved to MongoDB: {len(all_services)} services")
    
    # Log activity
    await db.logs.insert_one({
        "timestamp": datetime.utcnow(),
        "level": "info",
        "category": "upload",
        "action": "package_uploaded",
        "message": f"Package {file.filename} uploaded with {len(all_services)} services",
        "metadata": {"projectId": project["projectId"], "services": len(all_services)}
    })
    
    return {
        "success": True,
        "projectId": project["projectId"],
        "packageName": project["packageName"],
        "services": len(all_services),
        "documents": doc_count,
        "flowServices": flow_count,
        "javaServices": java_count
    }


@router.get("")
async def list_projects():
    """List all projects"""
    projects = []
    async for project in db.projects.find().sort("uploadedAt", -1):
        project["_id"] = str(project["_id"])
        projects.append(project)
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["_id"] = str(project["_id"])
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    result = await db.projects.delete_one({"projectId": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}
