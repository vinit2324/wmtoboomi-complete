"""
Validation and Deployment Pipeline
Validates generated Boomi XML and deploys to Boomi with retries
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ET
import re

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    level: ValidationLevel
    category: str
    message: str
    location: Optional[str] = None
    fix_suggestion: Optional[str] = None

class BoomiXMLValidator:
    """Validates generated Boomi XML before deployment"""
    
    def __init__(self):
        self.required_namespaces = {
            'bns': 'http://api.platform.boomi.com/'
        }
        
    def validate_xml(self, xml_string: str, component_type: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate Boomi XML
        
        Args:
            xml_string: The XML to validate
            component_type: Type of component (Process, Profile, etc.)
            
        Returns:
            (is_valid, list_of_issues)
        """
        
        issues = []
        
        # Check if XML is well-formed
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="XML Structure",
                message=f"XML is not well-formed: {str(e)}",
                fix_suggestion="Check for unclosed tags and special characters"
            ))
            return False, issues
        
        # Validate namespaces
        issues.extend(self._validate_namespaces(root))
        
        # Validate based on component type
        if component_type.lower() in ['process', 'flow']:
            issues.extend(self._validate_process(root))
        elif component_type.lower() in ['profile', 'xml', 'json', 'edi']:
            issues.extend(self._validate_profile(root))
        elif component_type.lower() in ['connector', 'database', 'http', 'ftp']:
            issues.extend(self._validate_connector(root))
        
        # Check for errors
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in issues)
        
        return not has_errors, issues
    
    def _validate_namespaces(self, root: ET.Element) -> List[ValidationIssue]:
        """Validate XML namespaces"""
        
        issues = []
        
        # Check for required namespace
        if not any('boomi.com' in ns for ns in root.nsmap.values() if root.nsmap and ns):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Namespace",
                message="Missing Boomi namespace",
                fix_suggestion="Add xmlns:bns='http://api.platform.boomi.com/'"
            ))
        
        return issues
    
    def _validate_process(self, root: ET.Element) -> List[ValidationIssue]:
        """Validate Process XML"""
        
        issues = []
        
        # Check for required elements
        required_elements = ['name', 'shapes', 'connections']
        for elem in required_elements:
            if not root.find(f'.//*[local-name()="{elem}"]'):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="Process Structure",
                    message=f"Missing required element: {elem}",
                    fix_suggestion=f"Add <bns:{elem}> element"
                ))
        
        # Validate shapes
        shapes = root.findall('.//*[local-name()="shape"]')
        if len(shapes) < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="Process Structure",
                message="Process has fewer than 2 shapes (should have at least Start and Stop)",
                fix_suggestion="Add Start and Stop shapes"
            ))
        
        # Check for Start and Stop shapes
        shape_types = [s.find('.//*[local-name()="type"]').text for s in shapes if s.find('.//*[local-name()="type"]') is not None]
        if 'Start' not in shape_types:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Process Structure",
                message="Missing Start shape",
                fix_suggestion="Add Start shape as first element"
            ))
        if 'Stop' not in shape_types:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Process Structure",
                message="Missing Stop shape",
                fix_suggestion="Add Stop shape as last element"
            ))
        
        # Validate connections
        connections = root.findall('.//*[local-name()="connection"]')
        if len(connections) < len(shapes) - 1:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="Process Structure",
                message="Insufficient connections between shapes",
                fix_suggestion="Ensure all shapes are connected"
            ))
        
        # Check for orphaned shapes
        shape_ids = {s.find('.//*[local-name()="shapeId"]').text for s in shapes if s.find('.//*[local-name()="shapeId"]') is not None}
        connected_shapes = set()
        for conn in connections:
            from_shape = conn.find('.//*[local-name()="fromShapeId"]')
            to_shape = conn.find('.//*[local-name()="toShapeId"]')
            if from_shape is not None:
                connected_shapes.add(from_shape.text)
            if to_shape is not None:
                connected_shapes.add(to_shape.text)
        
        orphaned = shape_ids - connected_shapes
        if orphaned:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="Process Structure",
                message=f"{len(orphaned)} orphaned shape(s) not connected to process flow",
                fix_suggestion="Connect all shapes or remove unused ones"
            ))
        
        return issues
    
    def _validate_profile(self, root: ET.Element) -> List[ValidationIssue]:
        """Validate Profile XML"""
        
        issues = []
        
        # Check for required elements
        if not root.find('.//*[local-name()="name"]'):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Profile Structure",
                message="Missing profile name",
                fix_suggestion="Add <bns:name> element"
            ))
        
        # Check for schema
        schema = root.find('.//*[local-name()="schema"]')
        if schema is None:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Profile Structure",
                message="Missing schema definition",
                fix_suggestion="Add <bns:schema> element with XSD/JSON Schema"
            ))
        else:
            # Validate schema content
            if len(schema.text or '') < 10:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="Profile Structure",
                    message="Schema appears to be empty or too short",
                    fix_suggestion="Ensure schema is properly defined"
                ))
        
        return issues
    
    def _validate_connector(self, root: ET.Element) -> List[ValidationIssue]:
        """Validate Connector XML"""
        
        issues = []
        
        # Check for required elements
        if not root.find('.//*[local-name()="operation"]'):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="Connector Structure",
                message="Missing operation type",
                fix_suggestion="Add <bns:operation> element (e.g., GET, POST, query)"
            ))
        
        return issues


