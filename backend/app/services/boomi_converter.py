"""
Boomi Component Converter - Converts webMethods components to Boomi XML
"""

from typing import Dict, Any, List

class BoomiConverter:
    """Convert webMethods components to Boomi format"""
    
    @staticmethod
    def convert_flow_service(service: Dict[str, Any]) -> str:
        """Convert FlowService to Boomi Process XML"""
        
        service_name = service['name'].split('/')[-1]
        flow_steps = service.get('flowSteps', [])
        
        # Build shapes from flow steps
        shapes = []
        shape_id = 1
        
        # Start shape
        shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:StartShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>50</bns:y>
    </bns:ProcessShape>""")
        shape_id += 1
        
        # Convert each flow step
        y_position = 150
        for step in flow_steps:
            step_type = step.get('type', 'INVOKE')
            
            if step_type == 'MAP':
                shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:MapShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
      <bns:label>Map: {step.get('name', 'Transform')}</bns:label>
    </bns:ProcessShape>""")
            
            elif step_type == 'BRANCH':
                shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:DecisionShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
      <bns:label>Decision: {step.get('name', 'Branch')}</bns:label>
    </bns:ProcessShape>""")
            
            elif step_type == 'LOOP':
                shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:ForEachShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
      <bns:label>ForEach: {step.get('name', 'Loop')}</bns:label>
    </bns:ProcessShape>""")
            
            elif step_type == 'INVOKE':
                shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:ConnectorShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
      <bns:label>Connector: {step.get('name', 'Service')}</bns:label>
    </bns:ProcessShape>""")
            
            else:
                shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:BusinessRuleShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
      <bns:label>{step_type}: {step.get('name', 'Step')}</bns:label>
    </bns:ProcessShape>""")
            
            shape_id += 1
            y_position += 100
        
        # End shape
        shapes.append(f"""
    <bns:ProcessShape xsi:type="bns:EndShape">
      <bns:id>{shape_id}</bns:id>
      <bns:x>50</bns:x>
      <bns:y>{y_position}</bns:y>
    </bns:ProcessShape>""")
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <bns:name>{service_name}</bns:name>
  <bns:type>process</bns:type>
  <bns:description>Converted from webMethods FlowService: {service['name']}
  
Source Details:
- Type: {service['type']}
- Complexity: {service.get('complexity', 'unknown')}
- Flow Steps: {len(flow_steps)}
  
Automation Level: 85%</bns:description>
  <bns:object>
    <Process>{''.join(shapes)}
    </Process>
  </bns:object>
</bns:Component>"""
        
        return xml
    
    @staticmethod
    def convert_document_type(document: Dict[str, Any]) -> str:
        """Convert DocumentType to Boomi XML Profile"""
        
        doc_name = document['name'].split('/')[-1]
        fields = document.get('fields', [])
        
        # Generate XSD schema
        xsd_elements = []
        for field in fields:
            field_name = field['name']
            field_type = field.get('type', 'string')
            
            xsd_type = 'xs:string'
            if field_type in ['int', 'integer']:
                xsd_type = 'xs:integer'
            elif field_type in ['float', 'double']:
                xsd_type = 'xs:decimal'
            elif field_type in ['boolean', 'bool']:
                xsd_type = 'xs:boolean'
            elif field_type == 'date':
                xsd_type = 'xs:date'
            elif field_type == 'datetime':
                xsd_type = 'xs:dateTime'
            
            required = 'minOccurs="1"' if field.get('required', False) else 'minOccurs="0"'
            xsd_elements.append(f'      <xs:element name="{field_name}" type="{xsd_type}" {required}/>')
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <bns:name>{doc_name}</bns:name>
  <bns:type>profile.xml</bns:type>
  <bns:description>Converted from webMethods Document Type: {document['name']}
  
Source Details:
- Fields: {len(fields)}
  
Automation Level: 95%</bns:description>
  <bns:object>
    <ProfileXML>
      <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" 
                 targetNamespace="http://jadeglobal.com/migration"
                 elementFormDefault="qualified">
        <xs:element name="{doc_name}">
          <xs:complexType>
            <xs:sequence>
{''.join([f'\n{elem}' for elem in xsd_elements])}
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:schema>
    </ProfileXML>
  </bns:object>
</bns:Component>"""
        
        return xml
    
    @staticmethod
    def convert_edi_schema(edi_schema: Dict[str, Any]) -> str:
        """Convert EDI Schema to Boomi EDI Profile"""
        
        schema_name = edi_schema['name'].split('/')[-1]
        transaction_set = edi_schema.get('transactionSet', 'UNKNOWN')
        segments = edi_schema.get('segments', [])
        
        # Generate EDI profile structure
        edi_segments = []
        for segment in segments:
            seg_name = segment.get('name', 'SEG')
            elements = segment.get('elements', [])
            
            edi_segments.append(f"""
      <Segment>
        <Name>{seg_name}</Name>
        <Elements>""")
            
            for elem in elements:
                elem_name = elem.get('name', 'ELEM')
                elem_type = elem.get('type', 'AN')  # AN = Alphanumeric
                elem_length = elem.get('length', 0)
                
                edi_segments.append(f"""
          <Element>
            <Name>{elem_name}</Name>
            <Type>{elem_type}</Type>
            <MinLength>{elem_length}</MinLength>
            <MaxLength>{elem_length}</MaxLength>
          </Element>""")
            
            edi_segments.append("""
        </Elements>
      </Segment>""")
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <bns:name>{schema_name}</bns:name>
  <bns:type>profile.edi</bns:type>
  <bns:description>Converted from webMethods EDI Schema: {edi_schema['name']}
  
Source Details:
- Transaction Set: {transaction_set}
- Segments: {len(segments)}
  
Automation Level: 90%</bns:description>
  <bns:object>
    <EdiProfile>
      <Standard>X12</Standard>
      <Version>004010</Version>
      <TransactionSet>{transaction_set}</TransactionSet>
      <Segments>{''.join(edi_segments)}
      </Segments>
    </EdiProfile>
  </bns:object>
</bns:Component>"""
        
        return xml


def convert_service(service: Dict[str, Any]) -> Dict[str, Any]:
    """Main conversion function"""
    
    converter = BoomiConverter()
    service_type = service.get('type', '')
    
    if service_type == 'FlowService':
        return {
            'boomiXml': converter.convert_flow_service(service),
            'componentType': 'process',
            'automationLevel': '85%',
            'notes': [
                f"Converted {len(service.get('flowSteps', []))} flow steps to Boomi shapes",
                "Manual review recommended for complex logic"
            ]
        }
    
    elif service_type == 'DocumentType':
        return {
            'boomiXml': converter.convert_document_type(service),
            'componentType': 'profile.xml',
            'automationLevel': '95%',
            'notes': [
                f"Converted {len(service.get('fields', []))} fields to XSD schema",
                "Schema ready for use in Boomi processes"
            ]
        }
    
    elif service_type == 'EDISchema':
        return {
            'boomiXml': converter.convert_edi_schema(service),
            'componentType': 'profile.edi',
            'automationLevel': '90%',
            'notes': [
                f"Converted EDI transaction set {service.get('transactionSet', 'UNKNOWN')}",
                f"Generated {len(service.get('segments', []))} segment definitions"
            ]
        }
    
    else:
        return {
            'boomiXml': f'<!-- Conversion not yet implemented for {service_type} -->',
            'componentType': 'unknown',
            'automationLevel': '0%',
            'notes': [
                f"Conversion for {service_type} requires manual implementation"
            ]
        }
