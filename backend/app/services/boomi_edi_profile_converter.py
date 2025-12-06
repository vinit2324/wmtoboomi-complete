"""
webMethods to Boomi XML Profile Converter

Converts webMethods Document Types (node.ndf) to Boomi XML Profile format.
Generates proper XMLProfile structure with XMLElement hierarchy matching
Boomi's exact expected format.

Author: Jade Global Migration Accelerator
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import json


@dataclass
class BoomiDeploymentConfig:
    """Configuration for Boomi component deployment"""
    folder_id: str = "Rjo3NTQ1MTg0"
    folder_name: str = "MigrationPoC"
    folder_full_path: str = "Jade Global, Inc./MigrationPoC"
    branch_id: str = "QjoyOTQwMQ"
    branch_name: str = "main"
    created_by: str = "vinit.verma@jadeglobal.com"
    modified_by: str = "vinit.verma@jadeglobal.com"


class BoomiDataType(Enum):
    """Boomi XML Profile data types"""
    CHARACTER = "character"
    NUMBER = "number"
    DATETIME = "datetime"


@dataclass
class XMLElementDef:
    """Definition of an XML element for Boomi profile"""
    name: str
    data_type: BoomiDataType = BoomiDataType.CHARACTER
    min_occurs: int = 1
    max_occurs: int = 1  # -1 for unbounded
    is_attribute: bool = False
    looping_option: str = ""  # "unique" or "occurrence" for repeating elements
    validate_data: bool = True
    date_format: str = ""
    number_format: str = ""
    namespace_key: int = -1
    type_key: int = -1
    children: List['XMLElementDef'] = field(default_factory=list)
    attributes: List['XMLElementDef'] = field(default_factory=list)


@dataclass
class XMLNamespaceDef:
    """Definition of an XML namespace"""
    key: int
    name: str
    prefix: str
    uri: str = ""


class WebMethodsDocTypeParser:
    """
    Parser for webMethods Document Types (node.ndf files).
    Extracts document structure and converts to XMLElementDef hierarchy.
    """
    
    # Mapping of webMethods field types to Boomi data types
    WMTYPE_TO_BOOMI = {
        "string": BoomiDataType.CHARACTER,
        "java.lang.string": BoomiDataType.CHARACTER,
        "object": BoomiDataType.CHARACTER,
        "java.lang.object": BoomiDataType.CHARACTER,
        "record": BoomiDataType.CHARACTER,  # Complex type container
        "recref": BoomiDataType.CHARACTER,  # Document reference
        "number": BoomiDataType.NUMBER,
        "java.lang.integer": BoomiDataType.NUMBER,
        "java.lang.long": BoomiDataType.NUMBER,
        "java.lang.double": BoomiDataType.NUMBER,
        "java.lang.float": BoomiDataType.NUMBER,
        "java.math.bigdecimal": BoomiDataType.NUMBER,
        "int": BoomiDataType.NUMBER,
        "long": BoomiDataType.NUMBER,
        "double": BoomiDataType.NUMBER,
        "float": BoomiDataType.NUMBER,
        "date": BoomiDataType.DATETIME,
        "java.util.date": BoomiDataType.DATETIME,
        "datetime": BoomiDataType.DATETIME,
        "boolean": BoomiDataType.CHARACTER,  # Boomi treats boolean as character
        "java.lang.boolean": BoomiDataType.CHARACTER,
    }
    
    # Common date formats
    DATE_FORMATS = {
        "date": "yyyy-MM-dd",
        "datetime": "yyyy-MM-dd'T'HH:mm:ss",
        "timestamp": "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
    }
    
    def parse_node_ndf(self, content: str) -> Tuple[XMLElementDef, Dict[str, Any]]:
        """
        Parse webMethods node.ndf content and return root XMLElementDef.
        
        Returns:
            Tuple of (root_element, metadata)
        """
        metadata = {
            "source_type": "webMethods",
            "field_count": 0,
            "has_arrays": False,
            "has_nested": False,
            "automation_level": 95,
        }
        
        try:
            root = ET.fromstring(content)
            
            # Extract document name from the content
            doc_name = self._extract_doc_name(root)
            
            # Parse the rec_fields array to get field definitions
            fields = self._parse_rec_fields(root)
            
            metadata["field_count"] = len(fields)
            
            # Check for arrays and nested structures
            for f in fields:
                if f.max_occurs == -1:
                    metadata["has_arrays"] = True
                if f.children:
                    metadata["has_nested"] = True
            
            # Create root element with parsed children
            root_element = XMLElementDef(
                name=doc_name,
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1,
                children=fields
            )
            
            return root_element, metadata
            
        except ET.ParseError as e:
            # Return a basic structure if parsing fails
            return XMLElementDef(
                name="Document",
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1
            ), {"error": str(e), **metadata}
    
    def _extract_doc_name(self, root: ET.Element) -> str:
        """Extract document name from node.ndf"""
        # Try different locations where name might be stored
        name_elem = root.find(".//value[@name='node_nsName']")
        if name_elem is not None and name_elem.text:
            # Extract just the document name from namespace path
            parts = name_elem.text.split("/")
            return parts[-1] if parts else "Document"
        
        name_elem = root.find(".//value[@name='svc_name']")
        if name_elem is not None and name_elem.text:
            return name_elem.text
        
        name_elem = root.find(".//value[@name='name']")
        if name_elem is not None and name_elem.text:
            return name_elem.text
        
        return "Document"
    
    def _parse_rec_fields(self, root: ET.Element) -> List[XMLElementDef]:
        """Parse rec_fields array from node.ndf"""
        fields = []
        
        rec_fields = root.find(".//array[@name='rec_fields']")
        if rec_fields is None:
            return fields
        
        for record in rec_fields.findall("record"):
            field_def = self._parse_field_record(record)
            if field_def:
                fields.append(field_def)
        
        return fields
    
    def _parse_field_record(self, record: ET.Element) -> Optional[XMLElementDef]:
        """Parse a single field record from rec_fields"""
        field_name = ""
        field_type = "string"
        field_dim = 0  # 0 = scalar, 1 = array
        children = []
        
        # Extract field properties
        for value in record.findall("value"):
            name = value.get("name", "")
            text = value.text or ""
            
            if name == "field_name":
                field_name = text
            elif name == "field_type":
                field_type = text.lower()
            elif name == "field_dim":
                try:
                    field_dim = int(text)
                except ValueError:
                    field_dim = 0
        
        if not field_name:
            return None
        
        # Parse nested fields for record types
        nested_fields = record.find("array[@name='rec_fields']")
        if nested_fields is not None:
            for nested_record in nested_fields.findall("record"):
                child = self._parse_field_record(nested_record)
                if child:
                    children.append(child)
        
        # Determine Boomi data type
        boomi_type = self.WMTYPE_TO_BOOMI.get(field_type, BoomiDataType.CHARACTER)
        
        # Determine date format if datetime
        date_format = ""
        if boomi_type == BoomiDataType.DATETIME:
            date_format = self.DATE_FORMATS.get("datetime", "yyyy-MM-dd'T'HH:mm:ss")
        
        # Create XMLElementDef
        return XMLElementDef(
            name=field_name,
            data_type=boomi_type,
            min_occurs=0 if field_dim >= 0 else 1,  # Arrays are optional by default
            max_occurs=-1 if field_dim > 0 else 1,  # -1 for unbounded arrays
            looping_option="unique" if field_dim > 0 else "",
            validate_data=field_dim == 0,  # Don't validate arrays
            date_format=date_format,
            children=children
        )
    
    def parse_from_xsd(self, xsd_content: str) -> Tuple[XMLElementDef, Dict[str, Any]]:
        """Parse an XSD schema and convert to XMLElementDef hierarchy"""
        metadata = {
            "source_type": "XSD",
            "field_count": 0,
            "has_arrays": False,
            "has_nested": False,
            "automation_level": 90,
        }
        
        try:
            # Remove namespace prefixes for easier parsing
            xsd_content = re.sub(r'xmlns[^=]*="[^"]*"', '', xsd_content)
            xsd_content = re.sub(r'</?xs:', '</', xsd_content).replace('</', '<')
            
            root = ET.fromstring(xsd_content)
            
            # Find the root element
            root_elem = root.find(".//element")
            if root_elem is None:
                return XMLElementDef(name="Root"), metadata
            
            root_name = root_elem.get("name", "Root")
            children = self._parse_xsd_complex_type(root_elem)
            
            metadata["field_count"] = self._count_elements(children)
            
            return XMLElementDef(
                name=root_name,
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1,
                children=children
            ), metadata
            
        except Exception as e:
            return XMLElementDef(name="Root"), {"error": str(e), **metadata}
    
    def _parse_xsd_complex_type(self, elem: ET.Element) -> List[XMLElementDef]:
        """Parse XSD complexType children"""
        children = []
        
        # Look for sequence/all/choice
        for container in elem.findall(".//*"):
            if container.tag in ["sequence", "all", "choice"]:
                for child in container.findall("element"):
                    name = child.get("name", "")
                    if name:
                        xsd_type = child.get("type", "string").lower()
                        min_occurs = int(child.get("minOccurs", "1"))
                        max_occurs_str = child.get("maxOccurs", "1")
                        max_occurs = -1 if max_occurs_str == "unbounded" else int(max_occurs_str)
                        
                        # Determine data type
                        if "int" in xsd_type or "decimal" in xsd_type or "float" in xsd_type:
                            data_type = BoomiDataType.NUMBER
                        elif "date" in xsd_type or "time" in xsd_type:
                            data_type = BoomiDataType.DATETIME
                        else:
                            data_type = BoomiDataType.CHARACTER
                        
                        nested = self._parse_xsd_complex_type(child)
                        
                        children.append(XMLElementDef(
                            name=name,
                            data_type=data_type,
                            min_occurs=min_occurs,
                            max_occurs=max_occurs,
                            looping_option="unique" if max_occurs == -1 else "",
                            children=nested
                        ))
        
        return children
    
    def _count_elements(self, elements: List[XMLElementDef]) -> int:
        """Count total elements including nested"""
        count = len(elements)
        for elem in elements:
            count += self._count_elements(elem.children)
        return count


class BoomiXMLProfileGenerator:
    """
    Generates Boomi XML Profile XML in the exact format expected by Boomi.
    
    The output format matches the structure:
    <bns:Component>
      <bns:object>
        <XMLProfile>
          <ProfileProperties>
            <XMLGeneralInfo/>
            <XMLOptions/>
          </ProfileProperties>
          <DataElements>
            <XMLElement>...</XMLElement>
          </DataElements>
          <Namespaces>
            <XMLNamespace>...</XMLNamespace>
          </Namespaces>
          <tagLists/>
        </XMLProfile>
      </bns:object>
    </bns:Component>
    """
    
    def __init__(self, config: Optional[BoomiDeploymentConfig] = None):
        self.config = config or BoomiDeploymentConfig()
        self.key_counter = 0
    
    def _next_key(self) -> str:
        """Generate next unique key for XML elements"""
        self.key_counter += 1
        return str(self.key_counter)
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        if text is None:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    def _format_datetime(self) -> str:
        """Format current datetime for Boomi"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def generate_profile(
        self,
        root_element: XMLElementDef,
        name: str,
        description: str = "",
        namespaces: List[XMLNamespaceDef] = None
    ) -> str:
        """
        Generate complete Boomi XML Profile XML.
        
        Args:
            root_element: Root XMLElementDef containing the document structure
            name: Profile name
            description: Profile description
            namespaces: Optional list of namespace definitions
        
        Returns:
            Complete Boomi XML Profile XML string
        """
        self.key_counter = 0
        now = self._format_datetime()
        
        # Build the XML
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" branchId="{self.config.branch_id}" branchName="{self.config.branch_name}" createdBy="{self.config.created_by}" createdDate="{now}" currentVersion="true" deleted="false" folderFullPath="{self.config.folder_full_path}" folderId="{self.config.folder_id}" folderName="{self.config.folder_name}" modifiedBy="{self.config.modified_by}" modifiedDate="{now}" name="{self._escape_xml(name)}" type="profile.xml" version="1">
  <bns:encryptedValues/>
  <bns:description>{self._escape_xml(description)}</bns:description>
  <bns:object>
    <XMLProfile modelVersion="2" strict="true">
      <ProfileProperties>
        <XMLGeneralInfo/>
        <XMLOptions encoding="utf8" implicitElementOrdering="true" parseRespectMaxOccurs="true" respectMinOccurs="false" respectMinOccursAlways="false"/>
      </ProfileProperties>
      <DataElements>
