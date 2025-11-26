"""
Enterprise Conversion Engine - Part 1
Boomi XML Generator

Generates valid Boomi Platform API XML for:
- Profiles (XML, JSON, EDI, Flat File)
- Processes
- Maps
- Connectors
"""

import uuid
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from lxml import etree
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# BOOMI COMPONENT TYPES
# =============================================================================

class BoomiComponentType(str, Enum):
    """Boomi component types"""
    PROCESS = "process"
    PROFILE_XML = "profile.xml"
    PROFILE_JSON = "profile.json"
    PROFILE_EDI = "profile.edi"
    PROFILE_FLATFILE = "profile.flatfile"
    PROFILE_DATABASE = "profile.database"
    MAP = "map"
    CONNECTOR = "connector"
    CONNECTION = "connection"
    OPERATION = "operation"


class BoomiShapeType(str, Enum):
    """Boomi process shapes"""
    START = "start"
    STOP = "stop"
    MAP = "map"
    DECISION = "decision"
    BRANCH = "branch"
    ROUTE = "route"
    DATA_PROCESS = "dataprocess"
    MESSAGE = "message"
    FLOW_CONTROL = "flowcontrol"
    TRY_CATCH = "trycatch"
    EXCEPTION = "exception"
    NOTIFY = "notify"
    SET_PROPERTIES = "setproperties"
    CONNECTOR = "connector"
    DATABASE_CONNECTOR = "database"
    HTTP_CONNECTOR = "http"
    FTP_CONNECTOR = "ftp"
    JMS_CONNECTOR = "jms"
    PROCESS_CALL = "processcall"
    RETURN = "return"
    PROGRAM_COMMAND = "programcommand"
    CLEANSE = "cleanse"
    CROSS_REFERENCE = "crossreference"
    TRADING_PARTNER = "tradingpartner"


# =============================================================================
# BOOMI XML NAMESPACE AND SCHEMAS
# =============================================================================

BOOMI_NS = "http://api.platform.boomi.com/"
BOOMI_NSMAP = {
    'bns': BOOMI_NS,
    None: BOOMI_NS
}

# XSD namespace for profiles
XSD_NS = "http://www.w3.org/2001/XMLSchema"


# =============================================================================
# XML BUILDERS
# =============================================================================

class BoomiXMLBuilder:
    """
    Builds valid Boomi Platform API XML components.
    
    Reference: Boomi Platform API documentation
    """
    
    def __init__(self):
        self.component_id = None
    
    def _create_component_root(self, component_type: str, name: str, 
                               description: str = "") -> etree._Element:
        """Create root Component element"""
        # Generate new component ID
        self.component_id = str(uuid.uuid4())
        
        root = etree.Element(
            f"{{{BOOMI_NS}}}Component",
            nsmap={'bns': BOOMI_NS}
        )
        
        # Add standard elements
        etree.SubElement(root, f"{{{BOOMI_NS}}}name").text = name
        etree.SubElement(root, f"{{{BOOMI_NS}}}type").text = component_type
        if description:
            etree.SubElement(root, f"{{{BOOMI_NS}}}description").text = description
        
        return root
    
    def _add_object_element(self, parent: etree._Element) -> etree._Element:
        """Add object element that contains component-specific XML"""
        return etree.SubElement(parent, f"{{{BOOMI_NS}}}object")
    
    def to_string(self, root: etree._Element, pretty: bool = True) -> str:
        """Convert element tree to string"""
        return etree.tostring(
            root, 
            pretty_print=pretty, 
            xml_declaration=True, 
            encoding='UTF-8'
        ).decode('utf-8')


# =============================================================================
# PROFILE GENERATOR
# =============================================================================

