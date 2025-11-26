"""
Deep Parser Engine - Part 2
Flow.xml parser with complete pipeline state tracking

Parses the 9 flow verbs and all service invocations,
tracking pipeline state through the entire flow.
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from lxml import etree
import logging

from app.services.deep_parser_core import (
    FlowVerb, FlowStep, BranchCase, ServiceInvocation,
    PipelineVariable, ParsedService, ServiceType
)
from app.services.wmpublic_master import get_catalog, lookup_service

logger = logging.getLogger(__name__)


# =============================================================================
# FLOW.XML PARSER
# =============================================================================

class FlowXMLParser:
    """
    Parser for webMethods flow.xml files.
    
    Extracts:
    - All 9 flow verbs (MAP, BRANCH, LOOP, REPEAT, SEQUENCE, etc.)
    - Service invocations (wMPublic, custom, adapter)
    - Pipeline state tracking
    - Transformer expressions
    - Link criteria
    """
    
    # Flow verb tag mappings
    VERB_TAGS = {
        'map': FlowVerb.MAP,
        'branch': FlowVerb.BRANCH,
        'loop': FlowVerb.LOOP,
        'repeat': FlowVerb.REPEAT,
        'sequence': FlowVerb.SEQUENCE,
        'invoke': FlowVerb.INVOKE,
        'exit': FlowVerb.EXIT,
        'flow': FlowVerb.SEQUENCE,  # flow element is like sequence
    }
    
    # Tags that indicate try/catch/finally
    TRY_CATCH_TAGS = {
        'try': FlowVerb.TRY,
        'catch': FlowVerb.CATCH,
        'finally': FlowVerb.FINALLY,
    }
    
    def __init__(self):
        self.wmpublic_catalog = get_catalog()
        self.current_line = 0
        
    def parse(self, content: str) -> Tuple[List[FlowStep], Dict[str, int]]:
        """
        Parse flow.xml content.
        Returns (list of flow steps, verb counts)
        """
        try:
            # Clean content
            content = self._clean_xml_content(content)
            
            # Parse XML
            root = etree.fromstring(content.encode('utf-8'))
            
            # Extract flow steps
            steps = self._parse_element(root)
            
            # Count verbs
            verb_counts = self._count_verbs(steps)
            
            return steps, verb_counts
            
        except etree.XMLSyntaxError as e:
            logger.warning(f"XML parse error: {e}")
            # Try regex-based extraction as fallback
            return self._parse_with_regex(content)
    
    def _clean_xml_content(self, content: str) -> str:
        """Clean XML content for parsing"""
        # Remove BOM
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Remove null bytes
        content = content.replace('\x00', '')
        
        # Fix common namespace issues
        content = re.sub(r'xmlns:[a-z]+="[^"]*"', '', content)
        
        return content
    
    def _parse_element(self, element: etree._Element, depth: int = 0) -> List[FlowStep]:
        """Recursively parse XML element into FlowSteps"""
        steps = []
        self.current_line += 1
        
        for child in element:
            tag = child.tag.lower() if child.tag else ''
            
            # Remove namespace prefix
            if '}' in tag:
                tag = tag.split('}')[1]
            
            step = None
            
            # Check for flow verbs
            if tag in self.VERB_TAGS:
                verb = self.VERB_TAGS[tag]
                step = self._parse_verb_step(child, verb)
                
            elif tag in self.TRY_CATCH_TAGS:
                verb = self.TRY_CATCH_TAGS[tag]
                step = self._parse_try_catch_step(child, verb)
                
            elif tag == 'invoke' or 'service' in tag:
                step = self._parse_invoke_step(child)
                
            elif tag == 'mapset' or tag == 'mapcopy' or tag == 'mapdrop':
                step = self._parse_map_operation(child, tag)
            
            if step:
                # Parse nested children
                step.children = self._parse_element(child, depth + 1)
                steps.append(step)
            else:
                # Continue parsing children even without recognized step
                nested = self._parse_element(child, depth + 1)
                steps.extend(nested)
        
        return steps
    
    def _parse_verb_step(self, element: etree._Element, verb: FlowVerb) -> FlowStep:
        """Parse a flow verb step"""
        step = FlowStep(
            verb=verb,
            name=element.get('NAME', '') or element.get('name', ''),
            label=element.get('LABEL', '') or element.get('label', ''),
            comment=element.get('COMMENT', '') or element.get('comment', ''),
            enabled=element.get('DISABLED', '').lower() != 'true',
            line_number=self.current_line
        )
        
        if verb == FlowVerb.MAP:
            step = self._enrich_map_step(element, step)
        elif verb == FlowVerb.BRANCH:
            step = self._enrich_branch_step(element, step)
        elif verb == FlowVerb.LOOP:
            step = self._enrich_loop_step(element, step)
        elif verb == FlowVerb.REPEAT:
            step = self._enrich_repeat_step(element, step)
        elif verb == FlowVerb.SEQUENCE:
            step = self._enrich_sequence_step(element, step)
        elif verb == FlowVerb.EXIT:
            step = self._enrich_exit_step(element, step)
        elif verb == FlowVerb.INVOKE:
            step = self._enrich_invoke_step(element, step)
        
        return step
    
    def _enrich_map_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich MAP step with mappings and transformations"""
        
        # Parse MAPSET operations (variable assignments)
        for mapset in element.findall('.//MAPSET') + element.findall('.//mapset'):
            field = mapset.get('FIELD', '') or mapset.get('field', '')
            
            # Look for transformer expression
            value_elem = mapset.find('.//DATA') or mapset.find('.//data')
            if value_elem is not None:
                value = value_elem.text or ''
            else:
                value = mapset.text or ''
            
            if field:
                step.set_values.append({
                    'field': field,
                    'value': value,
                    'is_transformer': '%' in value  # Transformer expressions use %var%
                })
        
        # Parse MAPCOPY operations (field-to-field mappings)
        for mapcopy in element.findall('.//MAPCOPY') + element.findall('.//mapcopy'):
            source = mapcopy.get('FROM', '') or mapcopy.get('from', '')
            target = mapcopy.get('TO', '') or mapcopy.get('to', '')
            if source and target:
                step.mappings.append({
                    'source': source,
                    'target': target
                })
        
        # Parse MAPDROP operations (pipeline cleanup)
        for mapdrop in element.findall('.//MAPDROP') + element.findall('.//mapdrop'):
            field = mapdrop.get('FIELD', '') or mapdrop.get('field', '')
            if field:
                step.drop_values.append(field)
        
        # Parse MAPINVOKE (service calls within MAP)
        for mapinvoke in element.findall('.//MAPINVOKE') + element.findall('.//mapinvoke'):
            service = mapinvoke.get('SERVICE', '') or mapinvoke.get('service', '')
            if service:
                invocation = self._create_service_invocation(service)
                step.service_invocation = invocation
        
        return step
    
    def _enrich_branch_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich BRANCH step with conditions"""
        
        # Switch variable
        step.switch_variable = (element.get('SWITCH', '') or 
                               element.get('switch', '') or
                               element.get('VARIABLE', ''))
        
        # Evaluate labels flag
        eval_labels = element.get('EVALUATE', '') or element.get('evaluate_labels', '')
        step.evaluate_labels = eval_labels.lower() != 'false'
        
        # Parse branch cases
        for case_elem in (element.findall('.//CASE') + 
                         element.findall('.//case') +
                         element.findall('.//TARGET') +
                         element.findall('.//target')):
            
            label = (case_elem.get('LABEL', '') or 
                    case_elem.get('label', '') or
                    case_elem.get('VALUE', ''))
            is_default = (case_elem.get('DEFAULT', '').lower() == 'true' or
                         label == '$default' or
                         label == '*')
            
            branch_case = BranchCase(
                label=label,
                is_default=is_default,
                steps=self._parse_element(case_elem)
            )
            step.branches.append(branch_case)
        
        return step
    
    def _enrich_loop_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich LOOP step with iteration config"""
        
        # Input array to iterate
        step.loop_array = (element.get('INPUT', '') or 
                          element.get('ARRAY', '') or
                          element.get('input', ''))
        
        # Output variable for current item
        step.loop_variable = (element.get('OUTPUT', '') or
                             element.get('LOOPVAR', '') or
                             element.get('output', ''))
        
        # Counter variable
        step.loop_counter = (element.get('COUNT', '') or
                            element.get('COUNTER', '') or
                            element.get('$iteration', ''))
        
        return step
    
    def _enrich_repeat_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich REPEAT step (while loop)"""
        
        # Count/max iterations
        count = element.get('COUNT', '') or element.get('count', '')
        if count:
            try:
                step.complexity_factors = {'max_iterations': int(count)}
            except ValueError:
                pass
        
        # Repeat on success/failure
        step.exit_on = element.get('REPEATON', '') or element.get('repeat_on', 'FAILURE')
        
        return step
    
    def _enrich_sequence_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich SEQUENCE step"""
        
        # Exit on behavior
        step.exit_on = (element.get('EXITON', '') or 
                       element.get('exit_on', '') or
                       'FAILURE')
        
        return step
    
    def _enrich_exit_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich EXIT step"""
        
        # Exit from (flow, loop, parent)
        exit_from = element.get('FROM', '') or element.get('from', '')
        
        # Signal (success, failure)
        signal = element.get('SIGNAL', '') or element.get('signal', '')
        
        step.comment = f"Exit from {exit_from} with signal {signal}"
        
        return step
    
    def _parse_try_catch_step(self, element: etree._Element, verb: FlowVerb) -> FlowStep:
        """Parse TRY/CATCH/FINALLY step"""
        step = FlowStep(
            verb=verb,
            name=f"{verb.value} block",
            line_number=self.current_line
        )
        
        if verb == FlowVerb.CATCH:
            # Exception type to catch
            exception_type = element.get('EXCEPTION', '') or element.get('exception', '')
            step.comment = f"Catches: {exception_type or 'all exceptions'}"
        
        return step
    
    def _enrich_invoke_step(self, element: etree._Element, step: FlowStep) -> FlowStep:
        """Enrich INVOKE step"""
        service = (element.get('SERVICE', '') or 
                  element.get('service', '') or
                  element.get('NAME', ''))
        
        if service:
            step.service_invocation = self._create_service_invocation(service)
            step.name = service.split(':')[-1] if ':' in service else service
        
        return step
    
    def _parse_invoke_step(self, element: etree._Element) -> FlowStep:
        """Parse standalone INVOKE element"""
        service = (element.get('SERVICE', '') or 
                  element.get('service', '') or
                  element.get('NAME', '') or
                  element.text or '')
        
        step = FlowStep(
            verb=FlowVerb.INVOKE,
            name=service.split(':')[-1] if ':' in service else service,
            line_number=self.current_line
        )
        
        if service:
            step.service_invocation = self._create_service_invocation(service)
        
        return step
    
    def _parse_map_operation(self, element: etree._Element, operation: str) -> Optional[FlowStep]:
        """Parse individual map operation as step"""
        step = FlowStep(
            verb=FlowVerb.MAP,
            name=f"MAP:{operation}",
            line_number=self.current_line
        )
        
        if operation == 'mapset':
            field = element.get('FIELD', '') or element.get('field', '')
            value = element.text or ''
            step.set_values.append({'field': field, 'value': value})
        elif operation == 'mapcopy':
            source = element.get('FROM', '') or element.get('from', '')
            target = element.get('TO', '') or element.get('to', '')
            step.mappings.append({'source': source, 'target': target})
        elif operation == 'mapdrop':
            field = element.get('FIELD', '') or element.get('field', '')
            step.drop_values.append(field)
        
        return step
    
    def _create_service_invocation(self, service_path: str) -> ServiceInvocation:
        """Create ServiceInvocation from service path"""
        # Parse service path (e.g., "pub.string:concat" or "mypackage.services:myService")
        parts = service_path.split(':')
        if len(parts) >= 2:
            package = parts[0]
            name = parts[1]
        else:
            package = ''
            name = service_path
        
        # Check if wMPublic
        is_wmpublic = (package.startswith('pub.') or 
                      package.startswith('wm.') or
                      package.startswith('wm'))
        
        return ServiceInvocation(
            service_name=name,
            package=package,
            full_path=service_path,
            is_wmpublic=is_wmpublic,
            line_number=self.current_line
        )
    
    def _count_verbs(self, steps: List[FlowStep], counts: Dict[str, int] = None) -> Dict[str, int]:
        """Recursively count verb occurrences"""
        if counts is None:
            counts = {
                'MAP': 0,
                'BRANCH': 0,
                'LOOP': 0,
                'REPEAT': 0,
                'SEQUENCE': 0,
                'INVOKE': 0,
                'EXIT': 0,
                'TRY': 0,
                'CATCH': 0,
                'FINALLY': 0,
            }
        
        for step in steps:
            verb_name = step.verb.value
            if verb_name in counts:
                counts[verb_name] += 1
            
            # Count nested steps
            if step.children:
                self._count_verbs(step.children, counts)
            
            # Count branch steps
            for branch in step.branches:
                self._count_verbs(branch.steps, counts)
        
        return counts
    
    def _parse_with_regex(self, content: str) -> Tuple[List[FlowStep], Dict[str, int]]:
        """Fallback regex-based parsing"""
        steps = []
        verb_counts = {v.value: 0 for v in FlowVerb}
        
        # Find all verb occurrences
        verb_patterns = {
            FlowVerb.MAP: r'<MAP[^>]*>|<MAPSET|<MAPCOPY|<MAPDROP',
            FlowVerb.BRANCH: r'<BRANCH[^>]*>',
            FlowVerb.LOOP: r'<LOOP[^>]*>',
            FlowVerb.REPEAT: r'<REPEAT[^>]*>',
            FlowVerb.SEQUENCE: r'<SEQUENCE[^>]*>',
            FlowVerb.INVOKE: r'<INVOKE[^>]*SERVICE=["\']([^"\']+)',
            FlowVerb.EXIT: r'<EXIT[^>]*>',
        }
        
        for verb, pattern in verb_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            count = len(matches)
            verb_counts[verb.value] = count
            
            # Create basic steps
            for match in matches:
                step = FlowStep(
                    verb=verb,
                    name=match if isinstance(match, str) and verb == FlowVerb.INVOKE else verb.value
                )
                if verb == FlowVerb.INVOKE and isinstance(match, str):
                    step.service_invocation = self._create_service_invocation(match)
                steps.append(step)
        
        return steps, verb_counts
    
    def extract_service_invocations(self, steps: List[FlowStep]) -> Tuple[List[str], List[str]]:
        """Extract all service invocations, separated by wMPublic vs custom"""
        wmpublic = []
        custom = []
        
        def collect(step_list: List[FlowStep]):
            for step in step_list:
                if step.service_invocation:
                    inv = step.service_invocation
                    if inv.is_wmpublic:
                        wmpublic.append(inv.full_path)
                    else:
                        custom.append(inv.full_path)
                
                collect(step.children)
                for branch in step.branches:
                    collect(branch.steps)
        
        collect(steps)
        return wmpublic, custom


# =============================================================================
# PIPELINE STATE TRACKER
# =============================================================================

@dataclass
class PipelineState:
    """Represents pipeline state at a point in flow"""
    variables: Dict[str, PipelineVariable] = field(default_factory=dict)
    scope_stack: List[str] = field(default_factory=list)
    
    def add_variable(self, var: PipelineVariable):
        """Add variable to pipeline"""
        self.variables[var.path] = var
    
    def remove_variable(self, path: str):
        """Remove variable from pipeline"""
        if path in self.variables:
            del self.variables[path]
    
    def get_variable(self, path: str) -> Optional[PipelineVariable]:
        """Get variable by path"""
        return self.variables.get(path)
    
    def enter_scope(self, scope_name: str):
        """Enter a new scope (sequence, try, etc.)"""
        self.scope_stack.append(scope_name)
    
    def exit_scope(self) -> Optional[str]:
        """Exit current scope"""
        if self.scope_stack:
            return self.scope_stack.pop()
        return None
    
    def clone(self) -> 'PipelineState':
        """Create a copy of current state"""
        new_state = PipelineState()
        new_state.variables = dict(self.variables)
        new_state.scope_stack = list(self.scope_stack)
        return new_state


class PipelineAnalyzer:
    """
    Analyzes pipeline state through a flow.
    
    webMethods pipeline is a HEAP structure:
    - Variables accumulate from each service call
    - Requires manual DROP to clean up
    - Scope rules apply for sequences
    
    This differs from Boomi where data is managed automatically.
    """
    
    def __init__(self):
        self.state_history: List[Tuple[str, PipelineState]] = []
        self.issues: List[Dict] = []
    
    def analyze(self, steps: List[FlowStep], 
                initial_state: PipelineState = None) -> Dict[str, Any]:
        """
        Analyze pipeline through flow steps.
        Returns analysis results.
        """
        if initial_state is None:
            initial_state = PipelineState()
        
        self.state_history = []
        self.issues = []
        
        final_state = self._analyze_steps(steps, initial_state)
        
        return {
            'final_state': final_state,
            'state_history': self.state_history,
            'issues': self.issues,
            'total_variables': len(final_state.variables),
            'memory_concern': len(final_state.variables) > 50,
            'dropped_count': self._count_drops(steps),
        }
    
    def _analyze_steps(self, steps: List[FlowStep], 
                       state: PipelineState) -> PipelineState:
        """Recursively analyze steps"""
        
        for step in steps:
            # Record state before this step
            self.state_history.append((step.name, state.clone()))
            
            if step.verb == FlowVerb.MAP:
                state = self._analyze_map(step, state)
            elif step.verb == FlowVerb.INVOKE:
                state = self._analyze_invoke(step, state)
            elif step.verb == FlowVerb.LOOP:
                state = self._analyze_loop(step, state)
            elif step.verb == FlowVerb.BRANCH:
                state = self._analyze_branch(step, state)
            elif step.verb == FlowVerb.SEQUENCE:
                state.enter_scope(step.name)
                state = self._analyze_steps(step.children, state)
                state.exit_scope()
            elif step.verb in [FlowVerb.TRY, FlowVerb.CATCH, FlowVerb.FINALLY]:
                state = self._analyze_steps(step.children, state)
            else:
                # Continue with children
                state = self._analyze_steps(step.children, state)
        
        return state
    
    def _analyze_map(self, step: FlowStep, state: PipelineState) -> PipelineState:
        """Analyze MAP step's effect on pipeline"""
        
        # SET operations add to pipeline
        for set_op in step.set_values:
            field = set_op.get('field', '')
            if field:
                var = PipelineVariable(
                    name=field.split('/')[-1],
                    path=field,
                    type='string',  # Default, would need signature to know actual type
                    source=f"MAP:{step.name}"
                )
                state.add_variable(var)
        
        # COPY operations add to pipeline
        for copy_op in step.mappings:
            target = copy_op.get('target', '')
            if target:
                var = PipelineVariable(
                    name=target.split('/')[-1],
                    path=target,
                    type='string',
                    source=f"MAP:{step.name}"
                )
                state.add_variable(var)
        
        # DROP operations remove from pipeline
        for drop_path in step.drop_values:
            state.remove_variable(drop_path)
        
        return state
    
    def _analyze_invoke(self, step: FlowStep, state: PipelineState) -> PipelineState:
        """Analyze INVOKE step's effect on pipeline"""
        
        if step.service_invocation:
            inv = step.service_invocation
            
            # Service outputs are added to pipeline
            # If we have catalog info, use it
            svc_def = lookup_service(inv.full_path)
            if svc_def:
                for output in svc_def.outputs:
                    var = PipelineVariable(
                        name=output.name,
                        path=output.name,
                        type=output.type,
                        source=f"INVOKE:{inv.full_path}"
                    )
                    state.add_variable(var)
            else:
                # Unknown service - flag as potential issue
                if not inv.is_wmpublic:
                    self.issues.append({
                        'type': 'unknown_service',
                        'service': inv.full_path,
                        'message': f"Service {inv.full_path} outputs unknown - may add to pipeline"
                    })
        
        return state
    
    def _analyze_loop(self, step: FlowStep, state: PipelineState) -> PipelineState:
        """Analyze LOOP step's effect on pipeline"""
        
        # Loop variable is added
        if step.loop_variable:
            var = PipelineVariable(
                name=step.loop_variable.split('/')[-1],
                path=step.loop_variable,
                type='document',  # Loop iteration item
                source=f"LOOP:{step.name}"
            )
            state.add_variable(var)
        
        # Counter variable
        if step.loop_counter:
            var = PipelineVariable(
                name=step.loop_counter,
                path=step.loop_counter,
                type='string',
                source=f"LOOP:{step.name}"
            )
            state.add_variable(var)
        
        # Analyze loop body
        state = self._analyze_steps(step.children, state)
        
        # Note: In webMethods, loop variables persist after loop!
        # This is different from Boomi
        self.issues.append({
            'type': 'loop_variable_persists',
            'variable': step.loop_variable,
            'message': f"Loop variable {step.loop_variable} persists after LOOP - consider DROP"
        })
        
        return state
    
    def _analyze_branch(self, step: FlowStep, state: PipelineState) -> PipelineState:
        """Analyze BRANCH step's effect on pipeline"""
        
        # Each branch may modify pipeline differently
        branch_states = []
        
        for branch in step.branches:
            branch_state = state.clone()
            branch_state = self._analyze_steps(branch.steps, branch_state)
            branch_states.append(branch_state)
        
        # After branch, we need to consider variables from all paths
        # This is conservative - assumes any branch could execute
        for bs in branch_states:
            for path, var in bs.variables.items():
                if path not in state.variables:
                    state.add_variable(var)
        
        return state
    
    def _count_drops(self, steps: List[FlowStep]) -> int:
        """Count total DROP operations"""
        count = 0
        
        for step in steps:
            if step.verb == FlowVerb.MAP:
                count += len(step.drop_values)
            count += self._count_drops(step.children)
            for branch in step.branches:
                count += self._count_drops(branch.steps)
        
        return count