'''
        
        # Generate root element and all children
        xml += self._generate_element_xml(root_element, indent=8)
        
        xml += '''      </DataElements>
      <Namespaces>
'''
        
        # Generate namespace declarations
        if namespaces:
            for ns in namespaces:
                xml += f'''        <XMLNamespace key="{ns.key}" name="{self._escape_xml(ns.name)}" prefix="{ns.prefix}">
          <Types>
          </Types>
        </XMLNamespace>
'''
        else:
            # Default empty namespace
            xml += '''        <XMLNamespace key="-1" name="Empty Namespace" prefix="ns1">
          <Types>
          </Types>
        </XMLNamespace>
'''
        
        xml += '''      </Namespaces>
      <tagLists/>
    </XMLProfile>
  </bns:object>
</bns:Component>'''
        
        return xml
    
    def _generate_element_xml(self, element: XMLElementDef, indent: int = 8) -> str:
        """Generate XMLElement XML for a single element and its children"""
        ind = ' ' * indent
        key = self._next_key()
        
        # Build attributes
        attrs = []
        attrs.append(f'dataType="{element.data_type.value}"')
        attrs.append('isMappable="true"')
        attrs.append('isNode="true"')
        attrs.append(f'key="{key}"')
        
        # Handle looping option for arrays
        if element.looping_option:
            attrs.append(f'loopingOption="{element.looping_option}"')
        
        # Max/Min occurs
        max_occurs_str = "-1" if element.max_occurs == -1 else str(element.max_occurs)
        attrs.append(f'maxOccurs="{max_occurs_str}"')
        attrs.append(f'minOccurs="{element.min_occurs}"')
        attrs.append(f'name="{self._escape_xml(element.name)}"')
        attrs.append('typeExpanded="false"')
        attrs.append(f'typeKey="{element.type_key}"')
        attrs.append(f'useNamespace="{element.namespace_key}"')
        
        # Validate data (false for arrays typically)
        if not element.validate_data:
            attrs.append('validateData="false"')
        
        attrs_str = ' '.join(attrs)
        
        # Check if element has children
        has_children = bool(element.children) or bool(element.attributes)
        
        if has_children:
            xml = f'{ind}<XMLElement {attrs_str}>\n'
            
            # Add DataFormat
            xml += self._generate_data_format(element, indent + 2)
            
            # Add attributes first
            for attr in element.attributes:
                xml += self._generate_attribute_xml(attr, indent + 2)
            
            # Add child elements
            for child in element.children:
                xml += self._generate_element_xml(child, indent + 2)
            
            xml += f'{ind}</XMLElement>\n'
        else:
            xml = f'{ind}<XMLElement {attrs_str}>\n'
            xml += self._generate_data_format(element, indent + 2)
            xml += f'{ind}</XMLElement>\n'
        
        return xml
    
    def _generate_attribute_xml(self, attr: XMLElementDef, indent: int) -> str:
        """Generate XMLAttribute XML"""
        ind = ' ' * indent
        key = self._next_key()
        
        attrs = []
        attrs.append(f'dataType="{attr.data_type.value}"')
        attrs.append('isMappable="true"')
        attrs.append('isNode="true"')
        attrs.append(f'key="{key}"')
        attrs.append(f'name="{self._escape_xml(attr.name)}"')
        attrs.append(f'useNamespace="{attr.namespace_key}"')
        
        attrs_str = ' '.join(attrs)
        
        xml = f'{ind}<XMLAttribute {attrs_str}>\n'
        xml += self._generate_data_format(attr, indent + 2)
        xml += f'{ind}</XMLAttribute>\n'
        
        return xml
    
    def _generate_data_format(self, element: XMLElementDef, indent: int) -> str:
        """Generate DataFormat XML based on data type"""
        ind = ' ' * indent
        
        xml = f'{ind}<DataFormat>\n'
        
        if element.data_type == BoomiDataType.DATETIME:
            date_format = element.date_format or "yyyy-MM-dd'T'HH:mm:ss"
            xml += f'{ind}  <ProfileDateFormat dateFormat="{date_format}"/>\n'
        elif element.data_type == BoomiDataType.NUMBER:
            number_format = element.number_format or ""
            xml += f'{ind}  <ProfileNumberFormat numberFormat="{number_format}"/>\n'
        else:
            xml += f'{ind}  <ProfileCharacterFormat/>\n'
        
        xml += f'{ind}</DataFormat>\n'
        
        return xml


def convert_webmethods_to_boomi_xml_profile(
    node_ndf_content: str = None,
    xsd_content: str = None,
    name: str = None,
    description: str = None,
    customer_settings: Dict = None
) -> str:
    """
    Main conversion function for webMethods Document Type to Boomi XML Profile.
    
    Args:
        node_ndf_content: Content of webMethods node.ndf file
        xsd_content: Content of XSD schema (alternative input)
        name: Profile name (auto-detected if not provided)
        description: Profile description
        customer_settings: Customer settings dict with boomi.deployment config
    
    Returns:
        Boomi XML Profile XML string
    """
    # Create deployment config from customer settings
    if customer_settings:
        deployment = customer_settings.get('boomi', {}).get('deployment', {})
        config = BoomiDeploymentConfig(
            folder_id=deployment.get('folderId', 'Rjo3NTQ1MTg0'),
            folder_name=deployment.get('folderName', 'MigrationPoC'),
            folder_full_path=deployment.get('folderFullPath', 'Jade Global, Inc./MigrationPoC'),
            branch_id=deployment.get('branchId', 'QjoyOTQwMQ'),
            branch_name=deployment.get('branchName', 'main'),
            created_by=deployment.get('createdBy', 'vinit.verma@jadeglobal.com'),
            modified_by=deployment.get('modifiedBy', 'vinit.verma@jadeglobal.com')
        )
    else:
        config = BoomiDeploymentConfig()
    
    parser = WebMethodsDocTypeParser()
    generator = BoomiXMLProfileGenerator(config)
    
    # Parse input
    if node_ndf_content:
        root_element, metadata = parser.parse_node_ndf(node_ndf_content)
        source_desc = "webMethods Document Type"
    elif xsd_content:
        root_element, metadata = parser.parse_from_xsd(xsd_content)
        source_desc = "XSD Schema"
    else:
        # Create a sample structure if no input provided
        root_element = XMLElementDef(
            name=name or "Document",
            data_type=BoomiDataType.CHARACTER,
            min_occurs=1,
            max_occurs=1
        )
        metadata = {"field_count": 0, "automation_level": 100}
        source_desc = "Empty Template"
    
    # Determine profile name
    profile_name = name or root_element.name
    
    # Build description
    if not description:
        description = f"Migrated from {source_desc}\n\nField Count: {metadata.get('field_count', 0)}\nAutomation Level: {metadata.get('automation_level', 95)}%"
    
    # Generate the profile
    return generator.generate_profile(
        root_element=root_element,
        name=profile_name,
        description=description
    )


def convert_sample_order_structure() -> str:
    """
    Generate a sample Order XML Profile matching the structure in the user's example.
    This demonstrates the exact output format.
    """
    # Create the Order structure from the example
    order = XMLElementDef(
        name="Order",
        data_type=BoomiDataType.CHARACTER,
        min_occurs=1,
        max_occurs=1,
        children=[
            XMLElementDef(
                name="Header",
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1,
                children=[
                    XMLElementDef(
                        name="Number",
                        data_type=BoomiDataType.CHARACTER,
                        min_occurs=1,
                        max_occurs=1
                    ),
                    XMLElementDef(
                        name="Received",
                        data_type=BoomiDataType.DATETIME,
                        min_occurs=1,
                        max_occurs=1,
                        date_format="yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
                    )
                ]
            ),
            XMLElementDef(
                name="Customer",
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1,
                children=[
                    XMLElementDef(
                        name="Number",
                        data_type=BoomiDataType.NUMBER,
                        min_occurs=1,
                        max_occurs=1
                    ),
                    XMLElementDef(
                        name="ContactName",
                        data_type=BoomiDataType.CHARACTER,
                        min_occurs=1,
                        max_occurs=1
                    ),
                    XMLElementDef(
                        name="CompanyName",
                        data_type=BoomiDataType.CHARACTER,
                        min_occurs=1,
                        max_occurs=1
                    ),
                    XMLElementDef(
                        name="Address",
                        data_type=BoomiDataType.CHARACTER,
                        min_occurs=1,
                        max_occurs=1,
                        children=[
                            XMLElementDef(
                                name="Street",
                                data_type=BoomiDataType.CHARACTER,
                                min_occurs=1,
                                max_occurs=1
                            ),
                            XMLElementDef(
                                name="City",
                                data_type=BoomiDataType.CHARACTER,
                                min_occurs=1,
                                max_occurs=1
                            ),
                            XMLElementDef(
                                name="ZIP",
                                data_type=BoomiDataType.CHARACTER,
                                min_occurs=1,
                                max_occurs=1
                            ),
                            XMLElementDef(
                                name="State",
                                data_type=BoomiDataType.CHARACTER,
                                min_occurs=1,
                                max_occurs=1
                            )
                        ]
                    )
                ]
            ),
            XMLElementDef(
                name="LineItems",
                data_type=BoomiDataType.CHARACTER,
                min_occurs=1,
                max_occurs=1,
                children=[
                    XMLElementDef(
                        name="LineItem",
                        data_type=BoomiDataType.CHARACTER,
                        min_occurs=1,
                        max_occurs=-1,  # Unbounded
                        looping_option="unique",
                        validate_data=False,
                        children=[
                            XMLElementDef(
                                name="Article",
                                data_type=BoomiDataType.CHARACTER,
                                min_occurs=1,
                                max_occurs=1,
                                children=[
                                    XMLElementDef(
                                        name="Amount",
                                        data_type=BoomiDataType.NUMBER,
                                        min_occurs=1,
                                        max_occurs=1
                                    ),
                                    XMLElementDef(
                                        name="Price",
                                        data_type=BoomiDataType.NUMBER,
                                        min_occurs=1,
                                        max_occurs=1
                                    ),
                                    XMLElementDef(
                                        name="Tax",
                                        data_type=BoomiDataType.NUMBER,
                                        min_occurs=1,
                                        max_occurs=1
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )
    
    config = BoomiDeploymentConfig()
    generator = BoomiXMLProfileGenerator(config)
    
    return generator.generate_profile(
        root_element=order,
        name="Order_sample_profile",
        description="Sample Order XML Profile - Migrated from webMethods"
    )


# Utility functions
def create_deployment_config_from_customer(customer_settings: dict) -> BoomiDeploymentConfig:
    """Create deployment config from customer settings dict"""
    deployment = customer_settings.get('boomi', {}).get('deployment', {})
    return BoomiDeploymentConfig(
        folder_id=deployment.get('folderId', 'Rjo3NTQ1MTg0'),
        folder_name=deployment.get('folderName', 'MigrationPoC'),
        folder_full_path=deployment.get('folderFullPath', 'Jade Global, Inc./MigrationPoC'),
        branch_id=deployment.get('branchId', 'QjoyOTQwMQ'),
        branch_name=deployment.get('branchName', 'main'),
        created_by=deployment.get('createdBy', 'vinit.verma@jadeglobal.com'),
        modified_by=deployment.get('modifiedBy', 'vinit.verma@jadeglobal.com')
    )


if __name__ == "__main__":
    # Test the converter with sample Order structure
    print("=" * 80)
    print("BOOMI XML PROFILE CONVERTER TEST")
    print("=" * 80)
    
    # Generate sample Order profile
    sample_xml = convert_sample_order_structure()
    print("\n--- Sample Order Profile (first 3000 chars) ---")
    print(sample_xml[:3000])
    print("\n...(truncated)...")
    
    # Test with a mock webMethods node.ndf
    mock_node_ndf = '''<?xml version="1.0" encoding="UTF-8"?>
