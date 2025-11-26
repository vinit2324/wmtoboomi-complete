"""
Pattern Recognition Engine for webMethods to Boomi Migration
============================================================

This is the KEY to achieving 80-90% automation.

Most webMethods flows follow common patterns:
1. Fetch → Transform → Send (60% of all flows)
2. Error handling wrappers
3. Lookup/enrichment patterns
4. Batch processing loops
5. Conditional routing

By recognizing these patterns, we can auto-generate complete Boomi processes
instead of converting step-by-step.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re


class FlowPattern(Enum):
    """Common webMethods flow patterns"""
    # Data Integration Patterns (60% of flows)
    FETCH_TRANSFORM_SEND = "fetch_transform_send"      # Get data, transform, send somewhere
    DATABASE_TO_FILE = "database_to_file"              # Query DB, write to file
    FILE_TO_DATABASE = "file_to_database"              # Read file, insert to DB
    API_TO_API = "api_to_api"                          # Call API, transform, call another API
    
    # Processing Patterns (20% of flows)
    BATCH_PROCESSOR = "batch_processor"                # Loop over items, process each
    SPLITTER_AGGREGATOR = "splitter_aggregator"        # Split, process, combine
    CONTENT_ROUTER = "content_router"                  # Route based on content
    
    # Error Handling Patterns (15% of flows)
    TRY_CATCH_WRAPPER = "try_catch_wrapper"            # Main logic wrapped in try/catch
    RETRY_PATTERN = "retry_pattern"                    # Retry on failure
    DEAD_LETTER = "dead_letter"                        # Handle failures separately
    
    # Utility Patterns (5% of flows)
    SIMPLE_TRANSFORM = "simple_transform"              # Just data mapping
    VALIDATION = "validation"                          # Validate and route
    LOOKUP_ENRICHMENT = "lookup_enrichment"            # Lookup data, add to message
    
    # Unknown (needs manual review)
    UNKNOWN = "unknown"


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    pattern: FlowPattern
    confidence: float  # 0.0 to 1.0
    matched_elements: List[str]
    boomi_template: str
    automation_level: int  # percentage
    conversion_notes: List[str] = field(default_factory=list)


@dataclass
class FlowAnalysis:
    """Complete analysis of a flow service"""
    service_name: str
    total_steps: int
    verb_counts: Dict[str, int]
    service_calls: List[str]
    wmpublic_calls: List[str]
    custom_calls: List[str]
    adapter_types: List[str]
    has_loop: bool
    has_branch: bool
    has_try_catch: bool
    nesting_depth: int
    pipeline_complexity: str
    detected_patterns: List[PatternMatch]
    primary_pattern: Optional[PatternMatch]
    overall_automation: int


class PatternRecognitionEngine:
    """
    Recognizes common patterns in webMethods flows.
    
    This is the core engine that enables 80-90% automation by:
    1. Analyzing flow structure
    2. Identifying common patterns
    3. Generating appropriate Boomi templates
    """
    
    # Pattern signatures - what we look for
    PATTERN_SIGNATURES = {
        FlowPattern.FETCH_TRANSFORM_SEND: {
            "required_adapters": ["jdbc", "http", "ftp", "file"],  # at least one
            "required_verbs": ["map", "invoke"],
            "has_output": True,
            "typical_wmpublic": ["pub.document", "pub.string", "pub.xml", "pub.json"],
        },
        FlowPattern.DATABASE_TO_FILE: {
            "required_adapters": ["jdbc"],
            "output_adapters": ["ftp", "sftp", "file"],
            "typical_wmpublic": ["pub.flatFile", "pub.file"],
        },
        FlowPattern.FILE_TO_DATABASE: {
            "input_adapters": ["ftp", "sftp", "file"],
            "required_adapters": ["jdbc"],
            "typical_wmpublic": ["pub.flatFile", "pub.db"],
        },
        FlowPattern.API_TO_API: {
            "required_adapters": ["http"],
            "min_http_calls": 2,
            "typical_wmpublic": ["pub.json", "pub.xml", "pub.soap"],
        },
        FlowPattern.BATCH_PROCESSOR: {
            "required_verbs": ["loop"],
            "min_loop_steps": 2,
        },
        FlowPattern.TRY_CATCH_WRAPPER: {
            "required_verbs": ["sequence"],
            "has_try_catch": True,
        },
        FlowPattern.SIMPLE_TRANSFORM: {
            "required_verbs": ["map"],
            "max_steps": 5,
            "no_adapters": True,
        },
        FlowPattern.CONTENT_ROUTER: {
            "required_verbs": ["branch"],
            "min_branches": 2,
        },
    }
    
    def __init__(self):
        self.patterns_detected: List[PatternMatch] = []
        
    def analyze_flow(self, 
                     steps: List[Dict],
                     verb_counts: Dict[str, int],
                     service_invocations: List[Dict],
                     adapter_types: List[str]) -> FlowAnalysis:
        """
        Analyze a flow and detect patterns.
        
        Args:
            steps: Parsed flow steps
            verb_counts: Count of each verb type
            service_invocations: All service calls
            adapter_types: Types of adapters used
            
        Returns:
            FlowAnalysis with detected patterns and automation estimate
        """
        # Categorize service calls
        wmpublic_calls = [s for s in service_invocations if self._is_wmpublic(s)]
        custom_calls = [s for s in service_invocations if not self._is_wmpublic(s)]
        
        # Detect patterns
        detected = self._detect_patterns(
            verb_counts, 
            wmpublic_calls, 
            custom_calls,
            adapter_types,
            len(steps)
        )
        
        # Sort by confidence
        detected.sort(key=lambda x: x.confidence, reverse=True)
        
        # Get primary pattern
        primary = detected[0] if detected and detected[0].confidence > 0.5 else None
        
        # Calculate overall automation
        if primary:
            automation = primary.automation_level
        else:
            # Fallback: estimate based on components
            automation = self._estimate_automation(
                verb_counts, wmpublic_calls, custom_calls, adapter_types
            )
        
        return FlowAnalysis(
            service_name="",  # Set by caller
            total_steps=len(steps),
            verb_counts=verb_counts,
            service_calls=[s.get('full_path', s.get('service_name', '')) for s in service_invocations],
            wmpublic_calls=[s.get('full_path', '') for s in wmpublic_calls],
            custom_calls=[s.get('full_path', '') for s in custom_calls],
            adapter_types=adapter_types,
            has_loop=verb_counts.get('LOOP', 0) > 0,
            has_branch=verb_counts.get('BRANCH', 0) > 0,
            has_try_catch=verb_counts.get('TRY', 0) > 0 or verb_counts.get('SEQUENCE', 0) > 0,
            nesting_depth=self._calculate_nesting(steps),
            pipeline_complexity=self._assess_pipeline_complexity(verb_counts, len(service_invocations)),
            detected_patterns=detected,
            primary_pattern=primary,
            overall_automation=automation
        )
    
    def _is_wmpublic(self, service: Dict) -> bool:
        """Check if service is wMPublic"""
        name = service.get('full_path', service.get('service_name', ''))
        return name.startswith('pub.') or name.startswith('wm.')
    
    def _detect_patterns(self,
                         verb_counts: Dict[str, int],
                         wmpublic_calls: List[Dict],
                         custom_calls: List[Dict],
                         adapter_types: List[str],
                         total_steps: int) -> List[PatternMatch]:
        """Detect all matching patterns"""
        patterns = []
        
        # Check each pattern
        patterns.append(self._check_fetch_transform_send(verb_counts, wmpublic_calls, adapter_types))
        patterns.append(self._check_database_to_file(verb_counts, wmpublic_calls, adapter_types))
        patterns.append(self._check_file_to_database(verb_counts, wmpublic_calls, adapter_types))
        patterns.append(self._check_api_to_api(verb_counts, wmpublic_calls, adapter_types))
        patterns.append(self._check_batch_processor(verb_counts, wmpublic_calls, total_steps))
        patterns.append(self._check_try_catch_wrapper(verb_counts))
        patterns.append(self._check_simple_transform(verb_counts, adapter_types, total_steps))
        patterns.append(self._check_content_router(verb_counts))
        
        # Filter out low confidence matches
        return [p for p in patterns if p.confidence > 0.3]
    
    def _check_fetch_transform_send(self, verb_counts, wmpublic_calls, adapter_types) -> PatternMatch:
        """Check for Fetch-Transform-Send pattern"""
        confidence = 0.0
        matched = []
        
        # Has data source adapter?
        data_adapters = ['jdbc', 'http', 'ftp', 'sftp', 'file', 'jms']
        source_adapters = [a for a in adapter_types if a.lower() in data_adapters]
        if source_adapters:
            confidence += 0.3
            matched.append(f"Data source: {source_adapters}")
        
        # Has mapping?
        if verb_counts.get('MAP', 0) > 0 or verb_counts.get('INVOKE', 0) > 0:
            confidence += 0.3
            matched.append(f"Transform: {verb_counts.get('MAP', 0)} maps")
        
        # Has wMPublic transform calls?
        transform_packages = ['pub.document', 'pub.string', 'pub.xml', 'pub.json', 'pub.list']
        transform_calls = [c for c in wmpublic_calls 
                         if any(c.get('full_path', '').startswith(p) for p in transform_packages)]
        if transform_calls:
            confidence += 0.2
            matched.append(f"Transform services: {len(transform_calls)}")
        
        # Has output?
        if len(adapter_types) > 1 or verb_counts.get('INVOKE', 0) > 1:
            confidence += 0.2
            matched.append("Has output destination")
        
        return PatternMatch(
            pattern=FlowPattern.FETCH_TRANSFORM_SEND,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="fetch_transform_send",
            automation_level=85,
            conversion_notes=[
                "Standard integration pattern",
                "Map source connector → Map shape → Destination connector",
                "Boomi handles iteration automatically"
            ]
        )
    
    def _check_database_to_file(self, verb_counts, wmpublic_calls, adapter_types) -> PatternMatch:
        """Check for Database-to-File pattern"""
        confidence = 0.0
        matched = []
        
        # Has JDBC?
        if 'jdbc' in [a.lower() for a in adapter_types]:
            confidence += 0.4
            matched.append("JDBC adapter present")
        
        # Has file output?
        file_adapters = ['ftp', 'sftp', 'file']
        if any(a.lower() in file_adapters for a in adapter_types):
            confidence += 0.3
            matched.append("File output adapter present")
        
        # Has flat file conversion?
        ff_calls = [c for c in wmpublic_calls if 'flatFile' in c.get('full_path', '')]
        if ff_calls:
            confidence += 0.3
            matched.append("Flat file conversion")
        
        return PatternMatch(
            pattern=FlowPattern.DATABASE_TO_FILE,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="database_to_file",
            automation_level=88,
            conversion_notes=[
                "Database Connector → Map → Flat File Profile → FTP/Disk Connector",
                "Configure query in Database connector",
                "Set up Flat File profile for output format"
            ]
        )
    
    def _check_file_to_database(self, verb_counts, wmpublic_calls, adapter_types) -> PatternMatch:
        """Check for File-to-Database pattern"""
        confidence = 0.0
        matched = []
        
        # Has file input?
        file_adapters = ['ftp', 'sftp', 'file']
        if any(a.lower() in file_adapters for a in adapter_types):
            confidence += 0.3
            matched.append("File input adapter present")
        
        # Has JDBC output?
        if 'jdbc' in [a.lower() for a in adapter_types]:
            confidence += 0.4
            matched.append("JDBC adapter for output")
        
        # Has flat file parsing?
        ff_calls = [c for c in wmpublic_calls if 'flatFile' in c.get('full_path', '')]
        if ff_calls:
            confidence += 0.3
            matched.append("Flat file parsing")
        
        return PatternMatch(
            pattern=FlowPattern.FILE_TO_DATABASE,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="file_to_database",
            automation_level=85,
            conversion_notes=[
                "FTP/Disk Connector → Flat File Profile → Map → Database Connector",
                "Boomi handles batch inserts automatically",
                "Configure database operation (INSERT/UPSERT)"
            ]
        )
    
    def _check_api_to_api(self, verb_counts, wmpublic_calls, adapter_types) -> PatternMatch:
        """Check for API-to-API pattern"""
        confidence = 0.0
        matched = []
        
        # Has HTTP?
        http_count = adapter_types.count('http') + adapter_types.count('HTTP')
        if http_count >= 1:
            confidence += 0.3
            matched.append(f"HTTP adapter(s): {http_count}")
        if http_count >= 2:
            confidence += 0.3
            matched.append("Multiple HTTP calls (API to API)")
        
        # Has JSON/XML processing?
        api_calls = [c for c in wmpublic_calls 
                    if any(p in c.get('full_path', '') for p in ['pub.json', 'pub.xml', 'pub.soap'])]
        if api_calls:
            confidence += 0.3
            matched.append(f"API data processing: {len(api_calls)} calls")
        
        return PatternMatch(
            pattern=FlowPattern.API_TO_API,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="api_to_api",
            automation_level=82,
            conversion_notes=[
                "HTTP Connector (GET) → Map → HTTP Connector (POST)",
                "Configure authentication on each connector",
                "Use JSON/XML profiles for request/response"
            ]
        )
    
    def _check_batch_processor(self, verb_counts, wmpublic_calls, total_steps) -> PatternMatch:
        """Check for Batch Processor pattern"""
        confidence = 0.0
        matched = []
        
        # Has loop?
        loop_count = verb_counts.get('LOOP', 0)
        if loop_count > 0:
            confidence += 0.5
            matched.append(f"Loop(s): {loop_count}")
        
        # Multiple steps in loop?
        if total_steps > 3:
            confidence += 0.2
            matched.append(f"Multiple processing steps: {total_steps}")
        
        # Has list operations?
        list_calls = [c for c in wmpublic_calls if 'pub.list' in c.get('full_path', '')]
        if list_calls:
            confidence += 0.3
            matched.append(f"List operations: {len(list_calls)}")
        
        return PatternMatch(
            pattern=FlowPattern.BATCH_PROCESSOR,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="batch_processor",
            automation_level=80,
            conversion_notes=[
                "CRITICAL: Boomi handles iteration IMPLICITLY",
                "No need for explicit loops in most cases",
                "Use Split shape if explicit batching needed",
                "Consider Flow Control for throttling"
            ]
        )
    
    def _check_try_catch_wrapper(self, verb_counts) -> PatternMatch:
        """Check for Try-Catch wrapper pattern"""
        confidence = 0.0
        matched = []
        
        if verb_counts.get('SEQUENCE', 0) > 0:
            confidence += 0.3
            matched.append("SEQUENCE block")
        
        if verb_counts.get('TRY', 0) > 0:
            confidence += 0.4
            matched.append("TRY block")
        
        if verb_counts.get('CATCH', 0) > 0:
            confidence += 0.3
            matched.append("CATCH block")
        
        return PatternMatch(
            pattern=FlowPattern.TRY_CATCH_WRAPPER,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="try_catch_wrapper",
            automation_level=90,
            conversion_notes=[
                "Use Boomi Try/Catch shape",
                "Configure error handling path",
                "Consider Exception shape for specific errors"
            ]
        )
    
    def _check_simple_transform(self, verb_counts, adapter_types, total_steps) -> PatternMatch:
        """Check for Simple Transform pattern"""
        confidence = 0.0
        matched = []
        
        # Mostly MAP operations?
        map_count = verb_counts.get('MAP', 0)
        if map_count > 0:
            confidence += 0.4
            matched.append(f"MAP operations: {map_count}")
        
        # Few steps?
        if total_steps <= 5:
            confidence += 0.3
            matched.append(f"Simple flow: {total_steps} steps")
        
        # No complex adapters?
        if not adapter_types or len(adapter_types) == 0:
            confidence += 0.3
            matched.append("No external adapters")
        
        return PatternMatch(
            pattern=FlowPattern.SIMPLE_TRANSFORM,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="simple_transform",
            automation_level=95,
            conversion_notes=[
                "Simple Map shape conversion",
                "Direct field mappings",
                "May be inline-able into parent process"
            ]
        )
    
    def _check_content_router(self, verb_counts) -> PatternMatch:
        """Check for Content Router pattern"""
        confidence = 0.0
        matched = []
        
        # Has branching?
        branch_count = verb_counts.get('BRANCH', 0)
        if branch_count > 0:
            confidence += 0.5
            matched.append(f"BRANCH operations: {branch_count}")
        
        if branch_count >= 2:
            confidence += 0.3
            matched.append("Multiple routing paths")
        
        return PatternMatch(
            pattern=FlowPattern.CONTENT_ROUTER,
            confidence=min(confidence, 1.0),
            matched_elements=matched,
            boomi_template="content_router",
            automation_level=85,
            conversion_notes=[
                "Use Decision shape for routing",
                "Configure branch conditions",
                "Consider Route shape for complex routing"
            ]
        )
    
    def _calculate_nesting(self, steps: List[Dict], depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = depth
        for step in steps:
            children = step.get('children', [])
            branches = step.get('branches', [])
            
            if children:
                child_depth = self._calculate_nesting(children, depth + 1)
                max_depth = max(max_depth, child_depth)
            
            for branch in branches:
                branch_steps = branch.get('steps', [])
                branch_depth = self._calculate_nesting(branch_steps, depth + 1)
                max_depth = max(max_depth, branch_depth)
        
        return max_depth
    
    def _assess_pipeline_complexity(self, verb_counts: Dict[str, int], invocation_count: int) -> str:
        """Assess pipeline complexity"""
        total_verbs = sum(verb_counts.values())
        
        # Simple heuristic
        score = total_verbs + (invocation_count * 2)
        
        if score < 10:
            return "low"
        elif score < 30:
            return "medium"
        else:
            return "high"
    
    def _estimate_automation(self,
                            verb_counts: Dict[str, int],
                            wmpublic_calls: List[Dict],
                            custom_calls: List[Dict],
                            adapter_types: List[str]) -> int:
        """Estimate automation level when no pattern matches"""
        base = 70  # Start at 70%
        
        # wMPublic calls are highly automatable
        wmpublic_count = len(wmpublic_calls)
        if wmpublic_count > 0:
            base += min(wmpublic_count, 10)  # Up to +10%
        
        # Custom calls reduce automation
        custom_count = len(custom_calls)
        base -= min(custom_count * 5, 20)  # Up to -20%
        
        # Standard adapters are automatable
        standard_adapters = ['jdbc', 'http', 'ftp', 'sftp', 'file', 'jms']
        standard_count = sum(1 for a in adapter_types if a.lower() in standard_adapters)
        base += min(standard_count * 3, 10)  # Up to +10%
        
        # Complex verbs reduce automation slightly
        complex_verbs = verb_counts.get('LOOP', 0) + verb_counts.get('BRANCH', 0)
        base -= min(complex_verbs * 2, 10)  # Up to -10%
        
        return max(min(base, 95), 40)  # Clamp between 40-95%


# =============================================================================
# BOOMI PROCESS TEMPLATES
# =============================================================================

BOOMI_TEMPLATES = {
    "fetch_transform_send": """
    <!-- Boomi Process: Fetch-Transform-Send Pattern -->
    <Process>
        <Start/>
        <Connector type="source" operation="get"/>
        <Map sourceProfile="input" targetProfile="output"/>
        <Connector type="destination" operation="send"/>
        <Stop/>
    </Process>
    """,
    
    "database_to_file": """
    <!-- Boomi Process: Database to File Pattern -->
    <Process>
        <Start/>
        <DatabaseConnector operation="query"/>
        <Map sourceProfile="dbRecord" targetProfile="flatFileRecord"/>
        <FTPConnector operation="put"/>
        <Stop/>
    </Process>
    """,
    
    "file_to_database": """
    <!-- Boomi Process: File to Database Pattern -->
    <Process>
        <Start/>
        <FTPConnector operation="get"/>
        <Map sourceProfile="flatFileRecord" targetProfile="dbRecord"/>
        <DatabaseConnector operation="insert"/>
        <Stop/>
    </Process>
    """,
    
    "api_to_api": """
    <!-- Boomi Process: API to API Pattern -->
    <Process>
        <Start/>
        <HTTPConnector operation="get" url="sourceAPI"/>
        <Map sourceProfile="sourceJSON" targetProfile="targetJSON"/>
        <HTTPConnector operation="post" url="targetAPI"/>
        <Stop/>
    </Process>
    """,
    
    "batch_processor": """
    <!-- Boomi Process: Batch Processor Pattern -->
    <!-- NOTE: Boomi handles iteration implicitly! -->
    <Process>
        <Start/>
        <Connector type="source"/>
        <!-- No explicit loop needed - Boomi iterates automatically -->
        <Map sourceProfile="item" targetProfile="processedItem"/>
        <Connector type="destination"/>
        <Stop/>
    </Process>
    """,
    
    "try_catch_wrapper": """
    <!-- Boomi Process: Try-Catch Pattern -->
    <Process>
        <Start/>
        <TryCatch>
            <Try>
                <!-- Main processing -->
                <Map/>
                <Connector/>
            </Try>
            <Catch>
                <Notify type="error"/>
                <Stop status="error"/>
            </Catch>
        </TryCatch>
        <Stop/>
    </Process>
    """,
    
    "simple_transform": """
    <!-- Boomi Process: Simple Transform Pattern -->
    <Process>
        <Start/>
        <Map sourceProfile="input" targetProfile="output"/>
        <Stop/>
    </Process>
    """,
    
    "content_router": """
    <!-- Boomi Process: Content Router Pattern -->
    <Process>
        <Start/>
        <Decision>
            <Branch condition="field == 'value1'">
                <Connector type="destination1"/>
            </Branch>
            <Branch condition="field == 'value2'">
                <Connector type="destination2"/>
            </Branch>
            <Default>
                <Connector type="defaultDestination"/>
            </Default>
        </Decision>
        <Stop/>
    </Process>
    """,
}


def get_pattern_engine() -> PatternRecognitionEngine:
    """Get singleton pattern engine instance"""
    return PatternRecognitionEngine()