class ProfileGenerator(BoomiXMLBuilder):
    """Generates Boomi Profile XML"""
    
    def generate_xml_profile(self, name: str, fields: List[Dict], 
                            root_element: str = "Root",
                            description: str = "") -> str:
        """
        Generate XML Profile component.
        
        Args:
            name: Profile name
            fields: List of field definitions with keys:
                   - name: field name
                   - type: data type (string, integer, date, etc.)
                   - is_array: boolean
                   - children: nested fields
            root_element: Root XML element name
            description: Profile description
        """
        root = self._create_component_root(
            BoomiComponentType.PROFILE_XML.value,
            name,
            description or f"XML Profile: {name}"
        )
        
        obj = self._add_object_element(root)
        
        # Create ProfileXML element
        profile = etree.SubElement(obj, "ProfileXML")
        
        # Add XSD schema
        schema = etree.SubElement(
            profile, 
            f"{{{XSD_NS}}}schema",
            nsmap={'xsd': XSD_NS}
        )
        schema.set("elementFormDefault", "qualified")
        
        # Create root element definition
        root_elem = etree.SubElement(schema, f"{{{XSD_NS}}}element")
        root_elem.set("name", root_element)
        
        # Create complex type for root
        complex_type = etree.SubElement(root_elem, f"{{{XSD_NS}}}complexType")
        sequence = etree.SubElement(complex_type, f"{{{XSD_NS}}}sequence")
        
        # Add fields
        self._add_xsd_fields(sequence, fields, schema)
        
        return self.to_string(root)
    
    def _add_xsd_fields(self, parent: etree._Element, fields: List[Dict],
                       schema: etree._Element, prefix: str = ""):
        """Add XSD field definitions"""
        for field_def in fields:
            name = field_def.get('name', '')
            if not name:
                continue
            
            field_type = field_def.get('type', 'string')
            is_array = field_def.get('is_array', False)
            children = field_def.get('children', [])
            
            elem = etree.SubElement(parent, f"{{{XSD_NS}}}element")
            elem.set("name", name)
            
            # Handle array cardinality
            if is_array:
                elem.set("minOccurs", "0")
                elem.set("maxOccurs", "unbounded")
            else:
                elem.set("minOccurs", field_def.get('min_occurs', '0'))
                max_occurs = field_def.get('max_occurs', '1')
                if max_occurs == -1:
                    max_occurs = 'unbounded'
                elem.set("maxOccurs", str(max_occurs))
            
            # Handle nested structure vs simple type
            if children:
                # Complex type with children
                complex_type = etree.SubElement(elem, f"{{{XSD_NS}}}complexType")
                sequence = etree.SubElement(complex_type, f"{{{XSD_NS}}}sequence")
                self._add_xsd_fields(sequence, children, schema, f"{prefix}{name}/")
            else:
                # Simple type
                xsd_type = self._map_type_to_xsd(field_type)
                elem.set("type", xsd_type)
    
    def _map_type_to_xsd(self, wm_type: str) -> str:
        """Map webMethods type to XSD type"""
        type_map = {
            'string': 'xsd:string',
            'integer': 'xsd:integer',
            'int': 'xsd:int',
            'long': 'xsd:long',
            'float': 'xsd:float',
            'double': 'xsd:double',
            'decimal': 'xsd:decimal',
            'boolean': 'xsd:boolean',
            'date': 'xsd:date',
            'datetime': 'xsd:dateTime',
            'time': 'xsd:time',
            'binary': 'xsd:base64Binary',
            'object': 'xsd:anyType',
        }
        return type_map.get(wm_type.lower(), 'xsd:string')
    
    def generate_json_profile(self, name: str, fields: List[Dict],
                             description: str = "") -> str:
        """Generate JSON Profile component"""
        root = self._create_component_root(
            BoomiComponentType.PROFILE_JSON.value,
            name,
            description or f"JSON Profile: {name}"
        )
        
        obj = self._add_object_element(root)
        
        # Create ProfileJSON element
        profile = etree.SubElement(obj, "ProfileJSON")
        
        # JSON schema
        json_schema = etree.SubElement(profile, "JSONSchema")
        json_schema.text = self._generate_json_schema(fields)
        
        return self.to_string(root)
    
    def _generate_json_schema(self, fields: List[Dict]) -> str:
        """Generate JSON Schema string"""
        import json
        
        def field_to_schema(field_def: Dict) -> Dict:
            name = field_def.get('name', '')
            field_type = field_def.get('type', 'string')
            is_array = field_def.get('is_array', False)
            children = field_def.get('children', [])
            
            if children:
                # Object with properties
                props = {}
                for child in children:
                    props[child.get('name', '')] = field_to_schema(child)
                
                schema = {"type": "object", "properties": props}
            else:
                # Simple type
                json_type = {
                    'string': 'string',
                    'integer': 'integer',
                    'int': 'integer',
                    'long': 'integer',
                    'float': 'number',
                    'double': 'number',
                    'boolean': 'boolean',
                    'date': 'string',
                    'datetime': 'string',
                }.get(field_type.lower(), 'string')
                
                schema = {"type": json_type}
            
            if is_array:
                schema = {"type": "array", "items": schema}
            
            return schema
        
        root_schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {}
        }
        
        for field_def in fields:
            name = field_def.get('name', '')
            if name:
                root_schema["properties"][name] = field_to_schema(field_def)
        
        return json.dumps(root_schema, indent=2)
    
    def generate_flatfile_profile(self, name: str, fields: List[Dict],
                                  delimiter: str = ",",
                                  description: str = "") -> str:
        """Generate Flat File Profile component"""
        root = self._create_component_root(
            BoomiComponentType.PROFILE_FLATFILE.value,
            name,
            description or f"Flat File Profile: {name}"
        )
        
        obj = self._add_object_element(root)
        
        # Create ProfileFlatFile element
        profile = etree.SubElement(obj, "ProfileFlatFile")
        
        # File format
        file_format = etree.SubElement(profile, "FileFormat")
        etree.SubElement(file_format, "Delimiter").text = delimiter
        etree.SubElement(file_format, "TextQualifier").text = '"'
        etree.SubElement(file_format, "EscapeCharacter").text = '\\'
        
        # Record definition
        record = etree.SubElement(profile, "Record")
        etree.SubElement(record, "Name").text = "Record"
        
        # Fields
        for i, field_def in enumerate(fields):
            field_elem = etree.SubElement(record, "Field")
            etree.SubElement(field_elem, "Name").text = field_def.get('name', f'Field{i}')
            etree.SubElement(field_elem, "DataType").text = self._map_type_to_flatfile(
                field_def.get('type', 'string')
            )
            etree.SubElement(field_elem, "Position").text = str(i + 1)
        
        return self.to_string(root)
    
    def _map_type_to_flatfile(self, wm_type: str) -> str:
        """Map type to Flat File data type"""
        type_map = {
            'string': 'Character',
            'integer': 'Number',
            'int': 'Number',
            'long': 'Number',
            'float': 'Number',
            'double': 'Number',
            'date': 'Date/Time',
            'datetime': 'Date/Time',
            'boolean': 'Character',
        }
        return type_map.get(wm_type.lower(), 'Character')
    
    def generate_edi_profile(self, name: str, transaction_set: str,
                            version: str = "005010",
                            description: str = "") -> str:
        """Generate EDI Profile component"""
        root = self._create_component_root(
            BoomiComponentType.PROFILE_EDI.value,
            name,
            description or f"EDI Profile: {transaction_set}"
        )
        
        obj = self._add_object_element(root)
        
        # Create ProfileEDI element
        profile = etree.SubElement(obj, "ProfileEDI")
        
        # Standard info
        etree.SubElement(profile, "Standard").text = "X12"
        etree.SubElement(profile, "Version").text = version
        etree.SubElement(profile, "TransactionSet").text = transaction_set
        
        # Note: Full EDI profiles are typically imported from standard templates
        # This creates a basic structure
        
        return self.to_string(root)


