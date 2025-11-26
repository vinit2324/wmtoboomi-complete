"""
Complete Boomi Process XML Generator
Generates fully-wired, deployable Boomi process XML with proper shape connections
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

class ShapeType(Enum):
    START = "Start"
    STOP = "Stop"
    CONNECTOR = "Connector"
    MAP = "Map"
    DECISION = "Decision"
    DATA_PROCESS = "DataProcess"
    TRY_CATCH = "TryCatch"
    FOREACH = "ForEach"
    SET_PROPERTIES = "SetProperties"
    NOTIFICATION = "Notification"

@dataclass
class Shape:
    id: str
    type: ShapeType
    label: str
    x: int
    y: int
    config: Dict[str, Any]

@dataclass
class Connection:
    id: str
    from_shape: str
    to_shape: str
    label: Optional[str] = None

class CompleteProcessGenerator:
    """Generates complete, deployable Boomi Process XML"""
    
    def __init__(self):
        self.shapes: List[Shape] = []
        self.connections: List[Connection] = []
        self.x_offset = 50
        self.y_start = 50
        self.y_spacing = 150
        self.current_y = self.y_start
        
    def generate_uuid(self) -> str:
        """Generate Boomi-style UUID"""
        return str(uuid.uuid4())
    
    def add_shape(self, shape_type: ShapeType, label: str, config: Dict = None) -> str:
        """Add a shape and return its ID"""
        shape_id = self.generate_uuid()
        shape = Shape(
            id=shape_id,
            type=shape_type,
            label=label,
            x=self.x_offset,
            y=self.current_y,
            config=config or {}
        )
        self.shapes.append(shape)
        self.current_y += self.y_spacing
        return shape_id
    
    def connect_shapes(self, from_id: str, to_id: str, label: Optional[str] = None):
        """Connect two shapes"""
        connection = Connection(
            id=self.generate_uuid(),
            from_shape=from_id,
            to_shape=to_id,
            label=label
        )
        self.connections.append(connection)
    
    def generate_fetch_transform_send_process(
        self, 
        source_connector_type: str,
        source_config: Dict,
        transform_mappings: List[Dict],
        target_connector_type: str,
        target_config: Dict,
        process_name: str
    ) -> str:
        """Generate complete Fetch-Transform-Send process"""
        
        # Start shape
        start_id = self.add_shape(ShapeType.START, "Start")
        
        # Source connector
        source_id = self.add_shape(
            ShapeType.CONNECTOR,
            f"Get from {source_connector_type}",
            {
                "connectorType": source_connector_type,
                "operation": source_config.get("operation", "GET"),
                **source_config
            }
        )
        self.connect_shapes(start_id, source_id)
        
        # Map shape
        map_id = self.add_shape(
            ShapeType.MAP,
            "Transform Data",
            {
                "mappings": transform_mappings,
                "mapType": "standard"
            }
        )
        self.connect_shapes(source_id, map_id)
        
        # Target connector
        target_id = self.add_shape(
            ShapeType.CONNECTOR,
            f"Send to {target_connector_type}",
            {
                "connectorType": target_connector_type,
                "operation": target_config.get("operation", "POST"),
                **target_config
            }
        )
        self.connect_shapes(map_id, target_id)
        
        # Stop shape
        stop_id = self.add_shape(ShapeType.STOP, "Stop")
        self.connect_shapes(target_id, stop_id)
        
        # Generate XML
        return self._generate_process_xml(process_name)
    
    def generate_database_to_file_process(
        self,
        db_query: str,
        db_connection: Dict,
        file_path: str,
        file_format: str,
        process_name: str
    ) -> str:
        """Generate Database-to-File process"""
        
        start_id = self.add_shape(ShapeType.START, "Start")
        
        # Database connector
        db_id = self.add_shape(
            ShapeType.CONNECTOR,
            "Query Database",
            {
                "connectorType": "Database",
                "operation": "query",
                "sql": db_query,
                "connection": db_connection
            }
        )
        self.connect_shapes(start_id, db_id)
        
        # Optional map if format conversion needed
        if file_format.lower() in ['csv', 'xml', 'json']:
            map_id = self.add_shape(
                ShapeType.MAP,
                f"Format as {file_format.upper()}",
                {
                    "outputFormat": file_format,
                    "autoMap": True
                }
            )
            self.connect_shapes(db_id, map_id)
            prev_id = map_id
        else:
            prev_id = db_id
        
        # File connector
        file_id = self.add_shape(
            ShapeType.CONNECTOR,
            "Write to File",
            {
                "connectorType": "FTP",
                "operation": "PUT",
                "path": file_path,
                "createDirectory": True
            }
        )
        self.connect_shapes(prev_id, file_id)
        
        stop_id = self.add_shape(ShapeType.STOP, "Stop")
        self.connect_shapes(file_id, stop_id)
        
        return self._generate_process_xml(process_name)
    
    def generate_api_to_api_process(
        self,
        source_api: Dict,
        transform_logic: List[Dict],
        target_api: Dict,
        error_handling: bool,
        process_name: str
    ) -> str:
        """Generate API-to-API integration process"""
        
        start_id = self.add_shape(ShapeType.START, "Start")
        
        # Wrap in try-catch if error handling enabled
        if error_handling:
            try_id = self.add_shape(ShapeType.TRY_CATCH, "Try-Catch")
            self.connect_shapes(start_id, try_id)
            parent_id = try_id
        else:
            parent_id = start_id
        
        # Source API call
        source_id = self.add_shape(
            ShapeType.CONNECTOR,
            f"Call {source_api.get('name', 'Source API')}",
            {
                "connectorType": "HTTP",
                "operation": source_api.get("method", "GET"),
                "url": source_api.get("url"),
                "headers": source_api.get("headers", {}),
                "authType": source_api.get("authType", "None")
            }
        )
        self.connect_shapes(parent_id, source_id)
        
        # Transform
        map_id = self.add_shape(
            ShapeType.MAP,
            "Transform Response",
            {
                "mappings": transform_logic,
                "mapType": "standard"
            }
        )
        self.connect_shapes(source_id, map_id)
        
        # Target API call
        target_id = self.add_shape(
            ShapeType.CONNECTOR,
            f"Call {target_api.get('name', 'Target API')}",
            {
                "connectorType": "HTTP",
                "operation": target_api.get("method", "POST"),
                "url": target_api.get("url"),
                "headers": target_api.get("headers", {}),
                "authType": target_api.get("authType", "None")
            }
        )
        self.connect_shapes(map_id, target_id)
        
        stop_id = self.add_shape(ShapeType.STOP, "Stop")
        self.connect_shapes(target_id, stop_id)
        
        if error_handling:
            # Add error branch
            error_notify_id = self.add_shape(
                ShapeType.NOTIFICATION,
                "Send Error Notification",
                {
                    "recipients": ["admin@company.com"],
                    "subject": "Process Error",
                    "includeException": True
                }
            )
            self.connect_shapes(try_id, error_notify_id, label="catch")
            error_stop_id = self.add_shape(ShapeType.STOP, "Stop on Error")
            self.connect_shapes(error_notify_id, error_stop_id)
        
        return self._generate_process_xml(process_name)
    
    def generate_batch_processor_process(
        self,
        source_config: Dict,
        batch_size: int,
        processing_logic: Dict,
        target_config: Dict,
        process_name: str
    ) -> str:
        """Generate batch processing process with ForEach"""
        
        start_id = self.add_shape(ShapeType.START, "Start")
        
        # Get batch
        source_id = self.add_shape(
            ShapeType.CONNECTOR,
            "Get Batch",
            source_config
        )
        self.connect_shapes(start_id, source_id)
        
        # ForEach loop
        foreach_id = self.add_shape(
            ShapeType.FOREACH,
            f"Process Batch (size: {batch_size})",
            {
                "batchSize": batch_size,
                "continueOnError": True
            }
        )
        self.connect_shapes(source_id, foreach_id)
        
        # Process each item
        process_id = self.add_shape(
            ShapeType.DATA_PROCESS,
            "Process Item",
            processing_logic
        )
        self.connect_shapes(foreach_id, process_id)
        
        # Send results
        target_id = self.add_shape(
            ShapeType.CONNECTOR,
            "Send Results",
            target_config
        )
        self.connect_shapes(process_id, target_id)
        
        stop_id = self.add_shape(ShapeType.STOP, "Stop")
        self.connect_shapes(target_id, stop_id)
        
        return self._generate_process_xml(process_name)
    
    def generate_content_router_process(
        self,
        source_config: Dict,
        routing_rules: List[Dict],
        process_name: str
    ) -> str:
        """Generate content-based router process"""
        
        start_id = self.add_shape(ShapeType.START, "Start")
        
        # Get message
        source_id = self.add_shape(
            ShapeType.CONNECTOR,
            "Get Message",
            source_config
        )
        self.connect_shapes(start_id, source_id)
        
        # Decision shape for routing
        decision_id = self.add_shape(
            ShapeType.DECISION,
            "Route Message",
            {
                "decisionType": "XPath",
                "branches": len(routing_rules)
            }
        )
        self.connect_shapes(source_id, decision_id)
        
        # Create branch for each routing rule
        for i, rule in enumerate(routing_rules):
            route_id = self.add_shape(
                ShapeType.CONNECTOR,
                f"Route to {rule.get('destination')}",
                rule.get('connector_config', {})
            )
            self.connect_shapes(
                decision_id, 
                route_id, 
                label=rule.get('condition', f'Branch {i+1}')
            )
            
            stop_id = self.add_shape(ShapeType.STOP, f"Stop {i+1}")
            self.connect_shapes(route_id, stop_id)
        
        return self._generate_process_xml(process_name)
    
    def _generate_process_xml(self, process_name: str) -> str:
        """Generate complete Boomi Process XML"""
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Process xmlns:bns="http://api.platform.boomi.com/" 
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bns:name>{process_name}</bns:name>
    <bns:type>process</bns:type>
    <bns:description>Auto-generated from webMethods by Migration Accelerator</bns:description>
    <bns:processVersion>1.0</bns:processVersion>
    
    <bns:shapes>
'''
        
        # Add all shapes
        for shape in self.shapes:
            xml += self._generate_shape_xml(shape)
        
        xml += '''    </bns:shapes>
    
    <bns:connections>
'''
        
        # Add all connections
        for conn in self.connections:
            xml += self._generate_connection_xml(conn)
        
        xml += '''    </bns:connections>
</bns:Process>'''
        
        return xml
    
    def _generate_shape_xml(self, shape: Shape) -> str:
        """Generate XML for a single shape"""
        
        shape_xml = f'''        <bns:shape>
            <bns:shapeId>{shape.id}</bns:shapeId>
            <bns:type>{shape.type.value}</bns:type>
            <bns:label>{shape.label}</bns:label>
            <bns:x>{shape.x}</bns:x>
            <bns:y>{shape.y}</bns:y>
'''
        
        # Add shape-specific configuration
        if shape.config:
            shape_xml += '            <bns:configuration>\n'
            for key, value in shape.config.items():
                if isinstance(value, dict):
                    shape_xml += f'                <bns:{key}>\n'
                    for k, v in value.items():
                        shape_xml += f'                    <bns:{k}>{self._escape_xml(str(v))}</bns:{k}>\n'
                    shape_xml += f'                </bns:{key}>\n'
                elif isinstance(value, list):
                    shape_xml += f'                <bns:{key}>\n'
                    for item in value:
                        shape_xml += f'                    <bns:item>{self._escape_xml(str(item))}</bns:item>\n'
                    shape_xml += f'                </bns:{key}>\n'
                else:
                    shape_xml += f'                <bns:{key}>{self._escape_xml(str(value))}</bns:{key}>\n'
            shape_xml += '            </bns:configuration>\n'
        
        shape_xml += '        </bns:shape>\n'
        return shape_xml
    
    def _generate_connection_xml(self, conn: Connection) -> str:
        """Generate XML for a connection"""
        
        conn_xml = f'''        <bns:connection>
            <bns:connectionId>{conn.id}</bns:connectionId>
            <bns:fromShapeId>{conn.from_shape}</bns:fromShapeId>
            <bns:toShapeId>{conn.to_shape}</bns:toShapeId>
'''
        if conn.label:
            conn_xml += f'            <bns:label>{self._escape_xml(conn.label)}</bns:label>\n'
        
        conn_xml += '        </bns:connection>\n'
        return conn_xml
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def generate_process_from_flow_analysis(
    flow_analysis: Dict,
    pattern: str,
    service_name: str
) -> str:
    """
    Generate complete Boomi process from flow service analysis
    
    Args:
        flow_analysis: Analysis results from pattern engine
        pattern: Detected pattern type
        service_name: Name of the webMethods flow service
        
    Returns:
        Complete, deployable Boomi Process XML
    """
    
    generator = CompleteProcessGenerator()
    
    if pattern == "fetch_transform_send":
        # Extract configurations from analysis
        adapters = flow_analysis.get('adapters', [])
        source_adapter = adapters[0] if len(adapters) > 0 else {"type": "HTTP"}
        target_adapter = adapters[1] if len(adapters) > 1 else {"type": "HTTP"}
        
        return generator.generate_fetch_transform_send_process(
            source_connector_type=source_adapter.get('type', 'HTTP'),
            source_config=source_adapter.get('config', {}),
            transform_mappings=flow_analysis.get('mappings', []),
            target_connector_type=target_adapter.get('type', 'HTTP'),
            target_config=target_adapter.get('config', {}),
            process_name=service_name
        )
    
    elif pattern == "database_to_file":
        return generator.generate_database_to_file_process(
            db_query=flow_analysis.get('sql_query', 'SELECT * FROM table'),
            db_connection=flow_analysis.get('db_connection', {}),
            file_path=flow_analysis.get('file_path', '/output/data.csv'),
            file_format=flow_analysis.get('file_format', 'CSV'),
            process_name=service_name
        )
    
    elif pattern == "api_to_api":
        return generator.generate_api_to_api_process(
            source_api=flow_analysis.get('source_api', {}),
            transform_logic=flow_analysis.get('transform_logic', []),
            target_api=flow_analysis.get('target_api', {}),
            error_handling=flow_analysis.get('has_error_handling', True),
            process_name=service_name
        )
    
    elif pattern == "batch_processor":
        return generator.generate_batch_processor_process(
            source_config=flow_analysis.get('source_config', {}),
            batch_size=flow_analysis.get('batch_size', 100),
            processing_logic=flow_analysis.get('processing_logic', {}),
            target_config=flow_analysis.get('target_config', {}),
            process_name=service_name
        )
    
    elif pattern == "content_router":
        return generator.generate_content_router_process(
            source_config=flow_analysis.get('source_config', {}),
            routing_rules=flow_analysis.get('routing_rules', []),
            process_name=service_name
        )
    
    else:
        # Default to fetch-transform-send for unknown patterns
        return generator.generate_fetch_transform_send_process(
            source_connector_type="HTTP",
            source_config={},
            transform_mappings=[],
            target_connector_type="HTTP",
            target_config={},
            process_name=service_name
        )
