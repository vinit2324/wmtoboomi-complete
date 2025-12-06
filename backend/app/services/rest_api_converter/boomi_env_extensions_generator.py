"""
Boomi Environment Extensions Generator
======================================
Generates Boomi Process Property Component XML for environment-specific
configurations extracted from webMethods Global Variables.

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentProperty:
    """Single environment property"""
    name: str
    property_type: str = "string"
    default_value: str = ""
    is_sensitive: bool = False
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.property_type,
            'defaultValue': self.default_value if not self.is_sensitive else '',
            'isSensitive': self.is_sensitive,
            'description': self.description
        }


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


class BoomiEnvExtensionsGenerator:
    """
    Generates Boomi Process Property Component XML for Environment Extensions.
    """
    
    BOOMI_NS = "http://api.platform.boomi.com/"
    
    SENSITIVE_PATTERNS = [
        'key', 'secret', 'password', 'token', 'auth', 
        'credential', 'pwd', 'apikey', 'api_key', 'private'
    ]
    
    # Standard properties for REST API integrations
    STANDARD_REST_PROPERTIES = [
        EnvironmentProperty(name='BASE_URL', property_type='string', 
                          description='Base URL for the external API'),
        EnvironmentProperty(name='API_KEY', property_type='string', is_sensitive=True,
                          description='API Key for authentication'),
        EnvironmentProperty(name='API_VERSION', property_type='string', default_value='v1',
                          description='API version'),
        EnvironmentProperty(name='TIMEOUT_MS', property_type='string', default_value='30000',
                          description='Request timeout in milliseconds'),
        EnvironmentProperty(name='RETRY_COUNT', property_type='string', default_value='3',
                          description='Number of retry attempts'),
    ]
    
    def __init__(self, config: Optional[BoomiDeploymentConfig] = None):
        self.config = config or BoomiDeploymentConfig()
    
    def generate(
        self,
        name: str,
        properties: List[EnvironmentProperty],
        description: str = ""
    ) -> str:
        """
        Generate complete Process Property Component XML.
        """
        timestamp = self.config.get_timestamp()
        
        # Generate encrypted values section
        encrypted_values = self._generate_encrypted_values(properties)
        
        # Generate properties section
        properties_xml = self._generate_properties(properties)
        
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
    type="process.processproperty">
  <bns:encryptedValues>
{encrypted_values}
  </bns:encryptedValues>
  <bns:description>{self._escape_xml(description)}</bns:description>
  <bns:object>
    <ProcessProperties>
      <ProcessProperty>
{properties_xml}
      </ProcessProperty>
    </ProcessProperties>
  </bns:object>
</bns:Component>'''
        
        return xml
    
    def _generate_encrypted_values(self, properties: List[EnvironmentProperty]) -> str:
        """Generate encrypted values section for sensitive properties"""
        encrypted = []
        
        for prop in properties:
            if prop.is_sensitive:
                encrypted.append(
                    f'    <bns:encryptedValue isSet="false" '
                    f'path="//ProcessProperty/Property[@key=\'{prop.name}\']/@value"/>'
                )
        
        if encrypted:
            return '\n'.join(encrypted)
        return '    <!-- No encrypted values -->'
    
    def _generate_properties(self, properties: List[EnvironmentProperty]) -> str:
        """Generate properties XML"""
        prop_elements = []
        
        for prop in properties:
            prop_type = "password" if prop.is_sensitive else prop.property_type
            default_val = "" if prop.is_sensitive else prop.default_value
            
            prop_elements.append(
                f'        <Property key="{self._escape_xml(prop.name)}" '
                f'label="{self._escape_xml(prop.name)}" '
                f'type="{prop_type}" '
                f'value="{self._escape_xml(default_val)}"/>'
            )
        
        return '\n'.join(prop_elements)
    
    def extract_from_global_variables(
        self,
        global_variables: List[Dict[str, Any]]
    ) -> List[EnvironmentProperty]:
        """Extract environment properties from webMethods global variables."""
        properties = []
        seen = set()
        
        for var in global_variables:
            var_name = var.get('name', '')
            if not var_name or var_name in seen:
                continue
            
            seen.add(var_name)
            
            is_sensitive = var.get('isSensitive', False) or self._is_sensitive(var_name)
            
            properties.append(EnvironmentProperty(
                name=var_name,
                property_type='string',
                default_value=var.get('value', '') if not is_sensitive else '',
                is_sensitive=is_sensitive,
                description=var.get('description', f'Migrated from webMethods: {var_name}')
            ))
        
        return properties
    
    def extract_from_java_code(self, java_code: str) -> List[EnvironmentProperty]:
        """Extract environment properties from Java service code."""
        properties = []
        seen = set()
        
        patterns = [
            r'GlobalVariables\.getString\s*\(\s*["\']([^"\']+)["\']',
            r'GlobalVariables\.getValue\s*\(\s*["\']([^"\']+)["\']',
            r'getGlobalVariable\s*\(\s*["\']([^"\']+)["\']',
            r'ServerAPI\.getGlobalVariableValue\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, java_code)
            for var_name in matches:
                if var_name not in seen:
                    seen.add(var_name)
                    is_sensitive = self._is_sensitive(var_name)
                    properties.append(EnvironmentProperty(
                        name=var_name,
                        property_type='string',
                        is_sensitive=is_sensitive,
                        description=f'Extracted from Java code'
                    ))
        
        # Also look for hardcoded URLs that should be externalized
        url_pattern = r'["\']?(https?://[^"\'<>\s]+)["\']?'
        url_matches = re.findall(url_pattern, java_code)
        if url_matches and 'BASE_URL' not in seen:
            seen.add('BASE_URL')
            properties.append(EnvironmentProperty(
                name='BASE_URL',
                property_type='string',
                default_value=url_matches[0],
                is_sensitive=False,
                description='Base URL extracted from hardcoded value'
            ))
        
        return properties
    
    def _is_sensitive(self, name: str) -> bool:
        """Check if variable name indicates sensitive data"""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in self.SENSITIVE_PATTERNS)
    
    def _escape_xml(self, text: str) -> str:
        if text is None:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    def get_standard_rest_properties(self) -> List[EnvironmentProperty]:
        """Get standard properties for REST API integrations"""
        return self.STANDARD_REST_PROPERTIES.copy()


def generate_environment_extensions_xml(
    name: str,
    properties: List[Dict[str, Any]],
    description: str = "",
    deployment_config: Optional[Dict] = None
) -> str:
    """Factory function to generate Environment Extensions XML."""
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiEnvExtensionsGenerator(config)
    
    env_properties = [
        EnvironmentProperty(
            name=p.get('name', ''),
            property_type=p.get('type', 'string'),
            default_value=p.get('defaultValue', ''),
            is_sensitive=p.get('isSensitive', False),
            description=p.get('description', '')
        )
        for p in properties
    ]
    
    return generator.generate(name, env_properties, description)


def generate_env_extensions_from_package(
    package_name: str,
    global_variables: List[Dict[str, Any]],
    java_services: List[Dict[str, Any]],
    deployment_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """Generate Environment Extensions from package data."""
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiEnvExtensionsGenerator(config)
    
    all_properties = []
    seen = set()
    
    # Extract from global variables
    for prop in generator.extract_from_global_variables(global_variables):
        if prop.name not in seen:
            seen.add(prop.name)
            all_properties.append(prop)
    
    # Extract from Java code
    for java_svc in java_services:
        java_code = java_svc.get('code', '')
        if java_code:
            for prop in generator.extract_from_java_code(java_code):
                if prop.name not in seen:
                    seen.add(prop.name)
                    all_properties.append(prop)
    
    # Add standard REST properties if not already present
    for std_prop in generator.get_standard_rest_properties():
        if std_prop.name not in seen:
            seen.add(std_prop.name)
            all_properties.append(std_prop)
    
    # Generate component name
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '', package_name)
    component_name = f"Props_{clean_name}_Config"
    
    # Generate XML
    xml = generator.generate(
        name=component_name,
        properties=all_properties,
        description=f"Environment Extensions for {package_name} - Migrated from webMethods"
    )
    
    return {
        'componentName': component_name,
        'properties': [p.to_dict() for p in all_properties],
        'xml': xml
    }
