"""Conversion API routes - GENERIC enterprise solution, no hardcoding"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.database import db
import httpx
import base64
import uuid
import re
import json

router = APIRouter(prefix="/api/conversions", tags=["conversions"])

BOOMI_CONFIG = {
    "branchId": "QjoyOTQwMQ",
    "branchName": "main",
    "folderId": "Rjo3NTQ1MTg0",
    "folderFullPath": "Jade Global, Inc./MigrationPoC",
    "folderName": "MigrationPoC",
    "createdBy": "vinit.verma@jadeglobal.com"
}

def decrypt_api_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    try:
        from cryptography.fernet import Fernet
        import os
        encryption_key = os.getenv("ENCRYPTION_KEY", "")
        if not encryption_key:
            return encrypted_token
        fernet = Fernet(encryption_key.encode())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        return encrypted_token

def get_short_name(full_path: str) -> str:
    """Extract short name from full path like 'pkg.folder.ServiceName' -> 'ServiceName'"""
    if not full_path:
        return full_path
    return full_path.split('/')[-1].split('.')[-1]

def to_pascal_case(name: str) -> str:
    """Convert name to PascalCase for Boomi naming conventions"""
    # Remove special chars, split on _ or spaces, capitalize each word
    words = re.split(r'[_\s]+', name)
    return ''.join(word.capitalize() for word in words if word)

def extract_base_url(parsed_data: dict) -> str:
    """Extract base URL from global variables or service code - GENERIC"""
    # Try global variables first
    global_vars = parsed_data.get('globalVariables', [])
    for gv in global_vars:
        if isinstance(gv, dict):
            gv_name = gv.get('name', '').lower()
            gv_value = gv.get('value', '')
            if ('url' in gv_name or 'base' in gv_name or 'endpoint' in gv_name) and gv_value.startswith('http'):
                return gv_value
    
    # Try to extract from service code
    services = parsed_data.get('services', [])
    for svc in services:
        code = str(svc.get('code', '')) + str(svc.get('javaCode', ''))
        # Look for URL patterns in code
        url_match = re.search(r'https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9./_-]*)?', code)
        if url_match:
            return url_match.group(0)
    
    # Default placeholder
    return 'https://api.example.com'

def extract_package_name(project: dict) -> str:
    """Extract clean package name for component naming"""
    pkg_name = project.get('packageName', 'Integration')
    # Clean up: remove prefixes like CPRI_DIG_API001_
    clean_name = re.sub(r'^[A-Z]+_[A-Z]+_[A-Z0-9]+_', '', pkg_name)
    return clean_name.replace(' ', '_')

@router.post("/convert")
async def convert_component(data: dict):
    """Main conversion endpoint - routes to appropriate generator"""
    project_id = data.get('projectId')
    service_name = data.get('serviceName')
    component_type = data.get('componentType', 'process')
    display_name = data.get('displayName', service_name)
    is_request = data.get('isRequest', True)
    custom_url = data.get('url')
    return_groovy_only = data.get('returnGroovyOnly', False)
    
    print(f"\n{'='*60}")
    print(f"[CONVERT] Component: {display_name}")
    print(f"[CONVERT] Type: {component_type}, IsRequest: {is_request}")
    print(f"{'='*60}")
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    parsed_data = project.get('parsedData', {})
    
    # Debug: Print available data structure
    print(f"[DEBUG] Parsed data keys: {list(parsed_data.keys())}")
    services = parsed_data.get('services', [])
    print(f"[DEBUG] Total services: {len(services)}")
    for svc in services[:5]:
        svc_name = svc.get('name', 'unknown')
        svc_type = svc.get('type', 'unknown')
        has_input = bool(svc.get('inputSignature') or svc.get('inputs'))
        has_output = bool(svc.get('outputSignature') or svc.get('outputs'))
        print(f"[DEBUG]   - {svc_name} ({svc_type}) input:{has_input} output:{has_output}")
    
    if component_type == 'httpConnection':
        result = generate_http_connection(project, parsed_data, custom_url)
    elif component_type == 'httpOperation':
        result = generate_http_operation(service_name, display_name, project, parsed_data)
    elif component_type == 'jsonProfile':
        result = generate_json_profile(service_name, display_name, is_request, project, parsed_data)
    elif component_type == 'groovyScript':
        result = generate_groovy_script(service_name, display_name, project, parsed_data, return_groovy_only)
    else:
        from app.services.boomi_converter import convert_service
        service = find_service(service_name, parsed_data)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")
        result = convert_service(service)
    
    # Store conversion
    conversion = {
        "conversionId": str(datetime.utcnow().timestamp()),
        "projectId": project_id,
        "serviceName": service_name,
        "displayName": display_name,
        "componentType": result['componentType'],
        "boomiXml": result.get('boomiXml', ''),
        "groovyCode": result.get('groovyCode', ''),
        "automationLevel": result.get('automationLevel', 'SEMI'),
        "convertedAt": datetime.utcnow(),
        "status": "converted"
    }
    await db.conversions.insert_one(conversion)
    return result

def find_service(service_name: str, parsed_data: dict) -> dict:
    """Find a service by name using multiple matching strategies"""
    all_services = parsed_data.get('services', [])
    
    # Strategy 1: Exact match
    for svc in all_services:
        if svc.get('name') == service_name:
            return svc
    
    # Strategy 2: Short name match
    target_short = get_short_name(service_name)
    for svc in all_services:
        svc_short = get_short_name(svc.get('name', ''))
        if svc_short == target_short:
            return svc
    
    # Strategy 3: Partial match
    for svc in all_services:
        svc_name = svc.get('name', '')
        if service_name in svc_name or svc_name in service_name:
            return svc
    
    return None

def find_service_for_profile(display_name: str, service_name: str, parsed_data: dict) -> dict:
    """Find service for profile generation - handles _Request/_Response suffix removal"""
    all_services = parsed_data.get('services', [])
    
    # Remove profile suffixes to get base service name
    base_name = display_name
    for suffix in ['_Request_Profile', '_Response_Profile', '_Request', '_Response', '_Profile']:
        base_name = base_name.replace(suffix, '')
    
    print(f"[PROFILE_MATCH] Looking for service. display_name={display_name}, base_name={base_name}")
    
    # Strategy 1: Match on base_name
    for svc in all_services:
        svc_short = get_short_name(svc.get('name', ''))
        if svc_short.lower() == base_name.lower():
            print(f"[PROFILE_MATCH] Found exact match: {svc.get('name')}")
            return svc
    
    # Strategy 2: Partial match
    for svc in all_services:
        svc_short = get_short_name(svc.get('name', ''))
        if base_name.lower() in svc_short.lower() or svc_short.lower() in base_name.lower():
            print(f"[PROFILE_MATCH] Found partial match: {svc.get('name')}")
            return svc
    
    # Strategy 3: Try service_name directly
    result = find_service(service_name, parsed_data)
    if result:
        print(f"[PROFILE_MATCH] Found via service_name: {result.get('name')}")
        return result
    
    print(f"[PROFILE_MATCH] No match found. Available: {[get_short_name(s.get('name','')) for s in all_services[:10]]}")
    return None

def extract_fields_from_signature(signature: any) -> list:
    """Extract field list from various signature formats"""
    fields = []
    
    if isinstance(signature, dict):
        for key, value in signature.items():
            field_type = 'string'
            if isinstance(value, dict):
                field_type = value.get('type', value.get('javaType', 'string'))
            elif isinstance(value, str):
                field_type = value
            fields.append({'name': key, 'type': normalize_type(field_type)})
    elif isinstance(signature, list):
        for item in signature:
            if isinstance(item, dict):
                fields.append({
                    'name': item.get('name', item.get('field', 'field')),
                    'type': normalize_type(item.get('type', 'string'))
                })
            elif isinstance(item, str):
                fields.append({'name': item, 'type': 'string'})
    
    return fields

def normalize_type(java_type: str) -> str:
    """Convert Java types to simple types for Boomi profiles"""
    if not java_type:
        return 'string'
    java_type_lower = java_type.lower()
    if any(t in java_type_lower for t in ['int', 'long', 'short', 'byte', 'float', 'double', 'number', 'decimal', 'numeric']):
        return 'number'
    if 'bool' in java_type_lower:
        return 'boolean'
    if 'date' in java_type_lower or 'time' in java_type_lower:
        return 'datetime'
    return 'string'

def generate_http_connection(project: dict, parsed_data: dict, custom_url: str = None) -> dict:
    """Generate HTTP Connection XML - GENERIC, uses package name"""
    package_name = extract_package_name(project)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    base_url = custom_url if custom_url else extract_base_url(parsed_data)
    
    conn_name = f"{package_name}_HTTP_Connection"
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?><bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" branchId="{BOOMI_CONFIG['branchId']}" branchName="{BOOMI_CONFIG['branchName']}" createdBy="{BOOMI_CONFIG['createdBy']}" createdDate="{now}" currentVersion="true" deleted="false" folderFullPath="{BOOMI_CONFIG['folderFullPath']}" folderId="{BOOMI_CONFIG['folderId']}" folderName="{BOOMI_CONFIG['folderName']}" modifiedBy="{BOOMI_CONFIG['createdBy']}" modifiedDate="{now}" name="{conn_name}" subType="http" type="connector-settings" version="1">
  <bns:encryptedValues><bns:encryptedValue isSet="false" path="//HttpSettings/AuthSettings/@password"/></bns:encryptedValues>
  <bns:description>HTTP Connection for {package_name} - Base URL: {base_url}</bns:description>
  <bns:object>
    <HttpSettings authenticationType="NONE" url="{base_url}">
      <AuthSettings password="" user=""/>
      <SSLOptions clientauth="false" trustServerCert="false"/>
    </HttpSettings>
  </bns:object>
</bns:Component>'''
    
    return {
        'componentType': 'connector-settings', 
        'boomiXml': xml, 
        'automationLevel': 'AUTO', 
        'notes': [f'Connection: {conn_name}', f'URL: {base_url}']
    }

def generate_http_operation(service_name: str, display_name: str, project: dict, parsed_data: dict) -> dict:
    """Generate HTTP Operation XML - GENERIC, detects method from service name"""
    # Clean up operation name
    op_name = display_name.replace('_Operation', '') if display_name else get_short_name(service_name)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Detect HTTP method from naming conventions
    op_lower = op_name.lower()
    method = 'GET'
    if any(x in op_lower for x in ['create', 'add', 'insert', 'post', 'submit']):
        method = 'POST'
    elif any(x in op_lower for x in ['update', 'put', 'modify', 'edit']):
        method = 'PUT'
    elif any(x in op_lower for x in ['delete', 'remove']):
        method = 'DELETE'
    elif any(x in op_lower for x in ['patch']):
        method = 'PATCH'
    
    # Generate path elements based on naming
    path_elements = '<pathElements><element isVariable="true" key="1" name="resourcePath"/></pathElements>'
    if 'byid' in op_lower or 'getbyid' in op_lower:
        path_elements = '<pathElements><element isVariable="false" key="1" name="entities"/><element isVariable="true" key="2" name="id"/></pathElements>'
    
    boomi_op_name = f"{op_name}_Operation"
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?><bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" branchId="{BOOMI_CONFIG['branchId']}" branchName="{BOOMI_CONFIG['branchName']}" createdBy="{BOOMI_CONFIG['createdBy']}" createdDate="{now}" currentVersion="true" deleted="false" folderFullPath="{BOOMI_CONFIG['folderFullPath']}" folderId="{BOOMI_CONFIG['folderId']}" folderName="{BOOMI_CONFIG['folderName']}" modifiedBy="{BOOMI_CONFIG['createdBy']}" modifiedDate="{now}" name="{boomi_op_name}" subType="http" type="connector-action" version="1">
  <bns:encryptedValues/>
  <bns:description>HTTP {method} Operation for {op_name}</bns:description>
  <bns:object>
    <Operation>
      <Configuration>
        <HttpSendAction dataContentType="application/json" methodType="{method}" requestProfileType="JSON" responseProfileType="JSON">
          <requestHeaders/>{path_elements}
        </HttpSendAction>
      </Configuration>
    </Operation>
  </bns:object>
</bns:Component>'''
    
    return {
        'componentType': 'connector-action', 
        'boomiXml': xml, 
        'automationLevel': 'AUTO', 
        'notes': [f'Operation: {boomi_op_name}', f'Method: {method}']
    }

def generate_json_profile(service_name: str, display_name: str, is_request: bool, project: dict, parsed_data: dict) -> dict:
    """Generate JSON Profile XML - GENERIC, extracts fields from parsed data"""
    profile_name = display_name if display_name else get_short_name(service_name)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"\n[JSON_PROFILE] Generating: {profile_name}, is_request={is_request}")
    
    # Find the corresponding service
    svc = find_service_for_profile(display_name, service_name, parsed_data)
    
    fields = []
    if svc:
        print(f"[JSON_PROFILE] Service found: {svc.get('name')}")
        print(f"[JSON_PROFILE] Service keys: {list(svc.keys())}")
        
        # Extract fields based on request/response
        if is_request:
            # Try multiple sources for input fields
            if svc.get('inputSignature'):
                print(f"[JSON_PROFILE] Using inputSignature: {type(svc.get('inputSignature'))}")
                fields = extract_fields_from_signature(svc.get('inputSignature'))
            elif svc.get('inputs'):
                print(f"[JSON_PROFILE] Using inputs: {type(svc.get('inputs'))}")
                fields = extract_fields_from_signature(svc.get('inputs'))
            elif svc.get('parameters'):
                print(f"[JSON_PROFILE] Using parameters: {type(svc.get('parameters'))}")
                fields = extract_fields_from_signature(svc.get('parameters'))
            elif svc.get('sig_in'):
                print(f"[JSON_PROFILE] Using sig_in: {type(svc.get('sig_in'))}")
                fields = extract_fields_from_signature(svc.get('sig_in'))
        else:
            # Try multiple sources for output fields
            if svc.get('outputSignature'):
                print(f"[JSON_PROFILE] Using outputSignature: {type(svc.get('outputSignature'))}")
                fields = extract_fields_from_signature(svc.get('outputSignature'))
            elif svc.get('outputs'):
                print(f"[JSON_PROFILE] Using outputs: {type(svc.get('outputs'))}")
                fields = extract_fields_from_signature(svc.get('outputs'))
            elif svc.get('sig_out'):
                print(f"[JSON_PROFILE] Using sig_out: {type(svc.get('sig_out'))}")
                fields = extract_fields_from_signature(svc.get('sig_out'))
        
        # Debug: dump full service structure if no fields found
        if not fields:
            print(f"[JSON_PROFILE] No fields extracted! Service dump:")
            for key, val in svc.items():
                val_preview = str(val)[:100] if val else 'None'
                print(f"[JSON_PROFILE]   {key}: {val_preview}")
    else:
        print(f"[JSON_PROFILE] No service found for {profile_name}")
    
    print(f"[JSON_PROFILE] Extracted {len(fields)} fields: {[f['name'] for f in fields[:10]]}")
    
    # Build field entries XML
    key_counter = 3
    field_entries = ""
    for field in fields[:50]:  # Limit to 50 fields
        field_name = re.sub(r'[^\w]', '_', str(field.get('name', f'field{key_counter}')))
        field_type = field.get('type', 'string')
        
        if field_type == 'number':
            data_type = 'number'
            data_format = '<DataFormat><ProfileNumberFormat numberFormat=""/></DataFormat>'
        else:
            data_type = 'character'
            data_format = '<DataFormat><ProfileCharacterFormat/></DataFormat>'
        
        field_entries += f'''
            <JSONObjectEntry dataType="{data_type}" isMappable="true" isNode="true" key="{key_counter}" name="{field_name}">
              {data_format}
            </JSONObjectEntry>'''
        key_counter += 1
    
    # If no fields found, add a placeholder
    if not field_entries:
        print(f"[JSON_PROFILE] WARNING: No fields found, using placeholder")
        field_entries = '''
            <JSONObjectEntry dataType="character" isMappable="true" isNode="true" key="3" name="data">
              <DataFormat><ProfileCharacterFormat/></DataFormat>
            </JSONObjectEntry>'''
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?><bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" branchId="{BOOMI_CONFIG['branchId']}" branchName="{BOOMI_CONFIG['branchName']}" createdBy="{BOOMI_CONFIG['createdBy']}" createdDate="{now}" currentVersion="true" deleted="false" folderFullPath="{BOOMI_CONFIG['folderFullPath']}" folderId="{BOOMI_CONFIG['folderId']}" folderName="{BOOMI_CONFIG['folderName']}" modifiedBy="{BOOMI_CONFIG['createdBy']}" modifiedDate="{now}" name="{profile_name}" type="profile.json" version="1">
  <bns:encryptedValues/>
  <bns:description>JSON Profile: {profile_name} ({len(fields)} fields)</bns:description>
  <bns:object>
    <JSONProfile strict="false">
      <DataElements>
        <JSONRootValue dataType="character" isMappable="true" isNode="true" key="1" name="Root">
          <DataFormat>
            <ProfileCharacterFormat/>
          </DataFormat>
          <JSONObject isMappable="false" isNode="true" key="2" name="Object">{field_entries}
          </JSONObject>
          <Qualifiers>
            <QualifierList/>
          </Qualifiers>
        </JSONRootValue>
      </DataElements>
      <tagLists/>
    </JSONProfile>
  </bns:object>
</bns:Component>'''
    
    return {
        'componentType': 'profile.json', 
        'boomiXml': xml, 
        'automationLevel': 'AUTO', 
        'notes': [f'Profile: {profile_name}', f'Fields: {len(fields)}']
    }

def generate_groovy_script(service_name: str, display_name: str, project: dict, parsed_data: dict, return_groovy_only: bool = False) -> dict:
    """Generate Groovy Script - GENERIC, converts from Java service code"""
    script_name = display_name if display_name else get_short_name(service_name)
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Find the Java service
    svc = find_service(service_name, parsed_data)
    java_code = ""
    input_params = []
    output_params = []
    
    if svc:
        java_code = svc.get('code', svc.get('javaCode', ''))
        # Get input/output parameters for script generation
        if svc.get('inputSignature'):
            input_params = list(svc.get('inputSignature', {}).keys())
        elif svc.get('inputs'):
            inputs = svc.get('inputs', [])
            input_params = [i.get('name', i) if isinstance(i, dict) else i for i in inputs]
        
        if svc.get('outputSignature'):
            output_params = list(svc.get('outputSignature', {}).keys())
        elif svc.get('outputs'):
            outputs = svc.get('outputs', [])
            output_params = [o.get('name', o) if isinstance(o, dict) else o for o in outputs]
    
    # Convert Java to Groovy
    groovy_code = convert_java_to_groovy(java_code, script_name, input_params, output_params)
    
    if return_groovy_only:
        return {
            'componentType': 'groovyScript',
            'groovyCode': groovy_code,
            'boomiXml': '',
            'automationLevel': 'SEMI',
            'notes': [f'Script: {script_name}', 'Copy and paste into Boomi Data Process shape']
        }
    
    groovy_escaped = groovy_code.replace(']]>', ']]]]><![CDATA[>')
    xml = f'''<?xml version="1.0" encoding="UTF-8"?><bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" branchId="{BOOMI_CONFIG['branchId']}" branchName="{BOOMI_CONFIG['branchName']}" createdBy="{BOOMI_CONFIG['createdBy']}" createdDate="{now}" currentVersion="true" deleted="false" folderFullPath="{BOOMI_CONFIG['folderFullPath']}" folderId="{BOOMI_CONFIG['folderId']}" folderName="{BOOMI_CONFIG['folderName']}" modifiedBy="{BOOMI_CONFIG['createdBy']}" modifiedDate="{now}" name="Script_{script_name}" type="process" version="1">
  <bns:encryptedValues/>
  <bns:description>Groovy script converted from {script_name}</bns:description>
  <bns:object>
    <process enableUserLog="true" processLogLevel="WARN_DEBUG" workload="general">
      <shapes>
        <shape image="start" name="shape1" shapetype="start" userlabel="Start" x="48" y="48">
          <configuration/><dragpoints><dragpoint name="out:output" toPoint="in:input" toShape="shape2"/></dragpoints>
        </shape>
        <shape image="dataprocess" name="shape2" shapetype="dataprocess" userlabel="{script_name}" x="192" y="48">
          <configuration><dataprocess><processingStep><CustomScripting scriptLanguage="GROOVY"><![CDATA[{groovy_escaped}]]></CustomScripting></processingStep></dataprocess></configuration>
          <dragpoints><dragpoint name="out:output" toPoint="in:input" toShape="shape3"/></dragpoints>
        </shape>
        <shape image="stop" name="shape3" shapetype="stop" userlabel="Stop" x="336" y="48">
          <configuration/><dragpoints/>
        </shape>
      </shapes>
    </process>
  </bns:object>
</bns:Component>'''
    
    return {
        'componentType': 'process', 
        'groovyCode': groovy_code, 
        'boomiXml': xml, 
        'automationLevel': 'SEMI', 
        'notes': [f'Script: {script_name}']
    }

def convert_java_to_groovy(java_code: str, service_name: str, input_params: list, output_params: list) -> str:
    """Convert Java service code to Groovy - GENERIC conversion"""
    
    # If we have actual Java code, try to convert it
    if java_code and len(java_code.strip()) > 50:
        groovy = java_code
        
        # Basic Java to Groovy transformations
        groovy = re.sub(r'\bpublic\s+static\s+', '', groovy)
        groovy = re.sub(r'\bpublic\s+', '', groovy)
        groovy = re.sub(r'\bprivate\s+', '', groovy)
        groovy = re.sub(r'\bprotected\s+', '', groovy)
        groovy = re.sub(r'\bfinal\s+', '', groovy)
        groovy = re.sub(r'String\[\]\s+', 'def ', groovy)
        groovy = re.sub(r'String\s+', 'def ', groovy)
        groovy = re.sub(r'int\s+', 'def ', groovy)
        groovy = re.sub(r'boolean\s+', 'def ', groovy)
        groovy = re.sub(r'IData\s+', 'def ', groovy)
        groovy = re.sub(r'IDataCursor\s+', 'def ', groovy)
        
        # Add Boomi imports and wrapper
        header = f'''import com.boomi.execution.ExecutionUtil
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

// Groovy Script: {service_name}
// Converted from webMethods Java Service
// Input params: {', '.join(input_params) if input_params else 'none'}
// Output params: {', '.join(output_params) if output_params else 'none'}

def logger = ExecutionUtil.getBaseLogger()
logger.info("{service_name}: Starting...")

'''
        # Add input parameter loading
        if input_params:
            header += "// Load input parameters from Dynamic Process Properties\n"
            for param in input_params[:20]:
                safe_param = re.sub(r'[^\w]', '_', str(param))
                header += f'def {safe_param} = ExecutionUtil.getDynamicProcessProperty("{param}") ?: ""\n'
            header += "\n"
        
        footer = f'''

// Set output parameters
'''
        if output_params:
            for param in output_params[:20]:
                safe_param = re.sub(r'[^\w]', '_', str(param))
                footer += f'// ExecutionUtil.setDynamicProcessProperty("{param}", {safe_param}, false)\n'
        
        footer += f'\nlogger.info("{service_name}: Completed")'
        
        return header + "// Original logic (review and adapt):\n/*\n" + groovy[:2000] + "\n*/\n" + footer
    
    # Generate template if no code available
    input_loading = ""
    if input_params:
        input_loading = "// Load input parameters\n"
        for param in input_params[:20]:
            safe_param = re.sub(r'[^\w]', '_', str(param))
            input_loading += f'def {safe_param} = ExecutionUtil.getDynamicProcessProperty("{param}") ?: ""\n'
    
    output_setting = ""
    if output_params:
        output_setting = "\n// Set output parameters\n"
        for param in output_params[:20]:
            safe_param = re.sub(r'[^\w]', '_', str(param))
            output_setting += f'ExecutionUtil.setDynamicProcessProperty("{param}", {safe_param}, false)\n'
    
    return f'''import com.boomi.execution.ExecutionUtil
import java.net.URLEncoder
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

// Groovy Script: {service_name}
// TODO: Implement business logic from original webMethods Java service

def logger = ExecutionUtil.getBaseLogger()
logger.info("{service_name}: Starting...")

{input_loading}
// TODO: Implement your business logic here
// Example: Build URL, transform data, call service, etc.

{output_setting}
logger.info("{service_name}: Completed")'''

@router.post("/push-to-boomi")
async def push_to_boomi(data: dict):
    """Push component XML to Boomi Platform API"""
    project_id = data.get('projectId')
    component_xml = data.get('componentXml')
    component_name = data.get('componentName')
    
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    customer_id = project.get('customerId')
    customer = await db.customers.find_one({"customerId": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    boomi_settings = customer.get('settings', {}).get('boomi', {})
    account_id = boomi_settings.get('accountId', '')
    username = boomi_settings.get('username', '')
    encrypted_token = boomi_settings.get('apiToken', '')
    api_token = decrypt_api_token(encrypted_token)
    
    if not account_id or not username or not api_token:
        raise HTTPException(status_code=400, detail="Boomi credentials not configured")
    
    url = f"https://api.boomi.com/api/rest/v1/{account_id}/Component"
    auth_string = f"BOOMI_TOKEN.{username}:{api_token}"
    auth_b64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/xml", "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=component_xml, headers=headers, timeout=30.0)
            if response.status_code in [200, 201]:
                return {"success": True, "message": "Pushed to Boomi successfully"}
            elif response.status_code == 401:
                return {"success": False, "message": "Authentication failed"}
            else:
                return {"success": False, "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Push failed: {str(e)}"}

@router.get("/list/{project_id}")
async def list_conversions(project_id: str):
    conversions = await db.conversions.find({"projectId": project_id}).to_list(100)
    for conv in conversions:
        if '_id' in conv:
            del conv['_id']
    return {"conversions": conversions, "total": len(conversions)}

@router.get("/{conversion_id}")
async def get_conversion(conversion_id: str):
    conversion = await db.conversions.find_one({"conversionId": conversion_id})
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if '_id' in conversion:
        del conversion['_id']
    return conversion

# Debug endpoint to see parsed data structure
@router.get("/debug/{project_id}")
async def debug_parsed_data(project_id: str):
    """Debug endpoint to inspect parsed data structure"""
    project = await db.projects.find_one({"projectId": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    parsed_data = project.get('parsedData', {})
    services = parsed_data.get('services', [])
    
    debug_info = {
        "projectId": project_id,
        "packageName": project.get('packageName'),
        "parsedDataKeys": list(parsed_data.keys()),
        "totalServices": len(services),
        "services": []
    }
    
    for svc in services[:20]:
        svc_info = {
            "name": svc.get('name'),
            "type": svc.get('type'),
            "keys": list(svc.keys()),
            "hasInputSignature": bool(svc.get('inputSignature')),
            "hasOutputSignature": bool(svc.get('outputSignature')),
            "hasInputs": bool(svc.get('inputs')),
            "hasOutputs": bool(svc.get('outputs')),
        }
        if svc.get('inputSignature'):
            svc_info['inputSignatureType'] = type(svc.get('inputSignature')).__name__
            svc_info['inputSignaturePreview'] = str(svc.get('inputSignature'))[:200]
        if svc.get('outputSignature'):
            svc_info['outputSignatureType'] = type(svc.get('outputSignature')).__name__
            svc_info['outputSignaturePreview'] = str(svc.get('outputSignature'))[:200]
        debug_info['services'].append(svc_info)
    
    return debug_info
