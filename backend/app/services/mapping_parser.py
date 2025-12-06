"""
Mapping Parser - Extracts field-to-field mappings from webMethods flow.xml

Parses MAP steps to extract:
- Source field → Target field mappings
- Transformation types (COPY, CONCAT, SUBSTRING, etc.)
- Nested field mappings
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MappingParser:
    """Parse webMethods MAP steps to extract field mappings"""
    
    # Transformation types in webMethods
    TRANSFORM_TYPES = {
        'MAPCOPY': 'COPY',
        'MAPCONCAT': 'CONCAT',
        'MAPSUBSTRING': 'SUBSTRING',
        'MAPLOOKUP': 'LOOKUP',
        'MAPDELETE': 'DELETE',
        'MAPSET': 'SET',
        'MAPSETVAR': 'SET_VARIABLE',
        'MAPINVOKE': 'INVOKE',
        'MAPCONDITION': 'CONDITIONAL',
        'MAPDATE': 'DATE_FORMAT',
        'MAPNUMBER': 'NUMBER_FORMAT',
    }

    @staticmethod
    def parse_flow_mappings(flow_xml: str) -> List[Dict[str, Any]]:
        """
        Parse all MAP steps from flow.xml and extract mappings.
        
        Args:
            flow_xml: Raw XML content of flow.xml
            
        Returns:
            List of map definitions with field mappings
        """
        maps = []
        
        if not flow_xml:
            return maps
        
        try:
            # Clean XML
            flow_xml = MappingParser._clean_xml(flow_xml)
            root = ET.fromstring(flow_xml)
            
            # Find all MAP elements
            map_elements = root.findall('.//MAP') + root.findall('.//map')
            
            for map_elem in map_elements:
                map_def = MappingParser._parse_map_element(map_elem)
                if map_def and map_def.get('mappings'):
                    maps.append(map_def)
            
            # Also look for INVOKE steps that might contain inline mappings
            invoke_elements = root.findall('.//INVOKE') + root.findall('.//invoke')
            for invoke_elem in invoke_elements:
                inline_maps = MappingParser._parse_invoke_mappings(invoke_elem)
                if inline_maps:
                    maps.extend(inline_maps)
                    
        except ET.ParseError as e:
            logger.error(f"Failed to parse flow.xml: {e}")
        except Exception as e:
            logger.error(f"Error parsing mappings: {e}")
        
        return maps
    
    @staticmethod
    def _clean_xml(xml_content: str) -> str:
        """Clean XML content for parsing"""
        # Remove BOM and clean whitespace
        xml_content = xml_content.strip()
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]
        return xml_content
    
    @staticmethod
    def _parse_map_element(map_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single MAP element"""
        map_name = map_elem.get('NAME') or map_elem.get('name') or 'UnnamedMap'
        
        mappings = []
        source_profile = None
        target_profile = None
        
        # Find MAPTARGET (contains the actual mappings)
        maptarget = map_elem.find('.//MAPTARGET') or map_elem.find('.//maptarget')
        if maptarget is None:
            maptarget = map_elem
        
        # Find MAPSOURCE for source profile info
        mapsource = map_elem.find('.//MAPSOURCE') or map_elem.find('.//mapsource')
        if mapsource is not None:
            source_profile = MappingParser._extract_profile_name(mapsource)
        
        # Extract target profile from MAPTARGET
        target_profile = MappingParser._extract_profile_name(maptarget)
        
        # Parse all MAPITEM elements (each represents a target field mapping)
        mapitems = maptarget.findall('.//MAPITEM') or maptarget.findall('.//mapitem')
        
        for item in mapitems:
            mapping = MappingParser._parse_mapitem(item)
            if mapping:
                mappings.append(mapping)
        
        # Also parse direct MAPCOPY elements
        mapcopies = map_elem.findall('.//MAPCOPY') or map_elem.findall('.//mapcopy')
        for copy in mapcopies:
            mapping = MappingParser._parse_mapcopy(copy)
            if mapping:
                mappings.append(mapping)
        
        return {
            'name': map_name,
            'sourceProfile': source_profile,
            'targetProfile': target_profile,
            'mappings': mappings,
            'mappingCount': len(mappings)
        }
    
    @staticmethod
    def _parse_mapitem(item: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a MAPITEM element to extract field mapping"""
        # Get target field
        target_field = item.find('.//FIELD') or item.find('.//field')
        if target_field is None:
            return None
        
        target_name = target_field.get('name') or target_field.get('NAME') or ''
        target_type = target_field.get('type') or target_field.get('TYPE') or 'string'
        target_path = MappingParser._build_field_path(target_field)
        
        # Find the transformation/source
        transform_type = 'COPY'
        source_fields = []
        transform_details = None
        
        # Check for MAPCOPY (direct copy)
        mapcopy = item.find('.//MAPCOPY') or item.find('.//mapcopy')
        if mapcopy is not None:
            source_field = mapcopy.find('.//FIELD') or mapcopy.find('.//field')
            if source_field is not None:
                source_name = source_field.get('name') or source_field.get('NAME') or ''
                source_path = MappingParser._build_field_path(source_field)
                source_fields.append({
                    'name': source_name,
                    'path': source_path,
                    'type': source_field.get('type') or 'string'
                })
        
        # Check for MAPCONCAT (concatenation)
        mapconcat = item.find('.//MAPCONCAT') or item.find('.//mapconcat')
        if mapconcat is not None:
            transform_type = 'CONCAT'
            concat_fields = mapconcat.findall('.//FIELD') or mapconcat.findall('.//field')
            for cf in concat_fields:
                source_fields.append({
                    'name': cf.get('name') or cf.get('NAME') or '',
                    'path': MappingParser._build_field_path(cf),
                    'type': cf.get('type') or 'string'
                })
            # Get separator if present
            separator = mapconcat.get('separator') or mapconcat.get('SEPARATOR') or ''
            if separator:
                transform_details = f"Separator: '{separator}'"
        
        # Check for MAPSUBSTRING
        mapsubstr = item.find('.//MAPSUBSTRING') or item.find('.//mapsubstring')
        if mapsubstr is not None:
            transform_type = 'SUBSTRING'
            source_field = mapsubstr.find('.//FIELD') or mapsubstr.find('.//field')
            if source_field is not None:
                source_fields.append({
                    'name': source_field.get('name') or '',
                    'path': MappingParser._build_field_path(source_field),
                    'type': source_field.get('type') or 'string'
                })
            start = mapsubstr.get('startIndex') or mapsubstr.get('START') or '0'
            end = mapsubstr.get('endIndex') or mapsubstr.get('END') or ''
            transform_details = f"substring({start}, {end})"
        
        # Check for MAPSET (constant value)
        mapset = item.find('.//MAPSET') or item.find('.//mapset')
        if mapset is not None:
            transform_type = 'SET'
            value = mapset.get('value') or mapset.get('VALUE') or ''
            transform_details = f"Constant: '{value}'"
        
        # Check for MAPINVOKE (service call)
        mapinvoke = item.find('.//MAPINVOKE') or item.find('.//mapinvoke')
        if mapinvoke is not None:
            transform_type = 'INVOKE'
            service = mapinvoke.get('service') or mapinvoke.get('SERVICE') or ''
            transform_details = f"Service: {service}"
        
        # Check for MAPDATE (date formatting)
        mapdate = item.find('.//MAPDATE') or item.find('.//mapdate')
        if mapdate is not None:
            transform_type = 'DATE_FORMAT'
            source_field = mapdate.find('.//FIELD') or mapdate.find('.//field')
            if source_field is not None:
                source_fields.append({
                    'name': source_field.get('name') or '',
                    'path': MappingParser._build_field_path(source_field),
                    'type': 'date'
                })
            pattern = mapdate.get('pattern') or mapdate.get('PATTERN') or ''
            transform_details = f"Format: {pattern}"
        
        if not target_name:
            return None
        
        return {
            'targetField': target_name,
            'targetPath': target_path,
            'targetType': target_type,
            'sourceFields': source_fields,
            'transformationType': transform_type,
            'transformationDetails': transform_details
        }
    
    @staticmethod
    def _parse_mapcopy(copy_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a standalone MAPCOPY element"""
        fields = copy_elem.findall('.//FIELD') or copy_elem.findall('.//field')
        if len(fields) < 2:
            return None
        
        source_field = fields[0]
        target_field = fields[1] if len(fields) > 1 else fields[0]
        
        return {
            'targetField': target_field.get('name') or '',
            'targetPath': MappingParser._build_field_path(target_field),
            'targetType': target_field.get('type') or 'string',
            'sourceFields': [{
                'name': source_field.get('name') or '',
                'path': MappingParser._build_field_path(source_field),
                'type': source_field.get('type') or 'string'
            }],
            'transformationType': 'COPY',
            'transformationDetails': None
        }
    
    @staticmethod
    def _parse_invoke_mappings(invoke_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse mappings from INVOKE elements (input/output mappings)"""
        maps = []
        
        # Input mappings
        input_map = invoke_elem.find('.//MAP[@MODE="INPUT"]') or invoke_elem.find('.//map[@mode="input"]')
        if input_map is not None:
            map_def = MappingParser._parse_map_element(input_map)
            if map_def:
                map_def['name'] = f"{invoke_elem.get('SERVICE', 'invoke')}_input"
                map_def['direction'] = 'INPUT'
                maps.append(map_def)
        
        # Output mappings
        output_map = invoke_elem.find('.//MAP[@MODE="OUTPUT"]') or invoke_elem.find('.//map[@mode="output"]')
        if output_map is not None:
            map_def = MappingParser._parse_map_element(output_map)
            if map_def:
                map_def['name'] = f"{invoke_elem.get('SERVICE', 'invoke')}_output"
                map_def['direction'] = 'OUTPUT'
                maps.append(map_def)
        
        return maps
    
    @staticmethod
    def _build_field_path(field_elem: ET.Element) -> str:
        """Build full field path from element ancestry"""
        path_parts = []
        current = field_elem
        
        while current is not None:
            name = current.get('name') or current.get('NAME')
            if name and current.tag.upper() in ['FIELD', 'RECORD']:
                path_parts.insert(0, name)
            current = current.find('..')
        
        # Fallback to just the field name
        if not path_parts:
            name = field_elem.get('name') or field_elem.get('NAME') or ''
            path_parts = [name]
        
        return '/'.join(path_parts)
    
    @staticmethod
    def _extract_profile_name(elem: ET.Element) -> Optional[str]:
        """Extract document/profile name from element"""
        # Look for documentTypeName or similar attributes
        for attr in ['documentTypeName', 'documentType', 'docType', 'DOCUMENTTYPENAME']:
            if elem.get(attr):
                return elem.get(attr)
        
        # Look for nested document reference
        doc_ref = elem.find('.//DOCUMENT') or elem.find('.//document')
        if doc_ref is not None:
            return doc_ref.get('name') or doc_ref.get('NAME')
        
        return None
    
    @staticmethod
    def generate_auto_mappings(source_fields: List[Dict], target_fields: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate suggested auto-mappings based on field name similarity.
        Used when explicit mappings aren't available.
        """
        mappings = []
        used_targets = set()
        
        for source in source_fields:
            source_name = source.get('name', '').lower().replace('_', '').replace('-', '')
            best_match = None
            best_score = 0
            
            for target in target_fields:
                if target.get('name') in used_targets:
                    continue
                
                target_name = target.get('name', '').lower().replace('_', '').replace('-', '')
                
                # Exact match
                if source_name == target_name:
                    best_match = target
                    best_score = 100
                    break
                
                # Contains match
                if source_name in target_name or target_name in source_name:
                    score = 80
                    if score > best_score:
                        best_match = target
                        best_score = score
                
                # Partial match (common substrings)
                common_len = len(set(source_name) & set(target_name))
                score = (common_len / max(len(source_name), len(target_name))) * 60
                if score > best_score:
                    best_match = target
                    best_score = score
            
            if best_match and best_score >= 50:
                used_targets.add(best_match.get('name'))
                mappings.append({
                    'targetField': best_match.get('name'),
                    'targetPath': best_match.get('name'),
                    'targetType': best_match.get('type', 'string'),
                    'sourceFields': [{
                        'name': source.get('name'),
                        'path': source.get('name'),
                        'type': source.get('type', 'string')
                    }],
                    'transformationType': 'COPY',
                    'transformationDetails': None,
                    'confidence': best_score,
                    'autoGenerated': True
                })
        
        return mappings


def parse_service_mappings(flow_xml: str, source_doc: Dict = None, target_doc: Dict = None) -> Dict[str, Any]:
    """
    Main entry point - parse mappings from a flow service.
    Falls back to auto-generated mappings if none found.
    """
    parser = MappingParser()
    
    # Try to parse explicit mappings
    maps = parser.parse_flow_mappings(flow_xml)
    
    # If no explicit mappings found, generate suggestions
    if not maps and source_doc and target_doc:
        source_fields = source_doc.get('fields', [])
        target_fields = target_doc.get('fields', [])
        
        auto_mappings = parser.generate_auto_mappings(source_fields, target_fields)
        
        if auto_mappings:
            maps = [{
                'name': f"{source_doc.get('name', 'Source')} → {target_doc.get('name', 'Target')}",
                'sourceProfile': source_doc.get('name'),
                'targetProfile': target_doc.get('name'),
                'mappings': auto_mappings,
                'mappingCount': len(auto_mappings),
                'autoGenerated': True
            }]
    
    return {
        'maps': maps,
        'totalMappings': sum(m.get('mappingCount', 0) for m in maps)
    }