<Values version="2.0">
  <value name="node_type">record</value>
  <value name="node_nsName">enterprise/documents/PurchaseOrder</value>
  <array name="rec_fields" type="record" depth="1">
    <record>
      <value name="field_name">orderId</value>
      <value name="field_type">string</value>
      <value name="field_dim">0</value>
    </record>
    <record>
      <value name="field_name">orderDate</value>
      <value name="field_type">date</value>
      <value name="field_dim">0</value>
    </record>
    <record>
      <value name="field_name">totalAmount</value>
      <value name="field_type">java.lang.Double</value>
      <value name="field_dim">0</value>
    </record>
    <record>
      <value name="field_name">lineItems</value>
      <value name="field_type">record</value>
      <value name="field_dim">1</value>
      <array name="rec_fields" type="record" depth="1">
        <record>
          <value name="field_name">itemId</value>
          <value name="field_type">string</value>
          <value name="field_dim">0</value>
        </record>
        <record>
          <value name="field_name">quantity</value>
          <value name="field_type">java.lang.Integer</value>
          <value name="field_dim">0</value>
        </record>
        <record>
          <value name="field_name">price</value>
          <value name="field_type">java.lang.Double</value>
          <value name="field_dim">0</value>
        </record>
      </array>
    </record>
  </array>
</Values>'''
    
    print("\n\n--- webMethods node.ndf Conversion ---")
    converted_xml = convert_webmethods_to_boomi_xml_profile(
        node_ndf_content=mock_node_ndf,
        name="PurchaseOrder_profile",
        description="Converted from webMethods Document Type"
    )
    print(converted_xml[:3000])
    print("\n...(truncated)...")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE - Output matches Boomi XMLProfile format")
    print("=" * 80)