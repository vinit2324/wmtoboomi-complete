"""
Analysis service for complexity scoring and dependency analysis.
"""
import networkx as nx
from typing import List, Dict, Tuple
from collections import defaultdict

from app.models import (
    ParsedData,
    ParsedService,
    AnalysisResults,
    DependencyInfo,
    ComplexityAnalysis,
    MigrationWave,
    FlowVerbStats,
)


class AnalysisService:
    """Service for analyzing parsed webMethods packages."""
    
    # Complexity weights
    VERB_WEIGHTS = {
        'map': 1,
        'branch': 2,
        'loop': 3,
        'repeat': 3,
        'sequence': 1,
        'tryCatch': 2,
        'tryFinally': 2,
        'catch': 1,
        'finally': 1,
        'exit': 1,
    }
    
    # Automation levels by component type
    AUTOMATION_LEVELS = {
        'DocumentType': 0.95,
        'FlowService_simple': 0.90,
        'FlowService_medium': 0.70,
        'FlowService_complex': 0.50,
        'MapService': 0.85,
        'AdapterService_simple': 0.80,
        'AdapterService_complex': 0.50,
        'JavaService': 0.20,
    }
    
    @staticmethod
    def analyze(parsed_data: ParsedData) -> AnalysisResults:
        """Perform full analysis on parsed data."""
        # Build dependency graph
        dependencies = AnalysisService._build_dependencies(parsed_data)
        
        # Calculate complexity
        complexity = AnalysisService._calculate_complexity(parsed_data)
        
        # Calculate estimated hours
        estimated_hours = AnalysisService._estimate_hours(parsed_data, complexity)
        
        # Generate migration waves
        migration_waves = AnalysisService._generate_waves(parsed_data, dependencies)
        
        # Calculate automation potential
        automation_potential = AnalysisService._calculate_automation(parsed_data)
        
        # Aggregate wMPublic services
        wm_public_services = AnalysisService._aggregate_wm_public(parsed_data)
        
        return AnalysisResults(
            dependencies=dependencies,
            complexity=complexity,
            estimatedHours=estimated_hours,
            migrationWaves=migration_waves,
            automationPotential=automation_potential,
            wMPublicServices=wm_public_services
        )
    
    @staticmethod
    def _build_dependencies(parsed_data: ParsedData) -> List[DependencyInfo]:
        """Build service dependency graph."""
        # Create dependency mapping
        service_names = {svc.name for svc in parsed_data.services}
        depends_on = defaultdict(list)
        depended_by = defaultdict(list)
        
        for service in parsed_data.services:
            if service.serviceInvocations:
                for inv in service.serviceInvocations:
                    # Check if this is an internal service reference
                    target = f"{inv.package}:{inv.service}"
                    # Also check just the service name
                    for svc_name in service_names:
                        if inv.service in svc_name or target in svc_name:
                            depends_on[service.name].append(svc_name)
                            depended_by[svc_name].append(service.name)
                            break
        
        dependencies = []
        for service in parsed_data.services:
            dependencies.append(DependencyInfo(
                serviceName=service.name,
                dependsOn=list(set(depends_on.get(service.name, []))),
                dependedBy=list(set(depended_by.get(service.name, [])))
            ))
        
        return dependencies
    
    @staticmethod
    def _calculate_complexity(parsed_data: ParsedData) -> ComplexityAnalysis:
        """Calculate overall complexity analysis."""
        total_score = 0.0
        factors = {
            'flowVerbScore': 0,
            'serviceInvocations': 0,
            'adapterComplexity': 0,
            'nestingDepth': 0,
            'javaServices': 0,
        }
        
        for service in parsed_data.services:
            # Flow verb complexity
            if service.flowVerbs:
                verb_score = (
                    service.flowVerbs.map * AnalysisService.VERB_WEIGHTS['map'] +
                    service.flowVerbs.branch * AnalysisService.VERB_WEIGHTS['branch'] +
                    service.flowVerbs.loop * AnalysisService.VERB_WEIGHTS['loop'] +
                    service.flowVerbs.repeat * AnalysisService.VERB_WEIGHTS['repeat'] +
                    service.flowVerbs.sequence * AnalysisService.VERB_WEIGHTS['sequence'] +
                    service.flowVerbs.tryCatch * AnalysisService.VERB_WEIGHTS['tryCatch'] +
                    service.flowVerbs.exit * AnalysisService.VERB_WEIGHTS['exit']
                )
                factors['flowVerbScore'] += verb_score
            
            # Service invocations
            if service.serviceInvocations:
                factors['serviceInvocations'] += sum(inv.count for inv in service.serviceInvocations)
            
            # Adapter complexity
            if service.adapters:
                for adapter in service.adapters:
                    if adapter in ['JDBC', 'SAP']:
                        factors['adapterComplexity'] += 3
                    else:
                        factors['adapterComplexity'] += 1
            
            # Java services
            if service.type == 'JavaService':
                factors['javaServices'] += 5
        
        # Calculate total score
        total_score = (
            factors['flowVerbScore'] * 0.3 +
            factors['serviceInvocations'] * 0.25 +
            factors['adapterComplexity'] * 0.2 +
            factors['javaServices'] * 0.25
        )
        
        # Normalize and determine level
        service_count = len(parsed_data.services) or 1
        normalized_score = total_score / service_count
        
        if normalized_score < 10:
            level = "low"
        elif normalized_score < 30:
            level = "medium"
        else:
            level = "high"
        
        return ComplexityAnalysis(
            overall=level,
            score=round(total_score, 2),
            factors=factors
        )
    
    @staticmethod
    def _estimate_hours(parsed_data: ParsedData, complexity: ComplexityAnalysis) -> float:
        """Estimate migration hours."""
        # Base hours calculation
        flow_count = sum(1 for s in parsed_data.services if s.type == 'FlowService')
        adapter_count = sum(1 for s in parsed_data.services if s.type == 'AdapterService')
        java_count = sum(1 for s in parsed_data.services if s.type == 'JavaService')
        doc_count = len(parsed_data.documents)
        
        base_hours = (
            flow_count * 4 +
            adapter_count * 6 +
            java_count * 8 +
            doc_count * 2
        )
        
        # Complexity multiplier
        complexity_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }
        multiplier = complexity_multipliers.get(complexity.overall, 1.0)
        
        # wMPublic factor
        wm_public_count = sum(
            inv.count 
            for svc in parsed_data.services 
            for inv in svc.serviceInvocations
            if inv.package.startswith(('pub.', 'wm.'))
        )
        wm_public_factor = (wm_public_count / 100) * 0.5
        
        total_hours = (base_hours * multiplier) + wm_public_factor
        
        return round(total_hours, 1)
    
    @staticmethod
    def _generate_waves(parsed_data: ParsedData, dependencies: List[DependencyInfo]) -> List[MigrationWave]:
        """Generate migration waves based on dependencies."""
        # Build dependency graph
        G = nx.DiGraph()
        
        for svc in parsed_data.services:
            G.add_node(svc.name)
        
        for dep in dependencies:
            for depends_on in dep.dependsOn:
                if depends_on in G:
                    G.add_edge(dep.serviceName, depends_on)
        
        # Check for cycles and handle them
        try:
            if not nx.is_directed_acyclic_graph(G):
                # Remove cycles by finding and breaking them
                cycles = list(nx.simple_cycles(G))
                for cycle in cycles:
                    if len(cycle) > 1:
                        G.remove_edge(cycle[0], cycle[1])
        except:
            pass
        
        # Generate waves using topological generations
        waves = []
        try:
            generations = list(nx.topological_generations(G))
            
            for i, gen in enumerate(generations):
                services = list(gen)
                
                # Calculate estimated hours for wave
                wave_hours = sum(
                    4 if any(s.name == svc and s.type == 'FlowService' for s in parsed_data.services) else
                    6 if any(s.name == svc and s.type == 'AdapterService' for s in parsed_data.services) else
                    8 if any(s.name == svc and s.type == 'JavaService' for s in parsed_data.services) else 2
                    for svc in services
                )
                
                # Get dependencies for this wave
                wave_deps = []
                for svc in services:
                    for dep in dependencies:
                        if dep.serviceName == svc:
                            wave_deps.extend(dep.dependsOn)
                
                waves.append(MigrationWave(
                    waveNumber=i + 1,
                    services=services,
                    estimatedHours=wave_hours,
                    dependencies=list(set(wave_deps))
                ))
        except:
            # If topological sort fails, put all in one wave
            waves.append(MigrationWave(
                waveNumber=1,
                services=[svc.name for svc in parsed_data.services],
                estimatedHours=sum(4 for _ in parsed_data.services),
                dependencies=[]
            ))
        
        return waves
    
    @staticmethod
    def _calculate_automation(parsed_data: ParsedData) -> str:
        """Calculate automation potential percentage."""
        total_components = len(parsed_data.services) + len(parsed_data.documents)
        if total_components == 0:
            return "0%"
        
        automation_score = 0.0
        
        # Documents - 95% automation
        automation_score += len(parsed_data.documents) * 0.95
        
        for service in parsed_data.services:
            if service.type == 'DocumentType':
                automation_score += 0.95
            elif service.type == 'FlowService':
                # Determine flow complexity
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
                    
                    if total_verbs < 10:
                        automation_score += 0.90  # Simple
                    elif total_verbs < 30:
                        automation_score += 0.70  # Medium
                    else:
                        automation_score += 0.50  # Complex
                else:
                    automation_score += 0.80  # Unknown, assume medium
                    
            elif service.type == 'MapService':
                automation_score += 0.85
            elif service.type == 'AdapterService':
                # Check for JDBC complexity
                if 'JDBC' in service.adapters:
                    automation_score += 0.50  # Conservative for JDBC
                else:
                    automation_score += 0.80
            elif service.type == 'JavaService':
                automation_score += 0.20  # Low automation for Java
        
        percentage = (automation_score / total_components) * 100
        return f"{int(round(percentage))}%"
    
    @staticmethod
    def _aggregate_wm_public(parsed_data: ParsedData) -> Dict[str, int]:
        """Aggregate wMPublic service usage."""
        wm_public = {}
        
        for service in parsed_data.services:
            if service.serviceInvocations:
                for inv in service.serviceInvocations:
                    if inv.package.startswith(('pub.', 'wm.', 'pub:', 'wm:')):
                        key = f"{inv.package}:{inv.service}" if ':' not in inv.service else inv.service
                        wm_public[key] = wm_public.get(key, 0) + inv.count
        
        # Sort by count descending
        return dict(sorted(wm_public.items(), key=lambda x: x[1], reverse=True))
