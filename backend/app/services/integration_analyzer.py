"""
Integration Pattern Analyzer - Groups related services into complete integration flows
"""

from typing import Dict, List, Any, Set, Tuple


class IntegrationAnalyzer:
    """Analyze and group services into integration patterns"""
    
    DOMAIN_DOCUMENT_MAP = {
        'b2b': ['order', 'invoice', 'shipment', 'asn', 'edi', '850', '810', '856', 'customer', 'canonical'],
        'edi': ['edi', '850', '810', '856', '997', '940', '945'],
        'inbound': ['order', '850', 'purchase', 'request', 'receive', 'canonical', 'customer'],
        'outbound': ['invoice', 'shipment', 'asn', '856', '810', 'response', 'send'],
        'crm': ['customer', 'account', 'opportunity', 'contact', 'sfdc', 'salesforce', 'master'],
        'sfdc': ['customer', 'account', 'opportunity', 'sfdc', 'salesforce'],
        'erp': ['order', 'invoice', 'material', 'inventory', 'sap', 'idoc', 'sales'],
        'sap': ['idoc', 'material', 'order', 'invoice', 'sap', 'bapi', 'canonical'],
        'finance': ['invoice', 'payment', 'cash', 'gl', 'ar', 'ap'],
        'payment': ['payment', 'batch', 'cash', 'invoice'],
        'hls': ['hl7', 'adt', 'fhir', 'patient', 'clinical'],
        'hl7': ['hl7', 'adt', 'patient', 'clinical'],
        'logistics': ['shipment', 'carrier', 'tracking', 'warehouse', 'asn'],
        'orchestration': ['order', 'invoice', 'payment', 'shipment', 'canonical'],
    }
    
    SOURCE_DOC_PATTERNS = ['request', 'input', 'inbound', '850', 'order', 'receive', 'master', 'customer']
    TARGET_DOC_PATTERNS = ['response', 'output', 'outbound', '810', '856', 'invoice', 'shipment', 'send']
    
    ADAPTER_PATTERNS = {
        'sfdc': 'Salesforce', 'salesforce': 'Salesforce', 'pub.sfdc': 'Salesforce',
        'sap': 'SAP', 'idoc': 'SAP', 'bapi': 'SAP', 'pub.sap': 'SAP',
        'jdbc': 'Database', 'pub.db': 'Database', 'pub.jdbc': 'Database',
        'http': 'HTTP Client', 'pub.client:http': 'HTTP Client', 'rest': 'HTTP Client',
        'jms': 'JMS', 'pub.jms': 'JMS',
        'ftp': 'FTP', 'sftp': 'SFTP', 'pub.ftp': 'FTP',
        'edi': 'EDI', 'pub.edi': 'EDI', 'wm.b2b.edi': 'EDI',
        'as2': 'AS2', 'hl7': 'HL7',
    }

    @staticmethod
    def analyze_integrations(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point - analyze services and group into integration patterns.
        Returns dict with 'integrations' key for frontend compatibility.
        """
        services = parsed_data.get('services', [])
        documents = parsed_data.get('documents', [])
        
        if not services:
            return {'integrations': [], 'totalIntegrations': 0}
        
        # Group services by functional area
        service_groups: Dict[str, List[Dict]] = {}
        for service in services:
            service_path = service.get('name', '') or service.get('path', '')
            area = IntegrationAnalyzer._get_functional_area(service_path)
            if area not in service_groups:
                service_groups[area] = []
            service_groups[area].append(service)
        
        integrations = []
        for area, group_services in service_groups.items():
            total_steps = sum(s.get('stepCount', 0) or len(s.get('flowSteps', [])) for s in group_services)
            
            # Count verbs
            verb_counts = {}
            for svc in group_services:
                for step in svc.get('flowSteps', []):
                    verb = step.get('type', 'UNKNOWN')
                    verb_counts[verb] = verb_counts.get(verb, 0) + 1
            
            # Determine complexity
            if total_steps <= 10:
                complexity, automation, estimated_hours = 'low', '90%', 2
            elif total_steps <= 25:
                complexity, automation, estimated_hours = 'medium', '80%', 4
            else:
                complexity, automation, estimated_hours = 'high', '70%', 6
            
            # Detect adapters
            adapters = IntegrationAnalyzer._detect_adapters(group_services, area)
            
            # Find relevant documents
            source_docs, target_docs = IntegrationAnalyzer._find_relevant_documents(area, documents)
            
            integration = {
                'name': IntegrationAnalyzer._generate_integration_name(area),
                'functionalArea': area,
                'services': group_services,
                'serviceCount': len(group_services),
                'adapters': list(adapters),
                'complexity': complexity,
                'automation': automation,
                'automationLevel': automation,
                'estimatedHours': estimated_hours,
                'verbCounts': verb_counts,
                'totalSteps': total_steps,
                'sourceDocuments': source_docs,
                'targetDocuments': target_docs
            }
            integrations.append(integration)
        
        return {
            'integrations': integrations,
            'totalIntegrations': len(integrations)
        }
    
    @staticmethod
    def _detect_adapters(services: List[Dict], functional_area: str) -> Set[str]:
        """Detect adapters/connectors from services and functional area."""
        adapters = set()
        
        for svc in services:
            # Check explicit adapters
            if svc.get('adapters'):
                for adapter in svc['adapters']:
                    adapters.add(adapter)
            
            # Check adapter service type
            if svc.get('type') == 'AdapterService':
                adapters.add(svc.get('adapterType', 'Unknown'))
            
            # Check flow steps for service invocations
            for step in svc.get('flowSteps', []):
                step_name = (step.get('name', '') or '').lower()
                for pattern, adapter_name in IntegrationAnalyzer.ADAPTER_PATTERNS.items():
                    if pattern in step_name:
                        adapters.add(adapter_name)
            
            # Check invocations
            for inv in svc.get('invocations', []):
                inv_name = (inv.get('service', '') if isinstance(inv, dict) else str(inv)).lower()
                for pattern, adapter_name in IntegrationAnalyzer.ADAPTER_PATTERNS.items():
                    if pattern in inv_name:
                        adapters.add(adapter_name)
        
        # Infer from functional area
        area_lower = functional_area.lower()
        area_adapters = {
            'sfdc': 'Salesforce', 'crm': 'Salesforce', 'salesforce': 'Salesforce',
            'sap': 'SAP', 'erp': 'SAP', 'idoc': 'SAP',
            'edi': 'EDI', 'b2b': 'EDI',
            'hl7': 'HL7', 'hls': 'HL7',
            'jdbc': 'Database', 'db': 'Database',
            'jms': 'JMS', 'ftp': 'FTP', 'sftp': 'SFTP',
            'http': 'HTTP Client', 'api': 'HTTP Client',
        }
        for keyword, adapter_name in area_adapters.items():
            if keyword in area_lower:
                adapters.add(adapter_name)
        
        return adapters
    
    @staticmethod
    def _get_functional_area(service_path: str) -> str:
        """Extract functional area from service path."""
        if not service_path:
            return 'unknown'
        path = service_path.replace('\\', '/')
        parts = [p for p in path.split('/') if p and p.lower() not in ['ns', 'pub', 'wm']]
        if len(parts) >= 3:
            return '/'.join(parts[:3])
        elif len(parts) >= 2:
            return '/'.join(parts[:2])
        elif parts:
            return parts[0]
        return 'unknown'
    
    @staticmethod
    def _generate_integration_name(path: str) -> str:
        """Generate friendly integration name from path."""
        parts = path.split('/')
        if len(parts) >= 3:
            return ' '.join(parts[1:]).title().replace('_', ' ') + " Integration"
        elif len(parts) >= 2:
            return ' '.join(parts).title().replace('_', ' ') + " Integration"
        return path.title().replace('_', ' ') + " Integration"
    
    @staticmethod
    def _find_relevant_documents(functional_area: str, all_documents: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Find documents relevant to an integration based on domain matching."""
        source_docs, target_docs = [], []
        if not all_documents:
            return source_docs, target_docs
        
        area_lower = functional_area.lower()
        path_parts = area_lower.replace('/', ' ').replace('_', ' ').split()
        
        # Build relevant keywords
        relevant_keywords: Set[str] = set()
        for part in path_parts:
            if part in ['ns', 'enterprise', 'pub']:
                continue
            relevant_keywords.add(part)
            if part in IntegrationAnalyzer.DOMAIN_DOCUMENT_MAP:
                relevant_keywords.update(IntegrationAnalyzer.DOMAIN_DOCUMENT_MAP[part])
        
        for doc in all_documents:
            doc_name = doc.get('name', '')
            doc_simple = doc_name.split('/')[-1].lower().replace('_', '')
            doc_path = doc_name.lower()
            
            # Check relevance
            relevance = sum(1 for kw in relevant_keywords if kw in doc_simple or kw in doc_path)
            for part in path_parts:
                if part not in ['ns', 'enterprise', 'pub'] and part in doc_path:
                    relevance += 2
            
            if relevance > 0:
                is_source = any(p in doc_simple for p in IntegrationAnalyzer.SOURCE_DOC_PATTERNS)
                is_target = any(p in doc_simple for p in IntegrationAnalyzer.TARGET_DOC_PATTERNS)
                
                if is_source and not is_target:
                    source_docs.append(doc)
                elif is_target and not is_source:
                    target_docs.append(doc)
                elif any(x in doc_simple for x in ['850', 'order', 'master', 'customer']):
                    source_docs.append(doc)
                else:
                    target_docs.append(doc)
        
        return source_docs, target_docs


# MAIN EXPORT FUNCTION - matches how router calls it
def analyze_integrations(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point called by router."""
    return IntegrationAnalyzer.analyze_integrations(parsed_data)
