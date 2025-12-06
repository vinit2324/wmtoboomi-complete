"""
Boomi JSON Profile Generator
============================
Generates Boomi JSON Profile XML from webMethods service signatures.

Uses EXACT Boomi Platform API format for profile.json components.

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoomiDeploymentConfig:
    """Boomi deployment configuration"""
    folder_id: str = "Rjo3NTQ1MTg0"
    folder_name: str = "MigrationPoC"
    folder_full_path: str = "Jade Global, Inc./MigrationPoC"
    branch_id: str = "QjoyOTQwMQ"
    branch_name: str = "main"
    created_by: str = "vinit.verma@jadeglobal.com"
    modified_by: str = "vinit.verma@jadeglobal.com"
    
    def get_timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class BoomiJSONProfileGenerator:
    """
    Generates Boomi JSON Profile XML from field definitions.
    """
    
    BOOMI_NS = "http://api.platform.boomi.com/"
    
    # webMethods to Boomi type mapping
    TYPE_MAPPING = {
        'string': 'CHARACTER',
        'character': 'CHARACTER',
        'int': 'NUMBER',
        'integer': 'NUMBER',
        'number': 'NUMBER',
        'long': 'NUMBER',
        'double': 'NUMBER',
        'float': 'NUMBER',
        'boolean': 'CHARACTER',
        'date': 'DATE',
        'datetime': 'DATETIME',
        'object': 'OBJECT',
        'array': 'ARRAY'
    }
    
    def __init__(self, config: Optional[BoomiDeploymentConfig] = None):
        self.config = config or BoomiDeploymentConfig()
        self.key_counter = 1
    
    def generate(
        self,
        name: str,
        fields: List[Dict],
        description: str = ""
    ) -> str:
        """
        Generate complete JSON Profile XML.
        
        Args:
            name: Component name
            fields: List of field definitions from webMethods signature
            description: Component description
            
        Returns:
            Complete Boomi JSON Profile XML
        """
        self.key_counter = 1
        timestamp = self.config.get_timestamp()
        
        # Generate field elements
        data_elements = self._generate_data_elements(fields)
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="{self.BOOMI_NS}"
    branchId="{self.config.branch_id}"
    branchName="{self.config.branch_name}"
    createdBy="{self.config.created_by}"
    createdDate="{timestamp}"
    modifiedBy="{self.config.modified_by}"
    modifiedDate="{timestamp}"
    folderFullPath="{self.config.folder_full_path}"
    folderId="{self.config.folder_id}"
    folderName="{self.config.folder_name}"
    name="{self._escape_xml(name)}"
    type="profile.json">
  <bns:encryptedValues/>
  <bns:description>{self._escape_xml(description)}</bns:description>
  <bns:object>
    <JSONProfile strict="false">
      <DataElements>
{data_elements}
      </DataElements>
      <DataFormat>
        <ProfileCharacterFormat/>
      </DataFormat>
    </JSONProfile>
  </bns:object>
</bns:Component>'''
        
        return xml
    
    def _generate_data_elements(self, fields: List[Dict]) -> str:
        """Generate DataElements section with nested structure"""
        if not fields:
            return self._generate_empty_object()
        
        root_key = self._next_key()
        
        # Build JSON object entries
        entries = self._generate_json_entries(fields, indent=10)
        
        return f'''        <JSONRootValue key="{root_key}">
          <JSONObject key="{self._next_key()}">
{entries}
          </JSONObject>
        </JSONRootValue>'''
    
    def _generate_json_entries(self, fields: List[Dict], indent: int = 10) -> str:
        """Generate JSONObjectEntry elements for fields"""
        entries = []
        pad = ' ' * indent
        
        for field in fields:
            field_name = field.get('name', '')
            field_type = field.get('type', 'string').lower()
            is_array = field.get('isArray', False)
            children = field.get('children', [])
            
            boomi_type = self.TYPE_MAPPING.get(field_type, 'CHARACTER')
            
            if is_array:
                # Array field
                entry = self._generate_array_entry(field_name, field_type, children, indent)
            elif children or field_type == 'object':
                # Nested object
                entry = self._generate_object_entry(field_name, children, indent)
            else:
                # Simple field
                entry = self._generate_simple_entry(field_name, boomi_type, indent)
            
            entries.append(entry)
        
        return '\n'.join(entries)
    
    def _generate_simple_entry(self, name: str, boomi_type: str, indent: int) -> str:
        """Generate simple JSONObjectEntry"""
        pad = ' ' * indent
        entry_key = self._next_key()
        value_key = self._next_key()
        
        return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONDataElement dataType="{boomi_type}" key="{value_key}"/>
{pad}</JSONObjectEntry>'''
    
    def _generate_object_entry(self, name: str, children: List[Dict], indent: int) -> str:
        """Generate JSONObjectEntry with nested JSONObject"""
        pad = ' ' * indent
        entry_key = self._next_key()
        obj_key = self._next_key()
        
        if children:
            nested_entries = self._generate_json_entries(children, indent + 4)
            return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONObject key="{obj_key}">
{nested_entries}
{pad}  </JSONObject>
{pad}</JSONObjectEntry>'''
        else:
            return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONObject key="{obj_key}"/>
{pad}</JSONObjectEntry>'''
    
    def _generate_array_entry(self, name: str, item_type: str, children: List[Dict], indent: int) -> str:
        """Generate JSONObjectEntry with JSONArray"""
        pad = ' ' * indent
        entry_key = self._next_key()
        array_key = self._next_key()
        
        boomi_type = self.TYPE_MAPPING.get(item_type, 'CHARACTER')
        
        if children or item_type == 'object':
            # Array of objects
            obj_key = self._next_key()
            if children:
                nested_entries = self._generate_json_entries(children, indent + 6)
                return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONArray key="{array_key}">
{pad}    <JSONObject key="{obj_key}">
{nested_entries}
{pad}    </JSONObject>
{pad}  </JSONArray>
{pad}</JSONObjectEntry>'''
            else:
                return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONArray key="{array_key}">
{pad}    <JSONObject key="{obj_key}"/>
{pad}  </JSONArray>
{pad}</JSONObjectEntry>'''
        else:
            # Array of simple types
            value_key = self._next_key()
            return f'''{pad}<JSONObjectEntry key="{entry_key}" name="{self._escape_xml(name)}">
{pad}  <JSONArray key="{array_key}">
{pad}    <JSONDataElement dataType="{boomi_type}" key="{value_key}"/>
{pad}  </JSONArray>
{pad}</JSONObjectEntry>'''
    
    def _generate_empty_object(self) -> str:
        """Generate empty JSON object structure"""
        root_key = self._next_key()
        obj_key = self._next_key()
        return f'''        <JSONRootValue key="{root_key}">
          <JSONObject key="{obj_key}"/>
        </JSONRootValue>'''
    
    def _next_key(self) -> int:
        """Get next unique key"""
        key = self.key_counter
        self.key_counter += 1
        return key
    
    def _escape_xml(self, text: str) -> str:
        if text is None:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def generate_json_profile_from_signature(
    name: str,
    fields: List[Dict],
    description: str = "",
    deployment_config: Optional[Dict] = None
) -> str:
    """
    Factory function to generate JSON Profile from signature fields.
    """
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiJSONProfileGenerator(config)
    return generator.generate(name, fields, description)


def generate_request_response_profiles(
    service_name: str,
    signature: Dict,
    deployment_config: Optional[Dict] = None
) -> Dict[str, str]:
    """
    Generate both request and response profiles from service signature.
    
    Args:
        service_name: Name of the service
        signature: Service signature with inputs and outputs
        deployment_config: Boomi deployment configuration
        
    Returns:
        Dictionary with 'request' and 'response' profile XMLs
    """
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiJSONProfileGenerator(config)
    
    result = {}
    
    # Request profile from inputs
    inputs = signature.get('inputs', [])
    if inputs:
        generator.key_counter = 1
        result['request'] = generator.generate(
            name=f"Profile_{service_name}_Request",
            fields=inputs,
            description=f"Request profile for {service_name}"
        )
    
    # Response profile from outputs
    outputs = signature.get('outputs', [])
    if outputs:
        generator.key_counter = 1
        result['response'] = generator.generate(
            name=f"Profile_{service_name}_Response",
            fields=outputs,
            description=f"Response profile for {service_name}"
        )
    
    return result


def generate_error_response_profile(
    deployment_config: Optional[Dict] = None
) -> str:
    """
    Generate standard error response profile.
    """
    error_fields = [
        {'name': 'error', 'type': 'object', 'children': [
            {'name': 'code', 'type': 'string'},
            {'name': 'message', 'type': 'string'},
            {'name': 'details', 'type': 'string'}
        ]}
    ]
    
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiJSONProfileGenerator(config)
    
    return generator.generate(
        name="Profile_Error_Response",
        fields=error_fields,
        description="Standard error response profile"
    )