# =============================================================================
# PROCESS GENERATOR
# =============================================================================

@dataclass
class ProcessShape:
    """Represents a shape in a Boomi process"""
    id: str
    type: BoomiShapeType
    name: str
    x: int = 0
    y: int = 0
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessConnection:
    """Connection between shapes"""
    from_shape: str
    to_shape: str
    label: str = ""


class ProcessGenerator(BoomiXMLBuilder):
    """Generates Boomi Process XML"""
    
    def __init__(self):
        super().__init__()
        self.shapes: List[ProcessShape] = []
        self.connections: List[ProcessConnection] = []
        self.shape_counter = 0
        self.current_x = 100
        self.current_y = 100
    
    def new_shape(self, shape_type: BoomiShapeType, name: str, 
                  config: Dict = None) -> ProcessShape:
        """Create a new shape"""
        self.shape_counter += 1
        shape_id = f"shape_{self.shape_counter}"
        
        shape = ProcessShape(
            id=shape_id,
            type=shape_type,
            name=name,
            x=self.current_x,
            y=self.current_y,
            configuration=config or {}
        )
        
        self.shapes.append(shape)
        
        # Move position for next shape
        self.current_x += 150
        if self.current_x > 800:
            self.current_x = 100
            self.current_y += 100
        
        return shape
    
    def connect(self, from_shape: ProcessShape, to_shape: ProcessShape,
                label: str = ""):
        """Connect two shapes"""
        self.connections.append(ProcessConnection(
            from_shape=from_shape.id,
            to_shape=to_shape.id,
            label=label
        ))
    
    def generate_process(self, name: str, description: str = "") -> str:
        """Generate complete process XML"""
        root = self._create_component_root(
            BoomiComponentType.PROCESS.value,
            name,
            description or f"Process: {name}"
        )
        
        obj = self._add_object_element(root)
        
        # Create Process element
        process = etree.SubElement(obj, "Process")
        process.set("processId", self.component_id)
        
        # Add shapes
        shapes_elem = etree.SubElement(process, "Shapes")
        for shape in self.shapes:
            self._add_shape(shapes_elem, shape)
        
        # Add connections
        conns_elem = etree.SubElement(process, "Connectors")
        for conn in self.connections:
            self._add_connection(conns_elem, conn)
        
        return self.to_string(root)
    
    def _add_shape(self, parent: etree._Element, shape: ProcessShape):
        """Add shape XML"""
        shape_elem = etree.SubElement(parent, "Shape")
        shape_elem.set("id", shape.id)
        shape_elem.set("type", shape.type.value)
        
        # Position
        pos = etree.SubElement(shape_elem, "Position")
        pos.set("x", str(shape.x))
        pos.set("y", str(shape.y))
        
        # Name/Label
        etree.SubElement(shape_elem, "Name").text = shape.name
        
        # Shape-specific configuration
        if shape.type == BoomiShapeType.MAP:
            self._add_map_config(shape_elem, shape.configuration)
        elif shape.type == BoomiShapeType.DECISION:
            self._add_decision_config(shape_elem, shape.configuration)
        elif shape.type == BoomiShapeType.DATA_PROCESS:
            self._add_data_process_config(shape_elem, shape.configuration)
        elif shape.type == BoomiShapeType.CONNECTOR:
            self._add_connector_config(shape_elem, shape.configuration)
        elif shape.type == BoomiShapeType.SET_PROPERTIES:
            self._add_set_properties_config(shape_elem, shape.configuration)
        elif shape.type == BoomiShapeType.FLOW_CONTROL:
            self._add_flow_control_config(shape_elem, shape.configuration)
    
    def _add_map_config(self, shape_elem: etree._Element, config: Dict):
        """Add Map shape configuration"""
        map_config = etree.SubElement(shape_elem, "MapConfiguration")
        
        # Profile references
        if 'source_profile' in config:
            etree.SubElement(map_config, "SourceProfile").text = config['source_profile']
        if 'target_profile' in config:
            etree.SubElement(map_config, "TargetProfile").text = config['target_profile']
        
        # Field mappings
        if 'mappings' in config:
            mappings = etree.SubElement(map_config, "Mappings")
            for mapping in config['mappings']:
                map_elem = etree.SubElement(mappings, "Mapping")
                etree.SubElement(map_elem, "Source").text = mapping.get('source', '')
                etree.SubElement(map_elem, "Target").text = mapping.get('target', '')
                if 'function' in mapping:
                    func = etree.SubElement(map_elem, "Function")
                    func.set("name", mapping['function'])
    
    def _add_decision_config(self, shape_elem: etree._Element, config: Dict):
        """Add Decision shape configuration"""
        decision = etree.SubElement(shape_elem, "DecisionConfiguration")
        
        # Condition
        if 'property' in config:
            etree.SubElement(decision, "Property").text = config['property']
        
        # Routes
        if 'routes' in config:
            routes = etree.SubElement(decision, "Routes")
            for route in config['routes']:
                route_elem = etree.SubElement(routes, "Route")
                etree.SubElement(route_elem, "Value").text = route.get('value', '')
                etree.SubElement(route_elem, "Label").text = route.get('label', '')
    
    def _add_data_process_config(self, shape_elem: etree._Element, config: Dict):
        """Add Data Process shape configuration"""
        dp = etree.SubElement(shape_elem, "DataProcessConfiguration")
        
        etree.SubElement(dp, "ProcessingType").text = config.get('type', 'Custom Scripting')
        
        if 'script' in config:
            script = etree.SubElement(dp, "Script")
            script.text = config['script']
    
    def _add_connector_config(self, shape_elem: etree._Element, config: Dict):
        """Add Connector shape configuration"""
        conn = etree.SubElement(shape_elem, "ConnectorConfiguration")
        
        etree.SubElement(conn, "ConnectorType").text = config.get('connector_type', 'HTTP')
        
        if 'connection_id' in config:
            etree.SubElement(conn, "ConnectionId").text = config['connection_id']
        if 'operation_id' in config:
            etree.SubElement(conn, "OperationId").text = config['operation_id']
    
    def _add_set_properties_config(self, shape_elem: etree._Element, config: Dict):
        """Add Set Properties configuration"""
        props = etree.SubElement(shape_elem, "SetPropertiesConfiguration")
        
        if 'properties' in config:
            for prop in config['properties']:
                prop_elem = etree.SubElement(props, "Property")
                etree.SubElement(prop_elem, "Name").text = prop.get('name', '')
                etree.SubElement(prop_elem, "Value").text = prop.get('value', '')
                etree.SubElement(prop_elem, "Type").text = prop.get('type', 'Document')
    
    def _add_flow_control_config(self, shape_elem: etree._Element, config: Dict):
        """Add Flow Control configuration"""
        fc = etree.SubElement(shape_elem, "FlowControlConfiguration")
        
        etree.SubElement(fc, "Type").text = config.get('flow_type', 'For Each Document')
    
    def _add_connection(self, parent: etree._Element, conn: ProcessConnection):
        """Add connection XML"""
        conn_elem = etree.SubElement(parent, "Connector")
        conn_elem.set("from", conn.from_shape)
        conn_elem.set("to", conn.to_shape)
        if conn.label:
            conn_elem.set("label", conn.label)


