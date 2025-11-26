"""
Integration Pattern Analyzer - Groups related services into complete integration flows
"""

from typing import Dict, List, Any
import re

class IntegrationAnalyzer:
    """Analyze and group services into integration patterns"""
    
    @staticmethod
    def analyze_integrations(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze services and group into integration patterns"""
        
        services = parsed_data.get('services', [])
        documents = parsed_data.get('documents', [])
        dependencies = parsed_data.get('dependencies', [])
        
        # Build dependency graph
        dependency_map = {}
        for dep in dependencies:
            source = dep['from']
            target = dep['to']
            if source not in dependency_map:
                dependency_map[source] = []
            dependency_map[source].append(target)
        
        # Identify integration patterns by analyzing service paths and names
        integrations = IntegrationAnalyzer._identify_integrations(services, dependency_map)
        
        # Generate implementation steps for each integration
        for integration in integrations:
            integration['boomiSteps'] = IntegrationAnalyzer._generate_boomi_steps(
                integration, services, documents
            )
        
        return {
            'integrations': integrations,
            'totalIntegrations': len(integrations),
            'dependencies': dependencies
        }
    
    @staticmethod
    def _identify_integrations(services: List[Dict], dependency_map: Dict) -> List[Dict]:
        """Identify integration patterns"""
        
        integrations = []
        processed = set()
        
        # Group by functional area (from path structure)
        functional_groups = {}
        for service in services:
            path_parts = service['name'].split('/')
            
            # Extract functional area (e.g., NS/enterprise/b2b/inbound)
            if len(path_parts) >= 4:
                functional_area = '/'.join(path_parts[:4])
            else:
                functional_area = '/'.join(path_parts[:-1])
            
            if functional_area not in functional_groups:
                functional_groups[functional_area] = []
            functional_groups[functional_area].append(service)
        
        # Create integrations from functional groups
        for area, area_services in functional_groups.items():
            if not area_services:
                continue
            
            integration = {
                'name': IntegrationAnalyzer._generate_integration_name(area),
                'functionalArea': area,
                'services': [],
                'documents': [],
                'adapters': [],
                'complexity': 'medium',
                'automationLevel': '80%',
                'estimatedHours': 0
            }
            
            total_steps = 0
            for svc in area_services:
                integration['services'].append({
                    'name': svc['name'],
                    'type': svc['type'],
                    'complexity': svc.get('complexity', 'low'),
                    'steps': len(svc.get('flowSteps', [])),
                    'dependencies': dependency_map.get(svc['name'], [])
                })
                total_steps += len(svc.get('flowSteps', []))
                
                # Track adapters
                if svc['type'] == 'AdapterService':
                    adapter_type = svc.get('adapterType', 'Unknown')
                    if adapter_type not in integration['adapters']:
                        integration['adapters'].append(adapter_type)
            
            # Calculate complexity and estimate
            integration['complexity'] = 'low' if total_steps < 20 else 'medium' if total_steps < 50 else 'high'
            integration['estimatedHours'] = len(area_services) * 4 + len(integration['adapters']) * 2
            
            integrations.append(integration)
        
        return integrations
    
    @staticmethod
    def _generate_integration_name(path: str) -> str:
        """Generate friendly integration name from path"""
        
        parts = path.split('/')
        if len(parts) >= 4:
            # e.g., NS/enterprise/b2b/inbound -> "B2B Inbound Integration"
            return ' '.join(parts[2:]).title() + " Integration"
        return "Integration"
    
    @staticmethod
    def _generate_boomi_steps(integration: Dict, all_services: List[Dict], all_documents: List[Dict]) -> List[Dict]:
        """Generate step-by-step Boomi implementation guide"""
        
        steps = []
        step_num = 1
        
        # Step 1: Create Connectors for adapters
        if integration['adapters']:
            for adapter in integration['adapters']:
                steps.append({
                    'stepNumber': step_num,
                    'category': 'Connector Setup',
                    'title': f'Create {adapter} Connector',
                    'description': f'Set up Boomi {adapter} connector with connection parameters',
                    'boomiComponent': 'Connector',
                    'automationLevel': '50%',
                    'tasks': [
                        f'Navigate to Build → Connectors',
                        f'Create new {adapter} Connector',
                        'Configure connection properties (host, port, credentials)',
                        'Test connection',
                        'Save connector'
                    ]
                })
                step_num += 1
        
        # Step 2: Create Source Profiles
        source_docs = IntegrationAnalyzer._identify_source_documents(integration, all_documents)
        for doc in source_docs:
            steps.append({
                'stepNumber': step_num,
                'category': 'Profile Creation',
                'title': f'Create Source Profile: {doc["name"].split("/")[-1]}',
                'description': f'Convert webMethods Document Type to Boomi Profile',
                'boomiComponent': 'Profile (XML/JSON/EDI)',
                'automationLevel': '90%',
                'tasks': [
                    'Navigate to Build → Profiles',
                    'Create new XML/JSON/EDI Profile',
                    f'Define schema with {len(doc.get("fields", []))} fields',
                    'Set namespace and root element',
                    'Validate profile structure',
                    'Save profile'
                ]
            })
            step_num += 1
        
        # Step 3: Create Target Profiles
        target_docs = IntegrationAnalyzer._identify_target_documents(integration, all_documents)
        for doc in target_docs:
            steps.append({
                'stepNumber': step_num,
                'category': 'Profile Creation',
                'title': f'Create Target Profile: {doc["name"].split("/")[-1]}',
                'description': f'Convert webMethods Document Type to Boomi Profile',
                'boomiComponent': 'Profile (XML/JSON/EDI)',
                'automationLevel': '90%',
                'tasks': [
                    'Navigate to Build → Profiles',
                    'Create new XML/JSON/EDI Profile',
                    f'Define schema with {len(doc.get("fields", []))} fields',
                    'Set namespace and root element',
                    'Validate profile structure',
                    'Save profile'
                ]
            })
            step_num += 1
        
        # Step 4: Create Maps
        if source_docs and target_docs:
            steps.append({
                'stepNumber': step_num,
                'category': 'Mapping',
                'title': 'Create Field Mappings',
                'description': 'Map fields from source to target profiles',
                'boomiComponent': 'Map',
                'automationLevel': '70%',
                'tasks': [
                    'Navigate to Build → Maps',
                    'Create new Map',
                    'Select source and target profiles',
                    'Map common fields automatically',
                    'Add transformations (date formats, lookups, etc.)',
                    'Add custom functions if needed',
                    'Test map with sample data',
                    'Save map'
                ]
            })
            step_num += 1
        
        # Step 5: Create Process for each service
        for svc in integration['services']:
            if svc['type'] == 'FlowService':
                steps.append({
                    'stepNumber': step_num,
                    'category': 'Process Creation',
                    'title': f'Create Process: {svc["name"].split("/")[-1]}',
                    'description': f'Convert webMethods Flow Service to Boomi Process ({svc["steps"]} steps)',
                    'boomiComponent': 'Process',
                    'automationLevel': '85%',
                    'tasks': [
                        'Navigate to Build → Processes',
                        'Create new Process',
                        'Add Start shape',
                        f'Convert {svc["steps"]} flow steps to Boomi shapes',
                        'Connect to connectors and profiles',
                        'Add error handling (Try-Catch)',
                        'Configure process properties',
                        'Test process',
                        'Save process'
                    ]
                })
                step_num += 1
        
        # Step 6: Testing
        steps.append({
            'stepNumber': step_num,
            'category': 'Testing',
            'title': 'Integration Testing',
            'description': 'End-to-end testing of complete integration',
            'boomiComponent': 'Process',
            'automationLevel': '30%',
            'tasks': [
                'Deploy to Test environment',
                'Test with sample data',
                'Verify data transformations',
                'Test error scenarios',
                'Validate against requirements',
                'Fix any issues',
                'Document test results'
            ]
        })
        step_num += 1
        
        # Step 7: Deployment
        steps.append({
            'stepNumber': step_num,
            'category': 'Deployment',
            'title': 'Production Deployment',
            'description': 'Deploy integration to production',
            'boomiComponent': 'Environment',
            'automationLevel': '50%',
            'tasks': [
                'Create deployment package',
                'Deploy to Production atom',
                'Configure production connections',
                'Enable monitoring and alerts',
                'Document deployment',
                'Handoff to operations team'
            ]
        })
        
        return steps
    
    @staticmethod
    def _identify_source_documents(integration: Dict, all_documents: List[Dict]) -> List[Dict]:
        """Identify source documents for this integration"""
        # Simplified - return related documents
        return [doc for doc in all_documents if any(
            svc['name'].split('/')[:-1] == doc['name'].split('/')[:-1] 
            for svc in integration['services']
        )][:2]
    
    @staticmethod
    def _identify_target_documents(integration: Dict, all_documents: List[Dict]) -> List[Dict]:
        """Identify target documents for this integration"""
        # Simplified - return related documents
        return [doc for doc in all_documents if any(
            svc['name'].split('/')[:-1] == doc['name'].split('/')[:-1] 
            for svc in integration['services']
        )][:2]


def analyze_integrations(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point"""
    analyzer = IntegrationAnalyzer()
    return analyzer.analyze_integrations(parsed_data)
