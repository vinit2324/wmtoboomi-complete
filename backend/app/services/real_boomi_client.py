"""
Real Boomi API Client - Uses Exact Format from Vinit's Postman Setup
"""

import httpx
import base64
from typing import Dict, Any, Optional

class RealBoomiClient:
    """
    Boomi API Client using exact format:
    - POST https://api.boomi.com/api/rest/v1/{accountId}/Component
    - Basic Auth (username:password)
    - Boomi XML in request body
    """
    
    def __init__(self, account_id: str, username: str, password: str):
        """
        Initialize Boomi client
        
        Args:
            account_id: Boomi account ID (e.g., "jadeglobalinc-LPA4UJ")
            username: Boomi username
            password: Boomi password
        """
        self.account_id = account_id
        self.username = username
        self.password = password
        self.base_url = f"https://api.boomi.com/api/rest/v1/{account_id}"
        
    def _get_auth_header(self) -> str:
        """Create Basic Auth header"""
        
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded}"
    
    async def push_component(
        self,
        component_xml: str,
        component_name: str
    ) -> Dict[str, Any]:
        """
        Push component to Boomi
        
        Args:
            component_xml: Complete Boomi component XML
            component_name: Name of the component
            
        Returns:
            API response with component ID and status
        """
        
        url = f"{self.base_url}/Component"
        
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/xml",
            "Accept": "application/xml"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url=url,
                    headers=headers,
                    content=component_xml
                )
                
                if response.status_code in [200, 201]:
                    # Success - parse response
                    return {
                        'success': True,
                        'status': response.status_code,
                        'componentId': self._extract_component_id(response.text),
                        'componentUrl': f"https://platform.boomi.com/{self.account_id}/component/{self._extract_component_id(response.text)}",
                        'message': 'Component created successfully',
                        'response': response.text
                    }
                
                else:
                    # Error
                    return {
                        'success': False,
                        'status': response.status_code,
                        'error': response.text,
                        'message': f'Failed to create component: {response.status_code}'
                    }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'Boomi API request timed out after 30 seconds'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Error calling Boomi API: {str(e)}'
            }
    
    def _extract_component_id(self, response_xml: str) -> Optional[str]:
        """Extract component ID from Boomi API response"""
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response_xml)
            
            # Look for componentId in response
            for elem in root.iter():
                if 'componentId' in elem.tag.lower() or elem.tag == 'id':
                    return elem.text
            
            return None
        
        except Exception:
            return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Boomi API connection"""
        
        url = f"{self.base_url}/Account/{self.account_id}"
        
        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url=url, headers=headers)
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'message': 'Connection successful',
                        'accountId': self.account_id
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Connection failed: {response.status_code}',
                        'error': response.text
                    }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }


def create_boomi_profile_xml(
    profile_name: str,
    profile_type: str,
    schema_content: str
) -> str:
    """
    Create Boomi Profile XML in exact format for API
    
    Args:
        profile_name: Name of the profile
        profile_type: Type (xml, json, edi, flat)
        schema_content: The actual schema (XSD, JSON Schema, etc.)
        
    Returns:
        Complete Boomi Profile XML ready to POST
    """
    
    # Map profile types to Boomi profile types
    type_map = {
        'xml': 'profile.xml',
        'json': 'profile.json',
        'edi': 'profile.edi',
        'flat': 'profile.flat'
    }
    
    boomi_type = type_map.get(profile_type.lower(), 'profile.xml')
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Component xmlns="http://api.platform.boomi.com/" type="{boomi_type}">
    <name>{profile_name}</name>
    <description>Converted from webMethods by Migration Accelerator</description>
    <object>
        <ProfileConfig>
            <schema><![CDATA[
{schema_content}
            ]]></schema>
        </ProfileConfig>
    </object>
</Component>'''
    
    return xml


def create_boomi_process_xml(
    process_name: str,
    shapes: list,
    connections: list
) -> str:
    """
    Create Boomi Process XML in exact format for API
    
    Args:
        process_name: Name of the process
        shapes: List of shape definitions
        connections: List of connection definitions
        
    Returns:
        Complete Boomi Process XML ready to POST
    """
    
    shapes_xml = ""
    for shape in shapes:
        shapes_xml += f'''
        <Shape>
            <shapeId>{shape['id']}</shapeId>
            <type>{shape['type']}</type>
            <label>{shape['label']}</label>
            <x>{shape.get('x', 100)}</x>
            <y>{shape.get('y', 100)}</y>
        </Shape>'''
    
    connections_xml = ""
    for conn in connections:
        connections_xml += f'''
        <Connection>
            <connectionId>{conn['id']}</connectionId>
            <from>{conn['from']}</from>
            <to>{conn['to']}</to>
        </Connection>'''
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Component xmlns="http://api.platform.boomi.com/" type="process">
    <name>{process_name}</name>
    <description>Converted from webMethods by Migration Accelerator</description>
    <object>
        <ProcessConfig>
            <shapes>{shapes_xml}
            </shapes>
            <connections>{connections_xml}
            </connections>
        </ProcessConfig>
    </object>
</Component>'''
    
    return xml