# =============================================================================
# MAP GENERATOR
# =============================================================================

class MapGenerator(BoomiXMLBuilder):
    """Generates Boomi Map component XML"""
    
    def generate_map(self, name: str, 
                     source_profile: str,
                     target_profile: str,
                     field_mappings: List[Dict],
                     description: str = "") -> str:
        """
        Generate Map component.
        
        Args:
            name: Map name
            source_profile: Source profile component ID
            target_profile: Target profile component ID
            field_mappings: List of mappings with keys:
                          - source: source field path
                          - target: target field path
                          - function: optional transformation function
        """
        root = self._create_component_root(
            BoomiComponentType.MAP.value,
            name,
            description or f"Map: {name}"
        )
        
        obj = self._add_object_element(root)
        
        # Create Map element
        map_elem = etree.SubElement(obj, "Map")
        
        # Source and target profiles
        etree.SubElement(map_elem, "SourceProfile").text = source_profile
        etree.SubElement(map_elem, "TargetProfile").text = target_profile
        
        # Mappings
        mappings = etree.SubElement(map_elem, "Mappings")
        
        for mapping in field_mappings:
            map_entry = etree.SubElement(mappings, "Mapping")
            
            # Source field
            source = etree.SubElement(map_entry, "SourceField")
            source.set("path", mapping.get('source', ''))
            
            # Target field
            target = etree.SubElement(map_entry, "TargetField")
            target.set("path", mapping.get('target', ''))
            
            # Optional function
            if 'function' in mapping:
                func = etree.SubElement(map_entry, "Function")
                func.set("name", mapping['function'])
                
                # Function parameters
                if 'parameters' in mapping:
                    for param_name, param_value in mapping['parameters'].items():
                        param = etree.SubElement(func, "Parameter")
                        param.set("name", param_name)
                        param.text = str(param_value)
        
        return self.to_string(root)


