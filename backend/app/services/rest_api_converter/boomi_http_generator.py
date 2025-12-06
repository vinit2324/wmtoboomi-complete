"""
Boomi HTTP Connector Generator
==============================
Generates Boomi HTTP Client Connection and Operation XML components.

Uses EXACT Boomi Platform API format for:
- HTTP Client Connection (connector-settings)
- HTTP Client Operation (connector-action)

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class AuthenticationType(str, Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    PASSWORD_DIGEST = "PASSWORD_DIGEST"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"
    AWS = "AWS"
    CUSTOM = "CUSTOM"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


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


class BoomiHTTPConnectionGenerator:
    """
    Generates Boomi HTTP Client Connection XML (connector-settings).
    """
    
    BOOMI_NS = "http://api.platform.boomi.com/"
    
    def __init__(self, config: Optional[BoomiDeploymentConfig] = None):
        self.config = config or BoomiDeploymentConfig()
        self.encrypted_values = []
    
    def generate(
        self,
        name: str,
        base_url: str,
        auth_type: AuthenticationType = AuthenticationType.NONE,
        description: str = "",
        username: str = "",
        password: str = "",
        oauth_settings: Optional[Dict] = None,
        oauth2_settings: Optional[Dict] = None,
        aws_settings: Optional[Dict] = None,
        timeout_ms: int = 60000,
        read_timeout_ms: int = 120000,
        trust_all_certs: bool = False,
        preemptive_auth: bool = True
    ) -> str:
        """
        Generate complete HTTP Client Connection XML.
        
        Args:
            name: Component name
            base_url: Base URL (can use ${env.VAR} for environment extensions)
            auth_type: Authentication type
            description: Component description
            username: Username for BASIC auth
            password: Password for BASIC auth
            oauth_settings: OAuth 1.0 settings dict
            oauth2_settings: OAuth 2.0 settings dict
            aws_settings: AWS signature settings dict
            timeout_ms: Connection timeout in milliseconds
            read_timeout_ms: Read timeout in milliseconds
            trust_all_certs: Trust all SSL certificates
            preemptive_auth: Use preemptive authentication
            
        Returns:
            Complete Boomi HTTP Client Connection XML
        """
        self.encrypted_values = []
        timestamp = self.config.get_timestamp()
        
        # Build component sections
        http_settings = self._generate_http_settings(
            base_url, auth_type, username, password,
            timeout_ms, read_timeout_ms, trust_all_certs, preemptive_auth
        )
        
        auth_settings = self._generate_auth_settings(auth_type, username, password)
        oauth_section = self._generate_oauth_settings(oauth_settings) if oauth_settings else ""
        oauth2_section = self._generate_oauth2_settings(oauth2_settings) if oauth2_settings else ""
        aws_section = self._generate_aws_settings(aws_settings) if aws_settings else ""
        ssl_options = self._generate_ssl_options(trust_all_certs)
        encrypted_section = self._generate_encrypted_values()
        
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
    type="connector-settings"
    subType="http">
{encrypted_section}
  <bns:description>{self._escape_xml(description)}</bns:description>
  <bns:object>
    <HttpSettings>
{http_settings}
{auth_settings}
{oauth_section}
{oauth2_section}
{aws_section}
{ssl_options}
    </HttpSettings>
  </bns:object>
</bns:Component>'''
        
        return xml
    
    def _generate_http_settings(
        self, url: str, auth_type: AuthenticationType,
        username: str, password: str,
        timeout_ms: int, read_timeout_ms: int,
        trust_all_certs: bool, preemptive_auth: bool
    ) -> str:
        """Generate HttpSettings element"""
        return f'''      <authenticationType>{auth_type.value}</authenticationType>
      <url>{self._escape_xml(url)}</url>
      <cookieScope>GLOBAL</cookieScope>
      <timeout>{timeout_ms}</timeout>
      <readTimeout>{read_timeout_ms}</readTimeout>
      <preemptive>{str(preemptive_auth).lower()}</preemptive>'''
    
    def _generate_auth_settings(
        self, auth_type: AuthenticationType,
        username: str, password: str
    ) -> str:
        """Generate AuthSettings element for BASIC auth"""
        if auth_type not in [AuthenticationType.BASIC, AuthenticationType.PASSWORD_DIGEST]:
            return ""
        
        if password:
            self.encrypted_values.append("//HttpSettings/AuthSettings/@password")
        
        return f'''      <AuthSettings user="{self._escape_xml(username)}" password=""/>'''
    
    def _generate_oauth_settings(self, settings: Dict) -> str:
        """Generate OAuthSettings element for OAuth 1.0"""
        consumer_key = settings.get('consumerKey', '')
        consumer_secret = settings.get('consumerSecret', '')
        access_token = settings.get('accessToken', '')
        token_secret = settings.get('tokenSecret', '')
        
        if consumer_secret:
            self.encrypted_values.append("//HttpSettings/OAuthSettings/@consumerSecret")
        if token_secret:
            self.encrypted_values.append("//HttpSettings/OAuthSettings/@tokenSecret")
        
        return f'''      <OAuthSettings 
        consumerKey="{self._escape_xml(consumer_key)}"
        consumerSecret=""
        accessToken="{self._escape_xml(access_token)}"
        tokenSecret=""/>'''
    
    def _generate_oauth2_settings(self, settings: Dict) -> str:
        """Generate OAuth2Settings element for OAuth 2.0"""
        client_id = settings.get('clientId', '')
        client_secret = settings.get('clientSecret', '')
        scope = settings.get('scope', '')
        grant_type = settings.get('grantType', 'CLIENT_CREDENTIALS')
        token_url = settings.get('tokenUrl', '')
        
        if client_secret:
            self.encrypted_values.append("//HttpSettings/OAuth2Settings/@clientSecret")
        
        return f'''      <OAuth2Settings
        grantType="{grant_type}"
        clientId="{self._escape_xml(client_id)}"
        clientSecret=""
        scope="{self._escape_xml(scope)}"
        accessTokenUrl="{self._escape_xml(token_url)}"/>'''
    
    def _generate_aws_settings(self, settings: Dict) -> str:
        """Generate AwsSettings element for AWS Signature"""
        access_key = settings.get('accessKey', '')
        secret_key = settings.get('secretKey', '')
        region = settings.get('region', 'us-east-1')
        service = settings.get('service', 'execute-api')
        
        if secret_key:
            self.encrypted_values.append("//HttpSettings/AwsSettings/@secretKey")
        
        return f'''      <AwsSettings
        accessKey="{self._escape_xml(access_key)}"
        secretKey=""
        region="{region}"
        service="{service}"/>'''
    
    def _generate_ssl_options(self, trust_all: bool) -> str:
        """Generate SSLOptions element"""
        return f'''      <SSLOptions clientauth="false" trustServerCert="{str(trust_all).lower()}"/>'''
    
    def _generate_encrypted_values(self) -> str:
        """Generate encryptedValues section"""
        if not self.encrypted_values:
            return "  <bns:encryptedValues/>"
        
        values = '\n'.join([
            f'    <bns:encryptedValue isSet="false" path="{path}"/>'
            for path in self.encrypted_values
        ])
        return f"  <bns:encryptedValues>\n{values}\n  </bns:encryptedValues>"
    
    def _escape_xml(self, text: str) -> str:
        if text is None:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


class BoomiHTTPOperationGenerator:
    """
    Generates Boomi HTTP Client Operation XML (connector-action).
    """
    
    BOOMI_NS = "http://api.platform.boomi.com/"
    
    def __init__(self, config: Optional[BoomiDeploymentConfig] = None):
        self.config = config or BoomiDeploymentConfig()
    
    def generate(
        self,
        name: str,
        method: HTTPMethod = HTTPMethod.GET,
        description: str = "",
        resource_path: str = "",
        request_content_type: str = "application/json",
        response_content_type: str = "application/json",
        request_profile_id: str = "",
        response_profile_id: str = "",
        custom_headers: Optional[List[Dict]] = None,
        follow_redirects: bool = True,
        return_errors: bool = True
    ) -> str:
        """
        Generate complete HTTP Client Operation XML.
        
        Args:
            name: Component name
            method: HTTP method
            description: Component description
            resource_path: Resource path (e.g., /api/v1/stores/{storeId})
            request_content_type: Request content type
            response_content_type: Response content type
            request_profile_id: ID of request JSON profile
            response_profile_id: ID of response JSON profile
            custom_headers: List of custom headers
            follow_redirects: Follow HTTP redirects
            return_errors: Return error responses
            
        Returns:
            Complete Boomi HTTP Client Operation XML
        """
        timestamp = self.config.get_timestamp()
        
        path_elements = self._generate_path_elements(resource_path)
        headers_section = self._generate_headers(custom_headers or [])
        
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
    type="connector-action"
    subType="http">
  <bns:encryptedValues/>
  <bns:description>{self._escape_xml(description)}</bns:description>
  <bns:object>
    <HttpSendAction methodType="{method.value}">
      <dataContentType>{request_content_type}</dataContentType>
      <returnErrorContent>{str(return_errors).lower()}</returnErrorContent>
      <followRedirects>{str(follow_redirects).lower()}</followRedirects>
{path_elements}
{headers_section}
      <responseHeaderMapping/>
      <Overrides/>
      <Archiving/>
      <Tracking dir="NONE"/>
      <Caching/>
    </HttpSendAction>
  </bns:object>
</bns:Component>'''
        
        return xml
    
    def _generate_path_elements(self, resource_path: str) -> str:
        """Generate pathElements from resource path"""
        if not resource_path:
            return "      <pathElements/>"
        
        # Split path and identify variables
        parts = resource_path.strip('/').split('/')
        elements = []
        
        for i, part in enumerate(parts):
            if part.startswith('{') and part.endswith('}'):
                # Variable path element
                var_name = part[1:-1]
                elements.append(
                    f'        <pathElement isVariable="true" key="{i}" name="{var_name}"/>'
                )
            else:
                # Static path element
                elements.append(
                    f'        <pathElement isVariable="false" key="{i}" name="{self._escape_xml(part)}"/>'
                )
        
        if elements:
            return "      <pathElements>\n" + '\n'.join(elements) + "\n      </pathElements>"
        return "      <pathElements/>"
    
    def _generate_headers(self, headers: List[Dict]) -> str:
        """Generate requestHeaders section"""
        if not headers:
            return "      <requestHeaders/>"
        
        header_elements = []
        for h in headers:
            header_elements.append(
                f'        <requestHeader name="{self._escape_xml(h.get("name", ""))}" '
                f'value="{self._escape_xml(h.get("value", ""))}"/>'
            )
        
        return "      <requestHeaders>\n" + '\n'.join(header_elements) + "\n      </requestHeaders>"
    
    def _escape_xml(self, text: str) -> str:
        if text is None:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def generate_http_connection_xml(
    name: str,
    base_url: str,
    auth_type: str = "NONE",
    deployment_config: Optional[Dict] = None,
    **kwargs
) -> str:
    """
    Factory function to generate HTTP Connection XML.
    """
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiHTTPConnectionGenerator(config)
    return generator.generate(
        name=name,
        base_url=base_url,
        auth_type=AuthenticationType(auth_type),
        **kwargs
    )


def generate_http_operation_xml(
    name: str,
    method: str = "GET",
    resource_path: str = "",
    deployment_config: Optional[Dict] = None,
    **kwargs
) -> str:
    """
    Factory function to generate HTTP Operation XML.
    """
    config = BoomiDeploymentConfig(**deployment_config) if deployment_config else BoomiDeploymentConfig()
    generator = BoomiHTTPOperationGenerator(config)
    return generator.generate(
        name=name,
        method=HTTPMethod(method),
        resource_path=resource_path,
        **kwargs
    )