class DeploymentPipeline:
    """Handles deployment to Boomi with retries and error handling"""
    
    def __init__(self, boomi_client):
        self.boomi_client = boomi_client
        self.validator = BoomiXMLValidator()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    async def deploy_component(
        self,
        component_name: str,
        component_type: str,
        boomi_xml: str,
        validate_first: bool = True
    ) -> Dict:
        """
        Deploy a component to Boomi with validation and retries
        
        Args:
            component_name: Name of the component
            component_type: Type (Process, Profile, etc.)
            boomi_xml: The XML to deploy
            validate_first: Whether to validate before deploying
            
        Returns:
            Deployment result with component ID and status
        """
        
        result = {
            'success': False,
            'component_id': None,
            'component_url': None,
            'attempts': 0,
            'errors': [],
            'warnings': []
        }
        
        # Validate first if requested
        if validate_first:
            is_valid, issues = self.validator.validate_xml(boomi_xml, component_type)
            
            # Add warnings
            result['warnings'] = [issue.message for issue in issues if issue.level == ValidationLevel.WARNING]
            
            if not is_valid:
                result['errors'] = [issue.message for issue in issues if issue.level == ValidationLevel.ERROR]
                return result
        
        # Attempt deployment with retries
        for attempt in range(1, self.max_retries + 1):
            result['attempts'] = attempt
            
            try:
                response = await self.boomi_client.create_component(
                    component_xml=boomi_xml,
                    component_type=component_type
                )
                
                result['success'] = True
                result['component_id'] = response.get('componentId')
                result['component_url'] = response.get('componentUrl')
                break
                
            except Exception as e:
                error_msg = str(e)
                result['errors'].append(f"Attempt {attempt}: {error_msg}")
                
                # Check if error is retryable
                if attempt < self.max_retries and self._is_retryable_error(error_msg):
                    import asyncio
                    await asyncio.sleep(self.retry_delay * attempt)
                    continue
                else:
                    break
        
        return result
    
    def _is_retryable_error(self, error_message: str) -> bool:
        """Determine if an error is worth retrying"""
        
        retryable_patterns = [
            'timeout',
            'connection',
            'temporary',
            '503',
            '504',
            'rate limit'
        ]
        
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in retryable_patterns)
    
    async def deploy_batch(
        self,
        components: List[Dict],
        validate_first: bool = True
    ) -> List[Dict]:
        """
        Deploy multiple components as a batch
        
        Args:
            components: List of components to deploy
                Each component should have: name, type, xml
            validate_first: Whether to validate before deploying
            
        Returns:
            List of deployment results
        """
        
        results = []
        
        for component in components:
            result = await self.deploy_component(
                component_name=component['name'],
                component_type=component['type'],
                boomi_xml=component['xml'],
                validate_first=validate_first
            )
            results.append({
                'name': component['name'],
                'type': component['type'],
                **result
            })
        
        return results


def validate_and_fix_common_issues(xml_string: str) -> str:
    """
    Automatically fix common XML issues
    
    Args:
        xml_string: The XML to fix
        
    Returns:
        Fixed XML string
    """
    
    # Fix common namespace issues
    if 'xmlns:bns' not in xml_string:
        xml_string = xml_string.replace(
            '<bns:',
            '<bns:' if 'xmlns:bns=' in xml_string else '<bns: xmlns:bns="http://api.platform.boomi.com/" '
        )
    
    # Escape unescaped ampersands
    xml_string = re.sub(r'&(?![a-zA-Z]+;)', '&amp;', xml_string)
    
    # Remove invalid XML characters
    xml_string = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', xml_string)
    
    # Ensure proper XML declaration
    if not xml_string.strip().startswith('<?xml'):
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
    
    return xml_string