# =============================================================================
# CONNECTOR GENERATOR
# =============================================================================

class ConnectorGenerator(BoomiXMLBuilder):
    """Generates Boomi Connector/Connection/Operation XML"""
    
    def generate_database_connection(self, name: str, 
                                     connection_string: str,
                                     driver_type: str = "mysql",
                                     description: str = "") -> str:
        """Generate Database Connection component"""
        root = self._create_component_root(
            BoomiComponentType.CONNECTION.value,
            name,
            description or f"Database Connection: {name}"
        )
        
        obj = self._add_object_element(root)
        
        conn = etree.SubElement(obj, "Connection")
        conn.set("type", "database")
        
        etree.SubElement(conn, "DriverType").text = driver_type
        etree.SubElement(conn, "ConnectionString").text = connection_string
        
        # Credentials would be added via Boomi connection management
        etree.SubElement(conn, "User").text = "${db.user}"
        etree.SubElement(conn, "Password").text = "${db.password}"
        
        return self.to_string(root)
    
    def generate_http_connection(self, name: str,
                                 base_url: str,
                                 auth_type: str = "None",
                                 description: str = "") -> str:
        """Generate HTTP Connection component"""
        root = self._create_component_root(
            BoomiComponentType.CONNECTION.value,
            name,
            description or f"HTTP Connection: {name}"
        )
        
        obj = self._add_object_element(root)
        
        conn = etree.SubElement(obj, "Connection")
        conn.set("type", "http")
        
        etree.SubElement(conn, "BaseURL").text = base_url
        etree.SubElement(conn, "AuthenticationType").text = auth_type
        
        return self.to_string(root)
    
    def generate_ftp_connection(self, name: str,
                                host: str,
                                port: int = 21,
                                description: str = "") -> str:
        """Generate FTP Connection component"""
        root = self._create_component_root(
            BoomiComponentType.CONNECTION.value,
            name,
            description or f"FTP Connection: {name}"
        )
        
        obj = self._add_object_element(root)
        
        conn = etree.SubElement(obj, "Connection")
        conn.set("type", "ftp")
        
        etree.SubElement(conn, "Host").text = host
        etree.SubElement(conn, "Port").text = str(port)
        etree.SubElement(conn, "User").text = "${ftp.user}"
        etree.SubElement(conn, "Password").text = "${ftp.password}"
        
        return self.to_string(root)
    
    def generate_database_operation(self, name: str,
                                   connection_id: str,
                                   operation_type: str,  # Query, Create, Update, Delete
                                   sql: str = "",
                                   description: str = "") -> str:
        """Generate Database Operation component"""
        root = self._create_component_root(
            BoomiComponentType.OPERATION.value,
            name,
            description or f"Database {operation_type}: {name}"
        )
        
        obj = self._add_object_element(root)
        
        op = etree.SubElement(obj, "Operation")
        op.set("type", "database")
        op.set("connectionId", connection_id)
        
        etree.SubElement(op, "OperationType").text = operation_type
        
        if sql:
            etree.SubElement(op, "SQL").text = sql
        
        return self.to_string(root)
    
    def generate_database_connector(self, name: str, 
                                   operation_type: str,
                                   sql: str,
                                   config: Dict[str, Any]) -> str:
        """
        Generate complete Database connector XML for orchestrator.
        
        Args:
            name: Connector name
            operation_type: query, insert, update, delete
            sql: SQL statement
            config: Configuration from JDBC analyzer
        """
        root = self._create_component_root(
            BoomiComponentType.CONNECTOR.value,
            name,
            f"Database Connector: {name} ({operation_type})"
        )
        
        obj = self._add_object_element(root)
        
        connector = etree.SubElement(obj, "Connector")
        connector.set("type", "database")
        connector.set("componentId", str(uuid.uuid4()))
        
        # Operation
        etree.SubElement(connector, "Operation").text = operation_type.upper()
        
        # SQL
        sql_elem = etree.SubElement(connector, "SQL")
        sql_elem.text = sql
        
        # Tables info
        if 'tables' in config:
            tables_elem = etree.SubElement(connector, "Tables")
            for table in config['tables']:
                t_elem = etree.SubElement(tables_elem, "Table")
                t_elem.set("name", table.get('name', ''))
                if table.get('alias'):
                    t_elem.set("alias", table['alias'])
        
        # Columns info
        if 'columns' in config:
            cols_elem = etree.SubElement(connector, "Columns")
            for col in config['columns']:
                c_elem = etree.SubElement(cols_elem, "Column")
                c_elem.set("name", col.get('name', ''))
        
        # Add conversion notes as comments
        if 'notes' in config:
            for note in config['notes']:
                connector.append(etree.Comment(f" {note} "))
        
        return self.to_string(root)
    
    def generate_http_connector(self, name: str, config: Dict[str, Any]) -> str:
        """
        Generate HTTP Client connector XML.
        
        Args:
            name: Connector name
            config: HTTP configuration (url, method, headers)
        """
        root = self._create_component_root(
            BoomiComponentType.CONNECTOR.value,
            name,
            f"HTTP Connector: {name}"
        )
        
        obj = self._add_object_element(root)
        
        connector = etree.SubElement(obj, "Connector")
        connector.set("type", "http-client")
        connector.set("componentId", str(uuid.uuid4()))
        
        # URL
        etree.SubElement(connector, "URL").text = config.get('url', '')
        
        # Method
        etree.SubElement(connector, "Method").text = config.get('method', 'GET')
        
        # Headers
        if config.get('headers'):
            headers = etree.SubElement(connector, "Headers")
            for hdr_name, hdr_value in config['headers'].items():
                h = etree.SubElement(headers, "Header")
                h.set("name", hdr_name)
                h.text = hdr_value
        
        # Authentication
        if config.get('auth_type'):
            auth = etree.SubElement(connector, "Authentication")
            auth.set("type", config['auth_type'])
        
        # Content Type
        if config.get('content_type'):
            etree.SubElement(connector, "ContentType").text = config['content_type']
        
        return self.to_string(root)
    
    def generate_ftp_connector(self, name: str, config: Dict[str, Any]) -> str:
        """
        Generate FTP/SFTP connector XML.
        
        Args:
            name: Connector name
            config: FTP configuration (host, port, operation, path)
        """
        is_sftp = config.get('sftp', False) or 'sftp' in name.lower()
        connector_type = "sftp" if is_sftp else "ftp"
        
        root = self._create_component_root(
            BoomiComponentType.CONNECTOR.value,
            name,
            f"{'SFTP' if is_sftp else 'FTP'} Connector: {name}"
        )
        
        obj = self._add_object_element(root)
        
        connector = etree.SubElement(obj, "Connector")
        connector.set("type", connector_type)
        connector.set("componentId", str(uuid.uuid4()))
        
        # Host
        etree.SubElement(connector, "Host").text = config.get('host', '')
        
        # Port
        default_port = 22 if is_sftp else 21
        etree.SubElement(connector, "Port").text = str(config.get('port', default_port))
        
        # Operation
        etree.SubElement(connector, "Operation").text = config.get('operation', 'get').upper()
        
        # Remote path
        if config.get('path'):
            etree.SubElement(connector, "RemotePath").text = config['path']
        
        # File mask
        if config.get('file_mask'):
            etree.SubElement(connector, "FileMask").text = config['file_mask']
        
        # Credentials placeholder
        etree.SubElement(connector, "User").text = "${ftp.user}"
        etree.SubElement(connector, "Password").text = "${ftp.password}"
        
        return self.to_string(root)
    
    def generate_jms_connector(self, name: str, config: Dict[str, Any]) -> str:
        """
        Generate JMS connector XML.
        
        Args:
            name: Connector name
            config: JMS configuration (queue/topic, operation)
        """
        root = self._create_component_root(
            BoomiComponentType.CONNECTOR.value,
            name,
            f"JMS Connector: {name}"
        )
        
        obj = self._add_object_element(root)
        
        connector = etree.SubElement(obj, "Connector")
        connector.set("type", "jms")
        connector.set("componentId", str(uuid.uuid4()))
        
        # Destination (queue or topic)
        dest_type = config.get('destination_type', 'queue')
        etree.SubElement(connector, "DestinationType").text = dest_type.upper()
        
        # Destination name
        dest_name = config.get('queue') or config.get('topic') or config.get('destination', '')
        etree.SubElement(connector, "DestinationName").text = dest_name
        
        # Operation
        operation = config.get('operation', 'send')
        etree.SubElement(connector, "Operation").text = operation.upper()
        
        # Message type
        if config.get('message_type'):
            etree.SubElement(connector, "MessageType").text = config['message_type']
        
        # Connection factory (placeholder)
        etree.SubElement(connector, "ConnectionFactory").text = "${jms.connection.factory}"
        
        return self.to_string(root)


# Export all generators
__all__ = [
    'BoomiComponentType',
    'BoomiShapeType',
    'ProfileGenerator',
    'ProcessGenerator',
    'ProcessShape',
    'MapGenerator',
    'ConnectorGenerator',
]
