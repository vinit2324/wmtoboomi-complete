"""
REST API Orchestrator
=====================
Main orchestration service for converting REST API webMethods packages to Boomi.

Coordinates all generators and produces:
- Complete Boomi components (HTTP Connection, Operations, Profiles, Scripts)
- Implementation steps with effort estimation
- Automation percentage calculation

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import logging

from .rest_package_parser import (
    RESTPackageParser, 
    RESTPackageData,
    parse_rest_api_package
)
from .boomi_http_generator import (
    BoomiHTTPConnectionGenerator,
    BoomiHTTPOperationGenerator,
    BoomiDeploymentConfig,
    HTTPMethod
)
from .boomi_json_profile_generator import (
    BoomiJSONProfileGenerator,
    generate_error_response_profile
)
from .boomi_groovy_generator import (
    BoomiGroovyGenerator,
    convert_java_to_groovy
)
from .boomi_env_extensions_generator import (
    BoomiEnvExtensionsGenerator,
    generate_env_extensions_from_package
)

logger = logging.getLogger(__name__)


class AutomationLevel(str, Enum):
    AUTO = "AUTO"
    SEMI = "SEMI"
    MANUAL = "MANUAL"


class ComponentType(str, Enum):
    FOLDER = "folder"
    ENV_EXTENSION = "envExtension"
    HTTP_CONNECTION = "httpConnection"
    HTTP_OPERATION = "httpOperation"
    JSON_PROFILE = "jsonProfile"
    GROOVY_SCRIPT = "groovyScript"
    PROCESS = "process"
    API_SERVICE = "apiService"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


@dataclass
class ConversionResult:
    """Result of a single component conversion"""
    component_type: str
    name: str
    status: str
    automation_level: str
    effort_hours: float
    xml: str = ""
    groovy_code: str = ""
    warnings: List[str] = field(default_factory=list)
    manual_instructions: str = ""
    source_info: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'componentType': self.component_type,
            'name': self.name,
            'status': self.status,
            'automationLevel': self.automation_level,
            'effortHours': self.effort_hours,
            'xml': self.xml,
            'groovyCode': self.groovy_code,
            'warnings': self.warnings,
            'manualInstructions': self.manual_instructions,
            'sourceInfo': self.source_info
        }


@dataclass
class ImplementationStep:
    """Single implementation step"""
    step_number: int
    component_type: str
    name: str
    description: str
    automation_level: str
    effort_hours: float
    source_files: List[str] = field(default_factory=list)
    can_view: bool = True
    can_convert: bool = False
    can_download: bool = False
    can_push: bool = False
    conversion_result: Optional[ConversionResult] = None
    manual_instructions: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'stepNumber': self.step_number,
            'componentType': self.component_type,
            'name': self.name,
            'description': self.description,
            'automationLevel': self.automation_level,
            'effortHours': self.effort_hours,
            'sourceFiles': self.source_files,
            'canView': self.can_view,
            'canConvert': self.can_convert,
            'canDownload': self.can_download,
            'canPush': self.can_push,
            'conversionResult': self.conversion_result.to_dict() if self.conversion_result else None,
            'manualInstructions': self.manual_instructions
        }


@dataclass
class ConversionSummary:
    """Summary of complete package conversion"""
    package_name: str
    package_type: str
    total_steps: int
    auto_steps: int
    semi_steps: int
    manual_steps: int
    total_effort_hours: float
    manual_baseline_hours: float
    automation_percentage: int
    
    def to_dict(self) -> Dict:
        return {
            'packageName': self.package_name,
            'packageType': self.package_type,
            'totalSteps': self.total_steps,
            'autoSteps': self.auto_steps,
            'semiSteps': self.semi_steps,
            'manualSteps': self.manual_steps,
            'totalEffortHours': self.total_effort_hours,
            'manualBaselineHours': self.manual_baseline_hours,
            'automationPercentage': self.automation_percentage,
            'effortSavedHours': self.manual_baseline_hours - self.total_effort_hours
        }


class RESTAPIOrchestrator:
    """
    Main orchestrator for REST API package conversion.
    """
    
    # Manual baseline hours for REST API package (without accelerator)
    MANUAL_BASELINE_HOURS = 42.0
    
    def __init__(self, deployment_config: Optional[Dict] = None):
        if deployment_config:
            self.config = BoomiDeploymentConfig(**deployment_config)
        else:
            self.config = BoomiDeploymentConfig()
        
        self.http_conn_gen = BoomiHTTPConnectionGenerator(self.config)
        self.http_op_gen = BoomiHTTPOperationGenerator(self.config)
        self.profile_gen = BoomiJSONProfileGenerator(self.config)
        self.groovy_gen = BoomiGroovyGenerator()
        self.env_gen = BoomiEnvExtensionsGenerator(self.config)
    
    def convert_package(self, zip_path: str) -> Dict[str, Any]:
        """
        Convert complete REST API package to Boomi components.
        """
        logger.info(f"Starting REST API package conversion: {zip_path}")
        
        # Parse package
        with RESTPackageParser(zip_path) as parser:
            package_data = parser.parse()
        
        # Generate all components
        results = {
            'packageName': package_data.package_name,
            'packageType': 'REST_API',
            'parsedData': package_data.to_dict(),
            'components': {},
            'implementationSteps': [],
            'summary': {}
        }
        
        # 1. Environment Extensions (AUTO - 100%)
        env_result = self._generate_env_extensions(package_data)
        results['components']['envExtension'] = env_result.to_dict()
        
        # 2. HTTP Connection (AUTO - 100%)
        conn_result = self._generate_http_connection(package_data)
        results['components']['httpConnection'] = conn_result.to_dict()
        
        # 3. HTTP Operations (AUTO - 90%)
        op_results = self._generate_http_operations(package_data)
        results['components']['httpOperations'] = [r.to_dict() for r in op_results]
        
        # 4. JSON Profiles (AUTO - 95%)
        profile_results = self._generate_json_profiles(package_data)
        results['components']['jsonProfiles'] = [r.to_dict() for r in profile_results]
        
        # 5. Groovy Scripts (SEMI - 50-70%)
        script_results = self._generate_groovy_scripts(package_data)
        results['components']['groovyScripts'] = [r.to_dict() for r in script_results]
        
        # Generate implementation steps
        all_results = [env_result, conn_result] + op_results + profile_results + script_results
        steps = self._generate_implementation_steps(package_data, all_results)
        results['implementationSteps'] = [s.to_dict() for s in steps]
        
        # Calculate summary
        summary = self._calculate_summary(package_data.package_name, steps)
        results['summary'] = summary.to_dict()
        
        logger.info(f"Conversion complete: {summary.automation_percentage}% automation")
        
        return results
    
    def _generate_env_extensions(self, package_data: RESTPackageData) -> ConversionResult:
        """Generate Environment Extensions component"""
        try:
            all_properties = []
            seen = set()
            
            for var in package_data.global_variables:
                var_dict = var.to_dict()
                if var_dict['name'] not in seen:
                    seen.add(var_dict['name'])
                    all_properties.append(self.env_gen.extract_from_global_variables([var_dict])[0])
            
            for java_svc in package_data.java_services:
                for prop in self.env_gen.extract_from_java_code(java_svc.code):
                    if prop.name not in seen:
                        seen.add(prop.name)
                        all_properties.append(prop)
            
            for prop in self.env_gen.get_standard_rest_properties():
                if prop.name not in seen:
                    seen.add(prop.name)
                    all_properties.append(prop)
            
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '', package_data.package_name)
            component_name = f"Props_{clean_name}_Config"
            
            xml = self.env_gen.generate(
                name=component_name,
                properties=all_properties,
                description=f"Environment Extensions for {package_data.package_name}"
            )
            
            return ConversionResult(
                component_type=ComponentType.ENV_EXTENSION.value,
                name=component_name,
                status='success',
                automation_level=AutomationLevel.AUTO.value,
                effort_hours=0,
                xml=xml,
                source_info=f"Extracted {len(all_properties)} properties"
            )
            
        except Exception as e:
            logger.error(f"Error generating env extensions: {e}")
            return ConversionResult(
                component_type=ComponentType.ENV_EXTENSION.value,
                name="Environment_Extensions",
                status='error',
                automation_level=AutomationLevel.MANUAL.value,
                effort_hours=1.0,
                warnings=[str(e)]
            )
    
    def _generate_http_connection(self, package_data: RESTPackageData) -> ConversionResult:
        """Generate HTTP Connection component"""
        try:
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '', package_data.package_name)
            conn_name = f"Conn_HTTP_{clean_name}"
            
            base_url = "${env.BASE_URL}"
            
            xml = self.http_conn_gen.generate(
                name=conn_name,
                base_url=base_url,
                description=f"HTTP Connection for {package_data.package_name} - Migrated from webMethods"
            )
            
            return ConversionResult(
                component_type=ComponentType.HTTP_CONNECTION.value,
                name=conn_name,
                status='success',
                automation_level=AutomationLevel.AUTO.value,
                effort_hours=0,
                xml=xml,
                source_info="Generated from REST API package analysis"
            )
            
        except Exception as e:
            logger.error(f"Error generating HTTP connection: {e}")
            return ConversionResult(
                component_type=ComponentType.HTTP_CONNECTION.value,
                name="HTTP_Connection",
                status='error',
                automation_level=AutomationLevel.MANUAL.value,
                effort_hours=1.0,
                warnings=[str(e)]
            )
    
    def _generate_http_operations(self, package_data: RESTPackageData) -> List[ConversionResult]:
        """Generate HTTP Operation components"""
        results = []
        
        for resource in package_data.rest_resources:
            for operation in resource.operations:
                try:
                    path_clean = operation.path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
                    op_name = f"Op_{operation.method}_{path_clean or 'API'}"
                    
                    xml = self.http_op_gen.generate(
                        name=op_name,
                        method=HTTPMethod(operation.method),
                        description=f"{operation.method} operation for {operation.path}",
                        resource_path=operation.path,
                        request_content_type=operation.consumes,
                        response_content_type=operation.produces
                    )
                    
                    results.append(ConversionResult(
                        component_type=ComponentType.HTTP_OPERATION.value,
                        name=op_name,
                        status='success',
                        automation_level=AutomationLevel.AUTO.value,
                        effort_hours=0,
                        xml=xml,
                        source_info=f"{operation.method} {operation.path} → {operation.service_name}"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error generating operation {operation.path}: {e}")
                    results.append(ConversionResult(
                        component_type=ComponentType.HTTP_OPERATION.value,
                        name=f"Op_{operation.method}",
                        status='warning',
                        automation_level=AutomationLevel.SEMI.value,
                        effort_hours=0.5,
                        warnings=[str(e)]
                    ))
        
        if not results:
            xml = self.http_op_gen.generate(
                name="Op_GET_Default",
                method=HTTPMethod.GET,
                description="Default HTTP GET operation"
            )
            results.append(ConversionResult(
                component_type=ComponentType.HTTP_OPERATION.value,
                name="Op_GET_Default",
                status='success',
                automation_level=AutomationLevel.AUTO.value,
                effort_hours=0,
                xml=xml,
                source_info="Default operation - no REST resources detected"
            ))
        
        return results
    
    def _generate_json_profiles(self, package_data: RESTPackageData) -> List[ConversionResult]:
        """Generate JSON Profile components"""
        results = []
        
        for sig_name, signature in package_data.service_signatures.items():
            sig_dict = signature.to_dict()
            
            if sig_dict['inputs']:
                try:
                    profile_name = f"Profile_{sig_name}_Request"
                    fields = sig_dict['inputs']
                    
                    self.profile_gen.key_counter = 1
                    xml = self.profile_gen.generate(
                        name=profile_name,
                        fields=fields,
                        description=f"Request profile for {sig_name} - from webMethods sig_in"
                    )
                    
                    results.append(ConversionResult(
                        component_type=ComponentType.JSON_PROFILE.value,
                        name=profile_name,
                        status='success',
                        automation_level=AutomationLevel.AUTO.value,
                        effort_hours=0,
                        xml=xml,
                        source_info=f"Generated from {sig_name} sig_in ({len(fields)} fields)"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error generating request profile for {sig_name}: {e}")
            
            if sig_dict['outputs']:
                try:
                    profile_name = f"Profile_{sig_name}_Response"
                    fields = sig_dict['outputs']
                    
                    self.profile_gen.key_counter = 1
                    xml = self.profile_gen.generate(
                        name=profile_name,
                        fields=fields,
                        description=f"Response profile for {sig_name} - from webMethods sig_out"
                    )
                    
                    results.append(ConversionResult(
                        component_type=ComponentType.JSON_PROFILE.value,
                        name=profile_name,
                        status='success',
                        automation_level=AutomationLevel.AUTO.value,
                        effort_hours=0,
                        xml=xml,
                        source_info=f"Generated from {sig_name} sig_out ({len(fields)} fields)"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error generating response profile for {sig_name}: {e}")
        
        try:
            error_xml = generate_error_response_profile({
                'folder_id': self.config.folder_id,
                'folder_name': self.config.folder_name,
                'folder_full_path': self.config.folder_full_path,
                'branch_id': self.config.branch_id,
                'branch_name': self.config.branch_name,
                'created_by': self.config.created_by,
                'modified_by': self.config.modified_by
            })
            
            results.append(ConversionResult(
                component_type=ComponentType.JSON_PROFILE.value,
                name="Profile_Error_Response",
                status='success',
                automation_level=AutomationLevel.AUTO.value,
                effort_hours=0,
                xml=error_xml,
                source_info="Standard error response profile"
            ))
        except Exception as e:
            logger.warning(f"Error generating error profile: {e}")
        
        return results
    
    def _generate_groovy_scripts(self, package_data: RESTPackageData) -> List[ConversionResult]:
        """Generate Groovy scripts from Java services"""
        results = []
        
        for java_svc in package_data.java_services:
            try:
                conversion = self.groovy_gen.convert(java_svc.code, java_svc.name)
                
                script_name = f"Script_{java_svc.name}"
                
                results.append(ConversionResult(
                    component_type=ComponentType.GROOVY_SCRIPT.value,
                    name=script_name,
                    status='success' if conversion.confidence >= 70 else 'warning',
                    automation_level=conversion.automation_level,
                    effort_hours=0 if conversion.confidence >= 80 else 0.5,
                    groovy_code=conversion.groovy_code,
                    warnings=conversion.warnings + conversion.manual_review_items,
                    source_info=f"Converted from {java_svc.name} (Confidence: {conversion.confidence}%)"
                ))
                
            except Exception as e:
                logger.warning(f"Error converting Java service {java_svc.name}: {e}")
                results.append(ConversionResult(
                    component_type=ComponentType.GROOVY_SCRIPT.value,
                    name=f"Script_{java_svc.name}",
                    status='error',
                    automation_level=AutomationLevel.MANUAL.value,
                    effort_hours=2.0,
                    warnings=[str(e)]
                ))
        
        variables = [v.name for v in package_data.global_variables]
        
        for script_type in ['coordinates', 'zip', 'store_id']:
            try:
                groovy_code = self.groovy_gen.generate_url_builder_script(script_type, variables)
                script_name = f"Script_URLBuilder_{script_type.title().replace('_', '')}"
                
                results.append(ConversionResult(
                    component_type=ComponentType.GROOVY_SCRIPT.value,
                    name=script_name,
                    status='success',
                    automation_level=AutomationLevel.AUTO.value,
                    effort_hours=0,
                    groovy_code=groovy_code,
                    source_info="Generated URL builder template"
                ))
                
            except Exception as e:
                logger.warning(f"Error generating URL builder {script_type}: {e}")
        
        return results
    
    def _generate_implementation_steps(
        self,
        package_data: RESTPackageData,
        conversion_results: List[ConversionResult]
    ) -> List[ImplementationStep]:
        """Generate ordered implementation steps"""
        steps = []
        step_num = 0
        
        # Step 1: Folder Creation (MANUAL - trivial)
        step_num += 1
        steps.append(ImplementationStep(
            step_number=step_num,
            component_type=ComponentType.FOLDER.value,
            name="Create Folder Structure",
            description="Create Boomi folder structure for migrated components",
            automation_level=AutomationLevel.MANUAL.value,
            effort_hours=0.1,
            can_view=True,
            can_convert=False,
            manual_instructions="""1. Log into Boomi AtomSphere
