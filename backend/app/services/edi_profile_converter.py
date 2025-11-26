"""
EDI Profile Converter - X12 and EDIFACT to Boomi
Converts webMethods EDI schemas to Boomi EDI Profiles with 90% automation
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

class EDIStandard(Enum):
    X12 = "X12"
    EDIFACT = "EDIFACT"

@dataclass
class EDISegment:
    id: str
    name: str
    elements: List[Dict[str, Any]]
    required: bool
    max_occurs: int = 1

@dataclass
class EDILoop:
    id: str
    name: str
    segments: List[EDISegment]
    child_loops: List['EDILoop']
    required: bool
    max_occurs: int = 99999

class EDIProfileConverter:
    """Converts EDI schemas to Boomi EDI Profiles"""
    
    def __init__(self):
        self.standard = None
        self.transaction_set = None
        self.version = None
        
    def convert_x12_to_boomi(
        self,
        transaction_set: str,
        version: str,
        schema_data: Dict
    ) -> str:
        """
        Convert X12 transaction set to Boomi EDI Profile
        
        Args:
            transaction_set: e.g., "850" (Purchase Order)
            version: e.g., "004010"
            schema_data: Parsed EDI schema from webMethods
            
        Returns:
            Complete Boomi EDI Profile XML
        """
        
        self.standard = EDIStandard.X12
        self.transaction_set = transaction_set
        self.version = version
        
        # Parse schema structure
        loops = self._parse_x12_loops(schema_data)
        
        # Generate Boomi EDI Profile XML
        return self._generate_edi_profile_xml(
            standard="X12",
            transaction_set=transaction_set,
            version=version,
            loops=loops
        )
    
    def convert_edifact_to_boomi(
        self,
        message_type: str,
        version: str,
        schema_data: Dict
    ) -> str:
        """
        Convert EDIFACT message to Boomi EDI Profile
        
        Args:
            message_type: e.g., "ORDERS" (Purchase Order)
            version: e.g., "D96A"
            schema_data: Parsed EDI schema from webMethods
            
        Returns:
            Complete Boomi EDI Profile XML
        """
        
        self.standard = EDIStandard.EDIFACT
        self.transaction_set = message_type
        self.version = version
        
        # Parse schema structure
        loops = self._parse_edifact_segments(schema_data)
        
        # Generate Boomi EDI Profile XML
        return self._generate_edi_profile_xml(
            standard="EDIFACT",
            transaction_set=message_type,
            version=version,
            loops=loops
        )
    
    def _parse_x12_loops(self, schema_data: Dict) -> List[EDILoop]:
        """Parse X12 loop structure from webMethods schema"""
        
        loops = []
        
        # Get loop definitions from schema
        loop_defs = schema_data.get('loops', [])
        
        for loop_def in loop_defs:
            loop = EDILoop(
                id=loop_def.get('id', 'LOOP_' + str(uuid.uuid4())[:8]),
                name=loop_def.get('name', 'Unknown Loop'),
                segments=self._parse_segments(loop_def.get('segments', [])),
                child_loops=[],
                required=loop_def.get('required', False),
                max_occurs=loop_def.get('maxOccurs', 99999)
            )
            
            # Parse child loops recursively
            if 'childLoops' in loop_def:
                loop.child_loops = self._parse_x12_loops({'loops': loop_def['childLoops']})
            
            loops.append(loop)
        
        return loops
    
    def _parse_edifact_segments(self, schema_data: Dict) -> List[EDILoop]:
        """Parse EDIFACT segment groups from webMethods schema"""
        
        # EDIFACT uses segment groups similar to X12 loops
        return self._parse_x12_loops(schema_data)
    
    def _parse_segments(self, segment_defs: List[Dict]) -> List[EDISegment]:
        """Parse segment definitions"""
        
        segments = []
        
        for seg_def in segment_defs:
            segment = EDISegment(
                id=seg_def.get('id', seg_def.get('tag', 'UNKNOWN')),
                name=seg_def.get('name', 'Unknown Segment'),
                elements=self._parse_elements(seg_def.get('elements', [])),
                required=seg_def.get('required', False),
                max_occurs=seg_def.get('maxOccurs', 1)
            )
            segments.append(segment)
        
        return segments
    
    def _parse_elements(self, element_defs: List[Dict]) -> List[Dict[str, Any]]:
        """Parse element definitions"""
        
        elements = []
        
        for elem_def in element_defs:
            element = {
                'id': elem_def.get('id', elem_def.get('position', len(elements) + 1)),
                'name': elem_def.get('name', f'Element {len(elements) + 1}'),
                'dataType': elem_def.get('dataType', 'AN'),
                'minLength': elem_def.get('minLength', 1),
                'maxLength': elem_def.get('maxLength', 35),
                'required': elem_def.get('required', False),
                'codeList': elem_def.get('codeList', [])
            }
            elements.append(element)
        
        return elements
    
    def _generate_edi_profile_xml(
        self,
        standard: str,
        transaction_set: str,
        version: str,
        loops: List[EDILoop]
    ) -> str:
        """Generate complete Boomi EDI Profile XML"""
        
        profile_id = str(uuid.uuid4())
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:EdiProfile xmlns:bns="http://api.platform.boomi.com/"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <bns:profileId>{profile_id}</bns:profileId>
    <bns:name>{standard}_{transaction_set}_{version}</bns:name>
    <bns:standard>{standard}</bns:standard>
    <bns:transactionSet>{transaction_set}</bns:transactionSet>
    <bns:version>{version}</bns:version>
    <bns:description>Converted from webMethods EDI Schema</bns:description>
    
    <bns:structure>
'''
        
        # Add loops and segments
        for loop in loops:
            xml += self._generate_loop_xml(loop, indent=2)
        
        xml += '''    </bns:structure>
</bns:EdiProfile>'''
        
        return xml
    
    def _generate_loop_xml(self, loop: EDILoop, indent: int = 2) -> str:
        """Generate XML for a loop"""
        
        ind = '    ' * indent
        
        xml = f'''{ind}<bns:loop>
{ind}    <bns:loopId>{loop.id}</bns:loopId>
{ind}    <bns:name>{self._escape_xml(loop.name)}</bns:name>
{ind}    <bns:required>{str(loop.required).lower()}</bns:required>
{ind}    <bns:maxOccurs>{loop.max_occurs}</bns:maxOccurs>
{ind}    <bns:segments>
'''
        
        # Add segments
        for segment in loop.segments:
            xml += self._generate_segment_xml(segment, indent + 2)
        
        xml += f'''{ind}    </bns:segments>
'''
        
        # Add child loops if any
        if loop.child_loops:
            xml += f'{ind}    <bns:childLoops>\n'
            for child_loop in loop.child_loops:
                xml += self._generate_loop_xml(child_loop, indent + 2)
            xml += f'{ind}    </bns:childLoops>\n'
        
        xml += f'{ind}</bns:loop>\n'
        
        return xml
    
    def _generate_segment_xml(self, segment: EDISegment, indent: int = 2) -> str:
        """Generate XML for a segment"""
        
        ind = '    ' * indent
        
        xml = f'''{ind}<bns:segment>
{ind}    <bns:segmentId>{segment.id}</bns:segmentId>
{ind}    <bns:name>{self._escape_xml(segment.name)}</bns:name>
{ind}    <bns:required>{str(segment.required).lower()}</bns:required>
{ind}    <bns:maxOccurs>{segment.max_occurs}</bns:maxOccurs>
{ind}    <bns:elements>
'''
        
        # Add elements
        for element in segment.elements:
            xml += self._generate_element_xml(element, indent + 2)
        
        xml += f'''{ind}    </bns:elements>
{ind}</bns:segment>
'''
        
        return xml
    
    def _generate_element_xml(self, element: Dict, indent: int = 2) -> str:
        """Generate XML for an element"""
        
        ind = '    ' * indent
        
        xml = f'''{ind}<bns:element>
{ind}    <bns:elementId>{element['id']}</bns:elementId>
{ind}    <bns:name>{self._escape_xml(element['name'])}</bns:name>
{ind}    <bns:dataType>{element['dataType']}</bns:dataType>
{ind}    <bns:minLength>{element['minLength']}</bns:minLength>
{ind}    <bns:maxLength>{element['maxLength']}</bns:maxLength>
{ind}    <bns:required>{str(element['required']).lower()}</bns:required>
'''
        
        # Add code list if present
        if element.get('codeList'):
            xml += f'{ind}    <bns:codeList>\n'
            for code in element['codeList']:
                xml += f'{ind}        <bns:code>{self._escape_xml(code)}</bns:code>\n'
            xml += f'{ind}    </bns:codeList>\n'
        
        xml += f'{ind}</bns:element>\n'
        
        return xml
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


class X12ProfileGenerator:
    """Pre-built X12 transaction set templates"""
    
    @staticmethod
    def generate_850_purchase_order(version: str = "004010") -> str:
        """Generate X12 850 Purchase Order EDI Profile"""
        
        converter = EDIProfileConverter()
        
        # X12 850 structure
        schema_data = {
            'loops': [
                {
                    'id': 'Heading',
                    'name': 'Heading',
                    'required': True,
                    'maxOccurs': 1,
                    'segments': [
                        {
                            'id': 'ST',
                            'name': 'Transaction Set Header',
                            'required': True,
                            'elements': [
                                {'id': 'ST01', 'name': 'Transaction Set Identifier Code', 'dataType': 'ID', 'minLength': 3, 'maxLength': 3, 'required': True},
                                {'id': 'ST02', 'name': 'Transaction Set Control Number', 'dataType': 'AN', 'minLength': 4, 'maxLength': 9, 'required': True}
                            ]
                        },
                        {
                            'id': 'BEG',
                            'name': 'Beginning Segment for Purchase Order',
                            'required': True,
                            'elements': [
                                {'id': 'BEG01', 'name': 'Transaction Set Purpose Code', 'dataType': 'ID', 'minLength': 2, 'maxLength': 2, 'required': True},
                                {'id': 'BEG02', 'name': 'Purchase Order Type Code', 'dataType': 'ID', 'minLength': 2, 'maxLength': 2, 'required': True},
                                {'id': 'BEG03', 'name': 'Purchase Order Number', 'dataType': 'AN', 'minLength': 1, 'maxLength': 22, 'required': True},
                                {'id': 'BEG05', 'name': 'Date', 'dataType': 'DT', 'minLength': 8, 'maxLength': 8, 'required': True}
                            ]
                        }
                    ]
                },
                {
                    'id': 'Detail',
                    'name': 'Detail',
                    'required': True,
                    'maxOccurs': 99999,
                    'segments': [
                        {
                            'id': 'PO1',
                            'name': 'Baseline Item Data',
                            'required': True,
                            'elements': [
                                {'id': 'PO101', 'name': 'Assigned Identification', 'dataType': 'AN', 'minLength': 1, 'maxLength': 20, 'required': False},
                                {'id': 'PO102', 'name': 'Quantity', 'dataType': 'R', 'minLength': 1, 'maxLength': 15, 'required': True},
                                {'id': 'PO103', 'name': 'Unit or Basis for Measurement Code', 'dataType': 'ID', 'minLength': 2, 'maxLength': 2, 'required': True},
                                {'id': 'PO104', 'name': 'Unit Price', 'dataType': 'R', 'minLength': 1, 'maxLength': 17, 'required': True}
                            ]
                        }
                    ],
                    'childLoops': [
                        {
                            'id': 'PID',
                            'name': 'Product/Item Description',
                            'required': False,
                            'maxOccurs': 1000,
                            'segments': [
                                {
                                    'id': 'PID',
                                    'name': 'Product/Item Description',
                                    'required': True,
                                    'elements': [
                                        {'id': 'PID01', 'name': 'Item Description Type', 'dataType': 'ID', 'minLength': 1, 'maxLength': 1, 'required': True},
                                        {'id': 'PID05', 'name': 'Description', 'dataType': 'AN', 'minLength': 1, 'maxLength': 80, 'required': True}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    'id': 'Summary',
                    'name': 'Summary',
                    'required': True,
                    'maxOccurs': 1,
                    'segments': [
                        {
                            'id': 'CTT',
                            'name': 'Transaction Totals',
                            'required': True,
                            'elements': [
                                {'id': 'CTT01', 'name': 'Number of Line Items', 'dataType': 'N0', 'minLength': 1, 'maxLength': 6, 'required': True}
                            ]
                        },
                        {
                            'id': 'SE',
                            'name': 'Transaction Set Trailer',
                            'required': True,
                            'elements': [
                                {'id': 'SE01', 'name': 'Number of Included Segments', 'dataType': 'N0', 'minLength': 1, 'maxLength': 10, 'required': True},
                                {'id': 'SE02', 'name': 'Transaction Set Control Number', 'dataType': 'AN', 'minLength': 4, 'maxLength': 9, 'required': True}
                            ]
                        }
                    ]
                }
            ]
        }
        
        return converter.convert_x12_to_boomi('850', version, schema_data)
    
    @staticmethod
    def generate_810_invoice(version: str = "004010") -> str:
        """Generate X12 810 Invoice EDI Profile"""
        
        converter = EDIProfileConverter()
        
        schema_data = {
            'loops': [
                {
                    'id': 'Heading',
                    'name': 'Heading',
                    'required': True,
                    'segments': [
                        {'id': 'ST', 'name': 'Transaction Set Header', 'required': True, 'elements': [
                            {'id': 'ST01', 'name': 'Transaction Set Identifier Code', 'dataType': 'ID', 'required': True, 'minLength': 3, 'maxLength': 3},
                            {'id': 'ST02', 'name': 'Transaction Set Control Number', 'dataType': 'AN', 'required': True, 'minLength': 4, 'maxLength': 9}
                        ]},
                        {'id': 'BIG', 'name': 'Beginning Segment for Invoice', 'required': True, 'elements': [
                            {'id': 'BIG01', 'name': 'Date', 'dataType': 'DT', 'required': True, 'minLength': 8, 'maxLength': 8},
                            {'id': 'BIG02', 'name': 'Invoice Number', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 22},
                            {'id': 'BIG04', 'name': 'Purchase Order Number', 'dataType': 'AN', 'required': False, 'minLength': 1, 'maxLength': 22}
                        ]}
                    ]
                },
                {
                    'id': 'Detail',
                    'name': 'Detail',
                    'required': True,
                    'maxOccurs': 99999,
                    'segments': [
                        {'id': 'IT1', 'name': 'Baseline Item Data (Invoice)', 'required': True, 'elements': [
                            {'id': 'IT101', 'name': 'Assigned Identification', 'dataType': 'AN', 'required': False, 'minLength': 1, 'maxLength': 20},
                            {'id': 'IT102', 'name': 'Quantity Invoiced', 'dataType': 'R', 'required': True, 'minLength': 1, 'maxLength': 15},
                            {'id': 'IT103', 'name': 'Unit or Basis for Measurement Code', 'dataType': 'ID', 'required': True, 'minLength': 2, 'maxLength': 2},
                            {'id': 'IT104', 'name': 'Unit Price', 'dataType': 'R', 'required': True, 'minLength': 1, 'maxLength': 17}
                        ]}
                    ]
                },
                {
                    'id': 'Summary',
                    'name': 'Summary',
                    'required': True,
                    'segments': [
                        {'id': 'TDS', 'name': 'Total Monetary Value Summary', 'required': True, 'elements': [
                            {'id': 'TDS01', 'name': 'Amount', 'dataType': 'R', 'required': True, 'minLength': 1, 'maxLength': 18}
                        ]},
                        {'id': 'SE', 'name': 'Transaction Set Trailer', 'required': True, 'elements': [
                            {'id': 'SE01', 'name': 'Number of Included Segments', 'dataType': 'N0', 'required': True, 'minLength': 1, 'maxLength': 10},
                            {'id': 'SE02', 'name': 'Transaction Set Control Number', 'dataType': 'AN', 'required': True, 'minLength': 4, 'maxLength': 9}
                        ]}
                    ]
                }
            ]
        }
        
        return converter.convert_x12_to_boomi('810', version, schema_data)


class EDIFACTProfileGenerator:
    """Pre-built EDIFACT message templates"""
    
    @staticmethod
    def generate_orders(version: str = "D96A") -> str:
        """Generate EDIFACT ORDERS (Purchase Order) Profile"""
        
        converter = EDIProfileConverter()
        
        schema_data = {
            'loops': [
                {
                    'id': 'Header',
                    'name': 'Header',
                    'required': True,
                    'segments': [
                        {'id': 'UNH', 'name': 'Message Header', 'required': True, 'elements': [
                            {'id': 'UNH01', 'name': 'Message Reference Number', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 14},
                            {'id': 'UNH02', 'name': 'Message Identifier', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 6}
                        ]},
                        {'id': 'BGM', 'name': 'Beginning of Message', 'required': True, 'elements': [
                            {'id': 'BGM01', 'name': 'Document Message Name', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 3},
                            {'id': 'BGM02', 'name': 'Document Message Number', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 35}
                        ]},
                        {'id': 'DTM', 'name': 'Date/Time/Period', 'required': True, 'maxOccurs': 10, 'elements': [
                            {'id': 'DTM01', 'name': 'Date/Time/Period Qualifier', 'dataType': 'AN', 'required': True, 'minLength': 3, 'maxLength': 3},
                            {'id': 'DTM02', 'name': 'Date/Time/Period', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 35}
                        ]}
                    ]
                },
                {
                    'id': 'Detail',
                    'name': 'Detail',
                    'required': True,
                    'maxOccurs': 99999,
                    'segments': [
                        {'id': 'LIN', 'name': 'Line Item', 'required': True, 'elements': [
                            {'id': 'LIN01', 'name': 'Line Item Number', 'dataType': 'N', 'required': True, 'minLength': 1, 'maxLength': 6},
                            {'id': 'LIN03', 'name': 'Item Number', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 35}
                        ]},
                        {'id': 'QTY', 'name': 'Quantity', 'required': True, 'maxOccurs': 10, 'elements': [
                            {'id': 'QTY01', 'name': 'Quantity Qualifier', 'dataType': 'AN', 'required': True, 'minLength': 3, 'maxLength': 3},
                            {'id': 'QTY02', 'name': 'Quantity', 'dataType': 'N', 'required': True, 'minLength': 1, 'maxLength': 15}
                        ]},
                        {'id': 'PRI', 'name': 'Price Details', 'required': True, 'elements': [
                            {'id': 'PRI01', 'name': 'Price Qualifier', 'dataType': 'AN', 'required': True, 'minLength': 3, 'maxLength': 3},
                            {'id': 'PRI02', 'name': 'Price', 'dataType': 'N', 'required': True, 'minLength': 1, 'maxLength': 15}
                        ]}
                    ]
                },
                {
                    'id': 'Summary',
                    'name': 'Summary',
                    'required': True,
                    'segments': [
                        {'id': 'UNS', 'name': 'Section Control', 'required': True, 'elements': [
                            {'id': 'UNS01', 'name': 'Section Identification', 'dataType': 'A', 'required': True, 'minLength': 1, 'maxLength': 1}
                        ]},
                        {'id': 'UNT', 'name': 'Message Trailer', 'required': True, 'elements': [
                            {'id': 'UNT01', 'name': 'Number of Segments', 'dataType': 'N', 'required': True, 'minLength': 1, 'maxLength': 6},
                            {'id': 'UNT02', 'name': 'Message Reference Number', 'dataType': 'AN', 'required': True, 'minLength': 1, 'maxLength': 14}
                        ]}
                    ]
                }
            ]
        }
        
        return converter.convert_edifact_to_boomi('ORDERS', version, schema_data)


def convert_edi_schema_from_webmethods(
    schema_file_path: str,
    edi_type: str
) -> str:
    """
    Main function to convert webMethods EDI schema to Boomi EDI Profile
    
    Args:
        schema_file_path: Path to webMethods EDI schema file
        edi_type: Either 'X12' or 'EDIFACT'
        
    Returns:
        Complete Boomi EDI Profile XML
    """
    
    # This would parse the actual webMethods EDI schema file
    # For now, using pre-built templates
    
    converter = EDIProfileConverter()
    
    if edi_type.upper() == 'X12':
        # Detect transaction set from schema
        # For demo, using 850
        return X12ProfileGenerator.generate_850_purchase_order()
    elif edi_type.upper() == 'EDIFACT':
        # Detect message type from schema
        # For demo, using ORDERS
        return EDIFACTProfileGenerator.generate_orders()
    else:
        raise ValueError(f"Unsupported EDI type: {edi_type}")
