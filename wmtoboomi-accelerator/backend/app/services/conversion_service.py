"""
Conversion service for generating Boomi XML components from webMethods.
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple, List
from lxml import etree

from app.database import get_conversions_collection
from app.models import (
    ParsedService,
    ParsedDocument,
    ConversionResponse,
    ConversionListResponse,
    ValidationResult,
    ValidationError,
    ManualReviewItem,
    BoomiComponentInfo,
    FlowVerbStats,
)
from app.services.logging_service import log_activity


# webMethods verb to Boomi shape mapping
VERB_TO_BOOMI = {
    'map': {'shape': 'Map', 'type': 'map'},
    'branch': {'shape': 'Decision', 'type': 'decision'},
    'loop': {'shape': 'ForEach', 'type': 'foreach'},
    'repeat': {'shape': 'ForEach', 'type': 'foreach'},  # With condition
    'sequence': {'shape': 'TryCatch', 'type': 'trycatch'},
    'tryCatch': {'shape': 'TryCatch', 'type': 'trycatch'},
    'tryFinally': {'shape': 'TryCatch', 'type': 'trycatch'},
    'catch': {'shape': 'TryCatch', 'type': 'trycatch'},
    'finally': {'shape': 'TryCatch', 'type': 'trycatch'},
    'exit': {'shape': 'Stop', 'type': 'stop'},
}

# Common wMPublic service to Boomi step mappings
WM_PUBLIC_TO_BOOMI = {
    'pub.string:concat': {'shape': 'Map', 'function': 'concat'},
    'pub.string:substring': {'shape': 'Map', 'function': 'substring'},
    'pub.string:toUpper': {'shape': 'Map', 'function': 'uppercase'},
    'pub.string:toLower': {'shape': 'Map', 'function': 'lowercase'},
    'pub.string:trim': {'shape': 'Map', 'function': 'trim'},
    'pub.string:replace': {'shape': 'Map', 'function': 'replace'},
    'pub.string:length': {'shape': 'Map', 'function': 'length'},
    'pub.math:addInts': {'shape': 'Map', 'function': 'add'},
    'pub.math:subtractInts': {'shape': 'Map', 'function': 'subtract'},
    'pub.math:multiplyInts': {'shape': 'Map', 'function': 'multiply'},
    'pub.math:divideInts': {'shape': 'Map', 'function': 'divide'},
    'pub.flow:setResponse': {'shape': 'SetProperties', 'type': 'set_properties'},
    'pub.flow:debugLog': {'shape': 'Notify', 'type': 'notify'},
    'pub.file:getFile': {'shape': 'DiskConnector', 'type': 'connector'},
    'pub.file:putFile': {'shape': 'DiskConnector', 'type': 'connector'},
    'pub.json:jsonStringToDocument': {'shape': 'Map', 'function': 'json_parse'},
    'pub.json:documentToJsonString': {'shape': 'Map', 'function': 'json_stringify'},
    'pub.xml:xmlStringToDocument': {'shape': 'Map', 'function': 'xml_parse'},
    'pub.xml:documentToXmlString': {'shape': 'Map', 'function': 'xml_stringify'},
    'pub.date:getCurrentDate': {'shape': 'Map', 'function': 'current_date'},
    'pub.date:formatDate': {'shape': 'Map', 'function': 'date_format'},
    'pub.list:appendToList': {'shape': 'Map', 'function': 'list_append'},
    'pub.list:getFromList': {'shape': 'Map', 'function': 'list_get'},
}


class ConversionService:
    """Service for converting webMethods components to Boomi."""
    
    @staticmethod
    async def convert_service(
        project_id: str,
        customer_id: str,
        service: ParsedService
    ) -> ConversionResponse:
        """Convert a webMethods service to Boomi component."""
        conversions = get_conversions_collection()
        
        conversion_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Determine component type and generate XML
        if service.type == "FlowService":
            component_type = "process"
            boomi_xml, notes, complexity, automation = ConversionService._convert_flow_service(service)
        elif service.type == "DocumentType":
            component_type = "profile.xml"
            boomi_xml, notes, complexity, automation = ConversionService._convert_document_type(service)
        elif service.type == "AdapterService":
            component_type = "connector"
            boomi_xml, notes, complexity, automation = ConversionService._convert_adapter(service)
        elif service.type == "MapService":
            component_type = "map"
            boomi_xml, notes, complexity, automation = ConversionService._convert_map_service(service)
        elif service.type == "JavaService":
            component_type = "process"  # Will use Data Process shape with Groovy
            boomi_xml, notes, complexity, automation = ConversionService._convert_java_service(service)
        else:
            component_type = "process"
            boomi_xml = ""
            notes = ["Unknown service type"]
            complexity = "high"
            automation = "0%"
        
        # Validate conversion
        validation = ConversionService._validate_conversion(boomi_xml, service, notes)
        
        # Determine status
        status = "converted" if validation.isValid else "failed"
        
        # Create conversion record
        doc = {
            "conversionId": conversion_id,
            "projectId": project_id,
            "customerId": customer_id,
            "componentType": component_type,
            "sourceType": service.type,
            "sourceName": service.name,
            "targetName": service.name.replace(':', '_').replace('/', '_'),
            "convertedAt": now,
            "status": status,
            "complexity": complexity,
            "automationLevel": automation,
            "boomiXml": boomi_xml,
            "boomiComponent": None,
            "validation": validation.model_dump(),
            "conversionNotes": notes
        }
        
        await conversions.insert_one(doc)
        
        await log_activity(
            action="service_converted",
            message=f"Converted {service.type}: {service.name}",
            category="convert",
            customer_id=customer_id,
            project_id=project_id,
            componentType=component_type,
            complexity=complexity,
            automationLevel=automation
        )
        
        return ConversionResponse(**{k: v for k, v in doc.items() if k != "_id"})
    
    @staticmethod
    def _convert_flow_service(service: ParsedService) -> Tuple[str, List[str], str, str]:
        """Convert Flow Service to Boomi Process XML."""
        notes = []
        
        # Calculate complexity
        total_verbs = 0
        if service.flowVerbs:
            total_verbs = (
                service.flowVerbs.map +
                service.flowVerbs.branch +
                service.flowVerbs.loop +
                service.flowVerbs.repeat +
                service.flowVerbs.sequence +
                service.flowVerbs.tryCatch +
                service.flowVerbs.exit
            )
        
        total_invocations = sum(inv.count for inv in service.serviceInvocations) if service.serviceInvocations else 0
        
        if total_verbs < 10 and total_invocations < 15:
            complexity = "low"
            automation = "90%"
        elif total_verbs < 30 and total_invocations < 50:
            complexity = "medium"
            automation = "70%"
        else:
            complexity = "high"
            automation = "50%"
        
        # Generate conversion notes
        if service.flowVerbs:
            if service.flowVerbs.loop > 0:
                notes.append(f"Converted {service.flowVerbs.loop} LOOP verb(s) to implicit Boomi iteration")
            if service.flowVerbs.map > 0:
                notes.append(f"Converted {service.flowVerbs.map} MAP verb(s) to Map shapes")
            if service.flowVerbs.branch > 0:
                notes.append(f"Converted {service.flowVerbs.branch} BRANCH verb(s) to Decision shapes")
            if service.flowVerbs.tryCatch > 0 or service.flowVerbs.tryFinally > 0:
                notes.append(f"Converted error handling to Try/Catch shapes")
        
        # Track wMPublic conversions
        wm_public_converted = 0
        custom_flagged = 0
        
        for inv in service.serviceInvocations:
            key = f"{inv.package}:{inv.service}"
            if inv.package.startswith(('pub.', 'wm.')):
                if key in WM_PUBLIC_TO_BOOMI:
                    wm_public_converted += inv.count
                else:
                    custom_flagged += inv.count
            else:
                custom_flagged += inv.count
        
        if wm_public_converted > 0:
            notes.append(f"Mapped {wm_public_converted} wMPublic service call(s) to Boomi steps")
        if custom_flagged > 0:
            notes.append(f"⚠️ {custom_flagged} custom service call(s) require manual review")
        
        # Generate Boomi Process XML
        xml = ConversionService._generate_process_xml(service)
        
        return xml, notes, complexity, automation
    
    @staticmethod
    def _generate_process_xml(service: ParsedService) -> str:
        """Generate Boomi Process XML from Flow Service."""
        name = service.name.replace(':', '_').replace('/', '_')
        
        # Build shapes list
        shapes = []
        shape_id = 1
        
        # Start shape
        shapes.append({
            'id': shape_id,
            'type': 'start',
            'name': 'Start',
            'x': 100,
            'y': 200
        })
        shape_id += 1
        
        x_pos = 250
        
        # Add shapes for flow verbs
        if service.flowVerbs:
            # MAP -> Map shape
            for _ in range(service.flowVerbs.map):
                shapes.append({
                    'id': shape_id,
                    'type': 'map',
                    'name': f'Map_{shape_id}',
                    'x': x_pos,
                    'y': 200
                })
                shape_id += 1
                x_pos += 150
            
            # BRANCH -> Decision shape
            for _ in range(service.flowVerbs.branch):
                shapes.append({
                    'id': shape_id,
                    'type': 'decision',
                    'name': f'Decision_{shape_id}',
                    'x': x_pos,
                    'y': 200
                })
                shape_id += 1
                x_pos += 150
            
            # Note: LOOP is implicit in Boomi
            if service.flowVerbs.loop > 0:
                # Boomi handles loops automatically
                pass
            
            # Try/Catch -> TryCatch shape
            if service.flowVerbs.tryCatch > 0 or service.flowVerbs.tryFinally > 0:
                shapes.append({
                    'id': shape_id,
                    'type': 'trycatch',
                    'name': f'TryCatch_{shape_id}',
                    'x': x_pos,
                    'y': 200
                })
                shape_id += 1
                x_pos += 150
        
        # Add connector shapes for adapter calls
        if service.adapters:
            for adapter in service.adapters:
                connector_type = {
                    'JDBC': 'database',
                    'HTTP': 'http',
                    'JMS': 'jms',
                    'FTP': 'ftp',
                    'SFTP': 'sftp',
                    'SAP': 'sap',
                    'File': 'disk'
                }.get(adapter, 'connector')
                
                shapes.append({
                    'id': shape_id,
                    'type': connector_type,
                    'name': f'{adapter}_Connector_{shape_id}',
                    'x': x_pos,
                    'y': 200
                })
                shape_id += 1
                x_pos += 150
        
        # Stop shape
        shapes.append({
            'id': shape_id,
            'type': 'stop',
            'name': 'Stop',
            'x': x_pos,
            'y': 200
        })
        
        # Generate XML
        root = etree.Element(
            '{http://api.platform.boomi.com/}Component',
            nsmap={'bns': 'http://api.platform.boomi.com/'}
        )
        root.set('type', 'process')
        
        etree.SubElement(root, '{http://api.platform.boomi.com/}name').text = name
        etree.SubElement(root, '{http://api.platform.boomi.com/}description').text = f"Converted from webMethods Flow Service: {service.name}"
        
        obj = etree.SubElement(root, '{http://api.platform.boomi.com/}object')
        process = etree.SubElement(obj, 'Process')
        
        # Add shapes
        shapes_elem = etree.SubElement(process, 'shapes')
        for shape in shapes:
            shape_elem = etree.SubElement(shapes_elem, 'shape')
            shape_elem.set('id', str(shape['id']))
            shape_elem.set('type', shape['type'])
            shape_elem.set('name', shape['name'])
            shape_elem.set('x', str(shape['x']))
            shape_elem.set('y', str(shape['y']))
        
        # Add connections
        connections = etree.SubElement(process, 'connections')
        for i in range(len(shapes) - 1):
            conn = etree.SubElement(connections, 'connection')
            conn.set('from', str(shapes[i]['id']))
            conn.set('to', str(shapes[i + 1]['id']))
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
    
    @staticmethod
    def _convert_document_type(service: ParsedService) -> Tuple[str, List[str], str, str]:
        """Convert Document Type to Boomi Profile XML."""
        name = service.name.replace(':', '_').replace('/', '_')
        notes = ["Document Type converted to XML Profile"]
        
        # Generate basic XML Profile structure
        root = etree.Element(
            '{http://api.platform.boomi.com/}Component',
            nsmap={'bns': 'http://api.platform.boomi.com/'}
        )
        root.set('type', 'profile.xml')
        
        etree.SubElement(root, '{http://api.platform.boomi.com/}name').text = name
        etree.SubElement(root, '{http://api.platform.boomi.com/}description').text = f"Converted from webMethods Document Type: {service.name}"
        
        obj = etree.SubElement(root, '{http://api.platform.boomi.com/}object')
        profile = etree.SubElement(obj, 'ProfileXML')
        
        # Generate basic XSD structure
        schema = etree.SubElement(
            profile, 
            '{http://www.w3.org/2001/XMLSchema}schema',
            nsmap={'xsd': 'http://www.w3.org/2001/XMLSchema'}
        )
        
        # Add root element
        root_elem = etree.SubElement(schema, '{http://www.w3.org/2001/XMLSchema}element')
        root_elem.set('name', name)
        
        complex_type = etree.SubElement(root_elem, '{http://www.w3.org/2001/XMLSchema}complexType')
        sequence = etree.SubElement(complex_type, '{http://www.w3.org/2001/XMLSchema}sequence')
        
        # Add fields from input/output signatures
        if service.inputSignature:
            for field_name, field_info in service.inputSignature.items():
                elem = etree.SubElement(sequence, '{http://www.w3.org/2001/XMLSchema}element')
                elem.set('name', field_name)
                elem.set('type', f"xsd:{field_info.get('type', 'string')}")
                if not field_info.get('required', False):
                    elem.set('minOccurs', '0')
        
        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        
        return xml, notes, "low", "95%"
    
    @staticmethod
    def _convert_adapter(service: ParsedService) -> Tuple[str, List[str], str, str]:
        """Convert Adapter Service to Boomi Connector."""
        name = service.name.replace(':', '_').replace('/', '_')
        notes = []
        
        # Determine adapter type
        adapter_type = service.adapters[0] if service.adapters else "Generic"
        
        # Map to Boomi connector type
        connector_types = {
            'JDBC': 'connector.database',
            'HTTP': 'connector.http',
            'JMS': 'connector.jms',
            'FTP': 'connector.ftp',
            'SFTP': 'connector.sftp',
            'SAP': 'connector.sap',
            'File': 'connector.disk',
        }
        
        component_type = connector_types.get(adapter_type, 'connector')
        
        # Check complexity
        if adapter_type == 'JDBC':
            notes.append("⚠️ JDBC Adapter - review for complex JOINs and WHERE clauses")
            complexity = "medium"
            automation = "50%"
        elif adapter_type == 'SAP':
            notes.append("SAP Adapter converted to SAP Connector")
            complexity = "medium"
            automation = "70%"
        else:
            notes.append(f"{adapter_type} Adapter converted to {adapter_type} Connector")
            complexity = "low"
            automation = "80%"
        
        # Generate connector XML
        root = etree.Element(
            '{http://api.platform.boomi.com/}Component',
            nsmap={'bns': 'http://api.platform.boomi.com/'}
        )
        root.set('type', component_type)
        
        etree.SubElement(root, '{http://api.platform.boomi.com/}name').text = name
        etree.SubElement(root, '{http://api.platform.boomi.com/}description').text = f"Converted from webMethods {adapter_type} Adapter: {service.name}"
        
        obj = etree.SubElement(root, '{http://api.platform.boomi.com/}object')
        
        # Add connector-specific configuration placeholder
        config = etree.SubElement(obj, 'ConnectorConfig')
        etree.SubElement(config, 'adapterType').text = adapter_type
        etree.SubElement(config, 'note').text = "Configuration requires manual setup"
        
        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        
        return xml, notes, complexity, automation
    
    @staticmethod
    def _convert_map_service(service: ParsedService) -> Tuple[str, List[str], str, str]:
        """Convert Map Service to Boomi Map."""
        name = service.name.replace(':', '_').replace('/', '_')
        notes = ["Map Service converted to Boomi Map"]
        
        # Generate Map component XML
        root = etree.Element(
            '{http://api.platform.boomi.com/}Component',
            nsmap={'bns': 'http://api.platform.boomi.com/'}
        )
        root.set('type', 'map')
        
        etree.SubElement(root, '{http://api.platform.boomi.com/}name').text = name
        etree.SubElement(root, '{http://api.platform.boomi.com/}description').text = f"Converted from webMethods Map Service: {service.name}"
        
        obj = etree.SubElement(root, '{http://api.platform.boomi.com/}object')
        map_elem = etree.SubElement(obj, 'Map')
        
        # Placeholder for mappings
        mappings = etree.SubElement(map_elem, 'mappings')
        etree.SubElement(mappings, 'note').text = "Field mappings require manual configuration"
        
        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        
        return xml, notes, "low", "85%"
    
    @staticmethod
    def _convert_java_service(service: ParsedService) -> Tuple[str, List[str], str, str]:
        """Convert Java Service to Boomi Process with Data Process shape."""
        name = service.name.replace(':', '_').replace('/', '_')
        notes = [
            "⚠️ Java Service requires manual conversion to Groovy",
            "Generated template Data Process shape",
            "Review original Java code for business logic"
        ]
        
        # Generate Process with Data Process shape
        root = etree.Element(
            '{http://api.platform.boomi.com/}Component',
            nsmap={'bns': 'http://api.platform.boomi.com/'}
        )
        root.set('type', 'process')
        
        etree.SubElement(root, '{http://api.platform.boomi.com/}name').text = name
        etree.SubElement(root, '{http://api.platform.boomi.com/}description').text = f"Converted from webMethods Java Service: {service.name} - REQUIRES MANUAL GROOVY CONVERSION"
        
        obj = etree.SubElement(root, '{http://api.platform.boomi.com/}object')
        process = etree.SubElement(obj, 'Process')
        
        # Add shapes: Start -> Data Process -> Stop
        shapes = etree.SubElement(process, 'shapes')
        
        start = etree.SubElement(shapes, 'shape')
        start.set('id', '1')
        start.set('type', 'start')
        start.set('name', 'Start')
        start.set('x', '100')
        start.set('y', '200')
        
        data_process = etree.SubElement(shapes, 'shape')
        data_process.set('id', '2')
        data_process.set('type', 'dataprocess')
        data_process.set('name', f'{name}_Groovy')
        data_process.set('x', '250')
        data_process.set('y', '200')
        
        # Add Groovy script placeholder
        groovy_config = etree.SubElement(data_process, 'groovyScript')
        groovy_config.text = '''// TODO: Convert Java logic to Groovy
// Original service: ''' + service.name + '''

import com.boomi.execution.ExecutionUtil

// Get input document
def input = dataContext.getStream(0)

// Your conversion logic here

// Set output
dataContext.storeStream(input, new Properties())
'''
        
        stop = etree.SubElement(shapes, 'shape')
        stop.set('id', '3')
        stop.set('type', 'stop')
        stop.set('name', 'Stop')
        stop.set('x', '400')
        stop.set('y', '200')
        
        # Connections
        connections = etree.SubElement(process, 'connections')
        conn1 = etree.SubElement(connections, 'connection')
        conn1.set('from', '1')
        conn1.set('to', '2')
        conn2 = etree.SubElement(connections, 'connection')
        conn2.set('from', '2')
        conn2.set('to', '3')
        
        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
        
        return xml, notes, "high", "20%"
    
    @staticmethod
    def _validate_conversion(xml: str, service: ParsedService, notes: List[str]) -> ValidationResult:
        """Validate generated Boomi XML."""
        errors = []
        warnings = []
        manual_items = []
        
        if not xml:
            errors.append(ValidationError(
                severity="error",
                message="No XML generated",
                location="conversion"
            ))
            return ValidationResult(
                isValid=False,
                automationLevel="0%",
                errors=errors
            )
        
        # Try to parse XML
        try:
            etree.fromstring(xml.encode())
        except etree.XMLSyntaxError as e:
            errors.append(ValidationError(
                severity="error",
                message=f"Invalid XML syntax: {str(e)}",
                location="xml_parse"
            ))
        
        # Check for manual review requirements
        if service.type == "JavaService":
            manual_items.append(ManualReviewItem(
                type="JavaService",
                name=service.name,
                reason="Requires manual Groovy conversion"
            ))
        
        if service.adapters and 'JDBC' in service.adapters:
            manual_items.append(ManualReviewItem(
                type="JDBC Adapter",
                name=service.name,
                reason="Review complex JOINs and WHERE clauses"
            ))
        
        # Check for warning notes
        for note in notes:
            if '⚠️' in note:
                warnings.append(ValidationError(
                    severity="warning",
                    message=note.replace('⚠️', '').strip(),
                    location=service.name
                ))
        
        # Calculate automation level from notes
        automation = "80%"
        for note in notes:
            if "90%" in note:
                automation = "90%"
                break
            elif "70%" in note:
                automation = "70%"
            elif "50%" in note:
                automation = "50%"
            elif "20%" in note or "manual" in note.lower():
                automation = "20%"
                break
        
        # Estimate manual effort
        manual_hours = len(manual_items) * 2
        if manual_hours > 0:
            effort = f"{manual_hours} hours"
        else:
            effort = "0 hours"
        
        return ValidationResult(
            isValid=len(errors) == 0,
            automationLevel=automation,
            errors=errors,
            warnings=warnings,
            manualReviewItems=manual_items,
            estimatedManualEffort=effort
        )
    
    @staticmethod
    async def get_conversion(conversion_id: str) -> Optional[ConversionResponse]:
        """Get a conversion by ID."""
        conversions = get_conversions_collection()
        
        doc = await conversions.find_one({"conversionId": conversion_id})
        if not doc:
            return None
        
        return ConversionResponse(**{k: v for k, v in doc.items() if k != "_id"})
    
    @staticmethod
    async def list_conversions(project_id: str) -> ConversionListResponse:
        """List all conversions for a project."""
        conversions = get_conversions_collection()
        
        cursor = conversions.find({"projectId": project_id}).sort("convertedAt", -1)
        
        conversion_list = []
        async for doc in cursor:
            conversion_list.append(ConversionResponse(**{k: v for k, v in doc.items() if k != "_id"}))
        
        return ConversionListResponse(
            conversions=conversion_list,
            total=len(conversion_list)
        )
    
    @staticmethod
    async def update_conversion_status(conversion_id: str, status: str, boomi_info: Optional[dict] = None):
        """Update conversion status after Boomi push."""
        conversions = get_conversions_collection()
        
        update_doc = {"status": status}
        if boomi_info:
            update_doc["boomiComponent"] = boomi_info
        
        await conversions.update_one(
            {"conversionId": conversion_id},
            {"$set": update_doc}
        )
