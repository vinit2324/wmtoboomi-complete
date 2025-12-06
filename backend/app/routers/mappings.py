"""
Mappings API Router - Endpoints for field mapping operations
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from app.database import db
from app.services.mapping_parser import parse_service_mappings, MappingParser
import zipfile
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mappings", tags=["mappings"])


@router.get("/{project_id}")
async def get_project_mappings(project_id: str):
    """Get all mappings for a project"""
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    all_maps = []
    services = project.get('parsedData', {}).get('services', [])
    
    package_data = project.get('packageFile')
    if not package_data:
        return {"maps": [], "totalMappings": 0}
    
    try:
        zip_bytes = io.BytesIO(package_data)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            for service in services:
                if service.get('type') != 'FlowService':
                    continue
                
                service_name = service.get('name', '')
                flow_path = f"{service_name}/flow.xml"
                
                flow_content = None
                for path_variant in [flow_path, f"ns/{flow_path}", flow_path.replace('/', '\\')]:
                    try:
                        flow_content = zf.read(path_variant).decode('utf-8', errors='ignore')
                        break
                    except KeyError:
                        continue
                
                if flow_content:
                    result = parse_service_mappings(flow_content)
                    for m in result.get('maps', []):
                        m['serviceName'] = service_name
                        all_maps.append(m)
    
    except Exception as e:
        logger.error(f"Error parsing mappings: {e}")
    
    return {
        "maps": all_maps,
        "totalMappings": sum(m.get('mappingCount', 0) for m in all_maps)
    }


@router.get("/{project_id}/service/{service_name:path}")
async def get_service_mappings(project_id: str, service_name: str):
    """Get mappings for a specific service"""
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    package_data = project.get('packageFile')
    if not package_data:
        raise HTTPException(status_code=404, detail="Package file not found")
    
    try:
        zip_bytes = io.BytesIO(package_data)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            flow_path = f"{service_name}/flow.xml"
            
            flow_content = None
            for path_variant in [flow_path, f"ns/{flow_path}", f"NS/{flow_path}"]:
                try:
                    flow_content = zf.read(path_variant).decode('utf-8', errors='ignore')
                    break
                except KeyError:
                    continue
            
            if not flow_content:
                for name in zf.namelist():
                    if service_name.split('/')[-1] in name and name.endswith('flow.xml'):
                        flow_content = zf.read(name).decode('utf-8', errors='ignore')
                        break
            
            if flow_content:
                return parse_service_mappings(flow_content)
    
    except Exception as e:
        logger.error(f"Error getting service mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"maps": [], "totalMappings": 0}


@router.get("/{project_id}/between/{source_doc:path}/{target_doc:path}")
async def get_mapping_between_docs(project_id: str, source_doc: str, target_doc: str):
    """
    Get mapping between two specific documents.
    If no explicit mapping exists, generates auto-mapping suggestions.
    """
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    documents = project.get('parsedData', {}).get('documents', [])
    
    # Find source and target documents
    source = None
    target = None
    
    for doc in documents:
        doc_name = doc.get('name', '')
        simple_name = doc_name.split('/')[-1]
        
        if source_doc in doc_name or source_doc == simple_name:
            source = doc
        if target_doc in doc_name or target_doc == simple_name:
            target = doc
    
    if not source:
        raise HTTPException(status_code=404, detail=f"Source document '{source_doc}' not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target document '{target_doc}' not found")
    
    # First try to find explicit mappings in flow services
    explicit_mappings = await _find_explicit_mappings(project, source, target)
    
    if explicit_mappings:
        return explicit_mappings
    
    # Generate auto-mapping suggestions
    parser = MappingParser()
    auto_mappings = parser.generate_auto_mappings(
        source.get('fields', []),
        target.get('fields', [])
    )
    
    # Get unmapped fields
    mapped_source_fields = {m['sourceFields'][0]['name'] for m in auto_mappings if m.get('sourceFields')}
    mapped_target_fields = {m['targetField'] for m in auto_mappings}
    
    unmapped_source = [f for f in source.get('fields', []) if f.get('name') not in mapped_source_fields]
    unmapped_target = [f for f in target.get('fields', []) if f.get('name') not in mapped_target_fields]
    
    return {
        'name': f"{source.get('name', '').split('/')[-1]} → {target.get('name', '').split('/')[-1]}",
        'sourceProfile': source.get('name'),
        'targetProfile': target.get('name'),
        'sourceFields': source.get('fields', []),
        'targetFields': target.get('fields', []),
        'mappings': auto_mappings,
        'unmappedSourceFields': unmapped_source,
        'unmappedTargetFields': unmapped_target,
        'mappingCount': len(auto_mappings),
        'autoGenerated': True
    }


async def _find_explicit_mappings(project: Dict, source: Dict, target: Dict) -> Optional[Dict]:
    """Search flow services for explicit mappings between source and target"""
    
    package_data = project.get('packageFile')
    if not package_data:
        return None
    
    source_name = source.get('name', '').split('/')[-1].lower()
    target_name = target.get('name', '').split('/')[-1].lower()
    
    try:
        zip_bytes = io.BytesIO(package_data)
        with zipfile.ZipFile(zip_bytes, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('flow.xml'):
                    try:
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        result = parse_service_mappings(content, source, target)
                        
                        for m in result.get('maps', []):
                            map_source = (m.get('sourceProfile') or '').lower()
                            map_target = (m.get('targetProfile') or '').lower()
                            
                            if (source_name in map_source or map_source in source_name) and \
                               (target_name in map_target or map_target in target_name):
                                m['sourceFields'] = source.get('fields', [])
                                m['targetFields'] = target.get('fields', [])
                                return m
                    except:
                        continue
    except:
        pass
    
    return None


@router.post("/{project_id}/generate")
async def generate_boomi_map(project_id: str, request: Dict[str, Any]):
    """Generate Boomi Map XML from mapping definition"""
    
    source_profile = request.get('sourceProfile', '')
    target_profile = request.get('targetProfile', '')
    mappings = request.get('mappings', [])
    
    map_xml = _generate_boomi_map_xml(source_profile, target_profile, mappings)
    
    return {
        "success": True,
        "boomiXml": map_xml,
        "componentType": "Map",
        "mappingCount": len(mappings)
    }


def _generate_boomi_map_xml(source_profile: str, target_profile: str, mappings: List[Dict]) -> str:
    """Generate Boomi-compatible Map XML"""
    
    source_name = source_profile.split('/')[-1] if source_profile else 'Source'
    target_name = target_profile.split('/')[-1] if target_profile else 'Target'
    
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<bns:Map xmlns:bns="http://api.platform.boomi.com/">',
        f'  <bns:Name>{source_name}_to_{target_name}_Map</bns:Name>',
        f'  <bns:Type>map</bns:Type>',
        f'  <bns:SourceProfile>{source_name}</bns:SourceProfile>',
        f'  <bns:TargetProfile>{target_name}</bns:TargetProfile>',
        f'  <bns:Mappings>',
    ]
    
    for mapping in mappings:
        target_field = mapping.get('targetField', '')
        source_fields = mapping.get('sourceFields', [])
        transform_type = mapping.get('transformationType', 'COPY')
        
        if source_fields:
            source_field = source_fields[0].get('name', '')
            
            xml_parts.append(f'    <bns:Mapping>')
            xml_parts.append(f'      <bns:SourceField>{source_field}</bns:SourceField>')
            xml_parts.append(f'      <bns:TargetField>{target_field}</bns:TargetField>')
            xml_parts.append(f'      <bns:TransformationType>{transform_type}</bns:TransformationType>')
            
            if len(source_fields) > 1:
                xml_parts.append(f'      <bns:AdditionalSources>')
                for sf in source_fields[1:]:
                    xml_parts.append(f'        <bns:Field>{sf.get("name", "")}</bns:Field>')
                xml_parts.append(f'      </bns:AdditionalSources>')
            
            xml_parts.append(f'    </bns:Mapping>')
    
    xml_parts.extend([
        f'  </bns:Mappings>',
        f'</bns:Map>'
    ])
    
    return '\n'.join(xml_parts)