# =============================================================================
# COMPLEXITY ANALYZER
# =============================================================================

class ComplexityAnalyzer:
    """
    Calculates complexity score for a flow service.
    
    Factors:
    - Number and types of verbs
    - Nesting depth
    - Service invocation count (especially wMPublic)
    - Pipeline complexity
    - Adapter usage
    """
    
    # Complexity weights
    VERB_WEIGHTS = {
        FlowVerb.MAP: 1,
        FlowVerb.BRANCH: 3,
        FlowVerb.LOOP: 4,
        FlowVerb.REPEAT: 4,
        FlowVerb.SEQUENCE: 2,
        FlowVerb.INVOKE: 2,
        FlowVerb.EXIT: 1,
        FlowVerb.TRY: 2,
        FlowVerb.CATCH: 2,
        FlowVerb.FINALLY: 2,
    }
    
    def calculate(self, service: ParsedService) -> Dict[str, Any]:
        """Calculate complexity for a service"""
        
        factors = {
            'verb_score': 0,
            'nesting_score': 0,
            'invocation_score': 0,
            'wmpublic_count': 0,
            'custom_count': 0,
            'pipeline_score': 0,
            'adapter_score': 0,
        }
        
        # Calculate verb score
        for verb_name, count in service.verb_counts.items():
            try:
                verb = FlowVerb(verb_name)
                weight = self.VERB_WEIGHTS.get(verb, 1)
                factors['verb_score'] += count * weight
            except ValueError:
                pass
        
        # Nesting depth
        max_depth = self._calculate_max_depth(service.flow_steps)
        factors['nesting_score'] = max_depth * 3
        
        # Invocation counts
        factors['wmpublic_count'] = len(service.wmpublic_calls)
        factors['custom_count'] = len(service.custom_calls)
        factors['invocation_score'] = (factors['wmpublic_count'] * 1 + 
                                       factors['custom_count'] * 2)
        
        # Adapter complexity
        if service.adapter_type:
            adapter_scores = {
                'JDBC': 5,
                'SAP': 8,
                'HTTP': 3,
                'SOAP': 4,
                'JMS': 4,
                'FTP': 2,
                'SFTP': 2,
                'File': 1,
            }
            factors['adapter_score'] = adapter_scores.get(
                service.adapter_type.value, 3
            )
            
            # Extra points for complex JDBC
            if service.adapter_type.value == 'JDBC':
                config = service.adapter_config
                if config.get('joins'):
                    factors['adapter_score'] += len(config['joins']) * 3
                if config.get('where_clauses'):
                    factors['adapter_score'] += len(config['where_clauses'])
        
        # Total score
        total_score = sum(factors.values())
        
        # Determine level
        if total_score < 20:
            level = 'low'
        elif total_score < 50:
            level = 'medium'
        else:
            level = 'high'
        
        return {
            'score': total_score,
            'level': level,
            'factors': factors,
            'max_nesting_depth': max_depth,
        }
    
    def _calculate_max_depth(self, steps: List[FlowStep], 
                            current_depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = current_depth
        
        for step in steps:
            if step.children:
                child_depth = self._calculate_max_depth(
                    step.children, current_depth + 1
                )
                max_depth = max(max_depth, child_depth)
            
            for branch in step.branches:
                branch_depth = self._calculate_max_depth(
                    branch.steps, current_depth + 1
                )
                max_depth = max(max_depth, branch_depth)
        
        return max_depth
    
    def estimate_conversion_hours(self, service: ParsedService) -> Dict[str, Any]:
        """Estimate hours needed to convert this service"""
        
        complexity = self.calculate(service)
        
        # Base hours by service type
        base_hours = {
            ServiceType.FLOW_SERVICE: 4,
            ServiceType.JAVA_SERVICE: 8,
            ServiceType.ADAPTER_SERVICE: 6,
            ServiceType.MAP_SERVICE: 2,
            ServiceType.DOCUMENT_TYPE: 1,
        }
        
        hours = base_hours.get(service.type, 4)
        
        # Complexity multiplier
        multipliers = {'low': 1.0, 'medium': 1.5, 'high': 2.5}
        hours *= multipliers.get(complexity['level'], 1.5)
        
        # wMPublic overhead (some need manual review)
        wmpublic_overhead = len(service.wmpublic_calls) * 0.1
        hours += min(wmpublic_overhead, 4)  # Cap at 4 hours
        
        # Custom service overhead (need to understand dependencies)
        custom_overhead = len(service.custom_calls) * 0.3
        hours += min(custom_overhead, 8)
        
        # Adapter overhead
        if service.adapter_type:
            if service.adapter_type in [AdapterType.JDBC, AdapterType.SAP]:
                hours += 2
            else:
                hours += 1
        
        # Automation potential
        automation = self._calculate_automation_potential(service, complexity)
        
        return {
            'estimated_hours': round(hours, 1),
            'automation_percentage': automation,
            'manual_hours': round(hours * (100 - automation) / 100, 1),
            'complexity': complexity
        }
    
    def _calculate_automation_potential(self, service: ParsedService,
                                       complexity: Dict) -> int:
        """Calculate automation potential percentage"""
        
        # Start with base by service type
        base = {
            ServiceType.FLOW_SERVICE: 85,
            ServiceType.JAVA_SERVICE: 25,
            ServiceType.ADAPTER_SERVICE: 70,
            ServiceType.MAP_SERVICE: 90,
            ServiceType.DOCUMENT_TYPE: 95,
        }
        
        automation = base.get(service.type, 70)
        
        # Reduce for complexity
        if complexity['level'] == 'high':
            automation -= 20
        elif complexity['level'] == 'medium':
            automation -= 10
        
        # Reduce for unknown services
        catalog = get_catalog()
        unknown_count = 0
        for svc in service.wmpublic_calls:
            if not catalog.get_service(svc):
                unknown_count += 1
        
        automation -= min(unknown_count * 2, 15)
        
        # Reduce for complex adapters
        if service.adapter_type == AdapterType.JDBC:
            if service.adapter_config.get('joins'):
                automation -= len(service.adapter_config['joins']) * 5
        elif service.adapter_type == AdapterType.SAP:
            automation -= 15
        
        return max(10, min(95, automation))


# Export for convenience
__all__ = [
    'FlowXMLParser',
    'PipelineAnalyzer',
    'PipelineState',
    'ComplexityAnalyzer',
]