2. Navigate to Build > Component Explorer
3. Right-click your account folder > New Folder
4. Create main folder (e.g., "YourProject")
5. Create subfolders: Connections, Profiles, Processes, Scripts, API"""
        ))
        
        # Step 2: Environment Extensions (AUTO)
        step_num += 1
        env_result = next((r for r in conversion_results if r.component_type == 'envExtension'), None)
        steps.append(ImplementationStep(
            step_number=step_num,
            component_type=ComponentType.ENV_EXTENSION.value,
            name="Create Environment Extensions",
            description="Process Property Component for environment-specific configurations",
            automation_level=AutomationLevel.AUTO.value,
            effort_hours=0,
            can_view=True,
            can_convert=True,
            can_download=True,
            can_push=True,
            conversion_result=env_result
        ))
        
        # Step 3: HTTP Connection (AUTO)
        step_num += 1
        conn_result = next((r for r in conversion_results if r.component_type == 'httpConnection'), None)
        steps.append(ImplementationStep(
            step_number=step_num,
            component_type=ComponentType.HTTP_CONNECTION.value,
            name="Create HTTP Connection",
            description="HTTP Client connection with base URL from Environment Extensions",
            automation_level=AutomationLevel.AUTO.value,
            effort_hours=0,
            can_view=True,
            can_convert=True,
            can_download=True,
            can_push=True,
            conversion_result=conn_result
        ))
        
        # HTTP Operations
        op_results = [r for r in conversion_results if r.component_type == 'httpOperation']
        for op_result in op_results:
            step_num += 1
            steps.append(ImplementationStep(
                step_number=step_num,
                component_type=ComponentType.HTTP_OPERATION.value,
                name=f"Create HTTP Operation: {op_result.name}",
                description=op_result.source_info or "HTTP Operation",
                automation_level=op_result.automation_level,
                effort_hours=op_result.effort_hours,
                can_view=True,
                can_convert=True,
                can_download=True,
                can_push=True,
                conversion_result=op_result
            ))
        
        # JSON Profiles
        profile_results = [r for r in conversion_results if r.component_type == 'jsonProfile']
        for profile_result in profile_results:
            step_num += 1
            steps.append(ImplementationStep(
                step_number=step_num,
                component_type=ComponentType.JSON_PROFILE.value,
                name=f"Create JSON Profile: {profile_result.name}",
                description=profile_result.source_info or "JSON Profile",
                automation_level=profile_result.automation_level,
                effort_hours=profile_result.effort_hours,
                can_view=True,
                can_convert=True,
                can_download=True,
                can_push=True,
                conversion_result=profile_result
            ))
        
        # Groovy Scripts
        script_results = [r for r in conversion_results if r.component_type == 'groovyScript']
        for script_result in script_results:
            step_num += 1
            steps.append(ImplementationStep(
                step_number=step_num,
                component_type=ComponentType.GROOVY_SCRIPT.value,
                name=f"Create Groovy Script: {script_result.name}",
                description=script_result.source_info or "Groovy Script",
                automation_level=script_result.automation_level,
                effort_hours=script_result.effort_hours,
                can_view=True,
                can_convert=True,
                can_download=True,
                can_push=False,
                conversion_result=script_result
            ))
        
        # Process Creation (SEMI)
        for flow_svc in package_data.flow_services:
            step_num += 1
            complexity = flow_svc.complexity
            effort = 1.0 if complexity == 'low' else 2.0 if complexity == 'medium' else 4.0
            
            steps.append(ImplementationStep(
                step_number=step_num,
                component_type=ComponentType.PROCESS.value,
                name=f"Create Process: {flow_svc.name}",
                description=f"Build Boomi process from flow service (Complexity: {complexity})",
                automation_level=AutomationLevel.SEMI.value,
                effort_hours=effort,
                source_files=[flow_svc.path],
                can_view=True,
                can_convert=True,
                can_download=True,
                can_push=False,
                manual_instructions=f"""Process Flow Design based on {flow_svc.name}:
1. Add Start shape
2. Add Set Properties shape (link Environment Extensions)
3. Add Decision shape for routing (if multiple paths)
4. Add Data Process shapes with Groovy scripts
5. Add HTTP Connector shape (link Connection and Operation)
6. Add Try/Catch for error handling
7. Add Stop shape

Invocations detected: {', '.join(flow_svc.invocations[:5])}..."""
            ))
        
        # API Service Component (SEMI)
        if package_data.rest_resources:
            step_num += 1
            steps.append(ImplementationStep(
                step_number=step_num,
                component_type=ComponentType.API_SERVICE.value,
                name="Configure API Service Component",
                description="Create API Service to expose REST endpoints",
                automation_level=AutomationLevel.SEMI.value,
                effort_hours=1.0,
                can_view=True,
                can_convert=False,
                manual_instructions=f"""1. Create new API Service Component
2. Set Base Path (e.g., /api)
3. Configure endpoints from REST resources
4. Link each endpoint to corresponding Process
5. Configure authentication as required"""
            ))
        
        # Testing (MANUAL)
        step_num += 1
        steps.append(ImplementationStep(
            step_number=step_num,
            component_type=ComponentType.TESTING.value,
            name="Testing & Validation",
            description="Test all components and validate functionality",
            automation_level=AutomationLevel.MANUAL.value,
            effort_hours=6.0,
            can_view=True,
            can_convert=False,
            manual_instructions="""1. Unit test each Groovy script in Test Mode
2. Test HTTP Connection connectivity
3. Test HTTP Operations with sample requests
4. Test complete process execution
5. Validate API responses match original webMethods output
6. Performance testing under load
7. Error handling validation"""
        ))
        
        # Deployment (MANUAL)
        step_num += 1
        steps.append(ImplementationStep(
            step_number=step_num,
            component_type=ComponentType.DEPLOYMENT.value,
            name="Deployment",
            description="Deploy to target environments (DEV, QA, PROD)",
            automation_level=AutomationLevel.MANUAL.value,
            effort_hours=3.0,
            can_view=True,
            can_convert=False,
            manual_instructions="""1. Create Packaged Component with all components
2. Deploy to DEV environment
3. Configure Environment Extensions values for DEV
4. Validate in DEV
5. Promote to QA, configure extensions, validate
6. Promote to PROD, configure extensions, validate
7. Set up monitoring and alerting"""
        ))
        
        return steps
    
    def _calculate_summary(
        self,
        package_name: str,
        steps: List[ImplementationStep]
    ) -> ConversionSummary:
        """Calculate conversion summary with effort and automation metrics"""
        auto_count = sum(1 for s in steps if s.automation_level == AutomationLevel.AUTO.value)
        semi_count = sum(1 for s in steps if s.automation_level == AutomationLevel.SEMI.value)
        manual_count = sum(1 for s in steps if s.automation_level == AutomationLevel.MANUAL.value)
        
        total_effort = sum(s.effort_hours for s in steps)
        
        effort_saved = self.MANUAL_BASELINE_HOURS - total_effort
        automation_pct = int((effort_saved / self.MANUAL_BASELINE_HOURS) * 100)
        automation_pct = max(0, min(100, automation_pct))
        
        return ConversionSummary(
            package_name=package_name,
            package_type='REST_API',
            total_steps=len(steps),
            auto_steps=auto_count,
            semi_steps=semi_count,
            manual_steps=manual_count,
            total_effort_hours=total_effort,
            manual_baseline_hours=self.MANUAL_BASELINE_HOURS,
            automation_percentage=automation_pct
        )


def convert_rest_api_package(
    zip_path: str,
    deployment_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """Factory function to convert REST API package."""
    orchestrator = RESTAPIOrchestrator(deployment_config)
    return orchestrator.convert_package(zip_path)


def generate_implementation_steps(
    package_data: Dict[str, Any],
    deployment_config: Optional[Dict] = None
) -> List[Dict]:
    """Generate implementation steps from parsed package data."""
    orchestrator = RESTAPIOrchestrator(deployment_config)
    
    return [
        {
            'stepNumber': 1,
            'componentType': 'folder',
            'name': 'Create Folder Structure',
            'automationLevel': 'MANUAL',
            'effortHours': 0.1
        },
        {
            'stepNumber': 2,
            'componentType': 'envExtension',
            'name': 'Create Environment Extensions',
            'automationLevel': 'AUTO',
            'effortHours': 0
        },
    ]
