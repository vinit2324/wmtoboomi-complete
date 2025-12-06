"""
REST API Converter Module
=========================
Converts webMethods REST API packages to Boomi components.

Author: Jade Global Inc.
Version: 2.0.0
"""

from .rest_package_parser import (
    RESTPackageParser,
    RESTPackageData,
    RESTResource,
    RESTOperation,
    ServiceSignature,
    SignatureField,
    JavaService,
    FlowService,
    GlobalVariable,
    parse_rest_api_package
)

from .boomi_http_generator import (
    BoomiHTTPConnectionGenerator,
    BoomiHTTPOperationGenerator,
    BoomiDeploymentConfig,
    AuthenticationType,
    HTTPMethod,
    generate_http_connection_xml,
    generate_http_operation_xml
)

from .boomi_json_profile_generator import (
    BoomiJSONProfileGenerator,
    generate_json_profile_from_signature,
    generate_request_response_profiles,
    generate_error_response_profile
)

from .boomi_groovy_generator import (
    BoomiGroovyGenerator,
    GroovyConversionResult,
    convert_java_to_groovy,
    generate_url_builder_scripts
)

from .boomi_env_extensions_generator import (
    BoomiEnvExtensionsGenerator,
    EnvironmentProperty,
    generate_environment_extensions_xml,
    generate_env_extensions_from_package
)

from .rest_api_orchestrator import (
    RESTAPIOrchestrator,
    ConversionResult,
    ImplementationStep,
    ConversionSummary,
    AutomationLevel,
    ComponentType,
    convert_rest_api_package,
    generate_implementation_steps
)

__all__ = [
    # Parser
    'RESTPackageParser',
    'RESTPackageData',
    'RESTResource',
    'RESTOperation',
    'ServiceSignature',
    'SignatureField',
    'JavaService',
    'FlowService',
    'GlobalVariable',
    'parse_rest_api_package',
    
    # HTTP Generator
    'BoomiHTTPConnectionGenerator',
    'BoomiHTTPOperationGenerator',
    'BoomiDeploymentConfig',
    'AuthenticationType',
    'HTTPMethod',
    'generate_http_connection_xml',
    'generate_http_operation_xml',
    
    # JSON Profile Generator
    'BoomiJSONProfileGenerator',
    'generate_json_profile_from_signature',
    'generate_request_response_profiles',
    'generate_error_response_profile',
    
    # Groovy Generator
    'BoomiGroovyGenerator',
    'GroovyConversionResult',
    'convert_java_to_groovy',
    'generate_url_builder_scripts',
    
    # Environment Extensions Generator
    'BoomiEnvExtensionsGenerator',
    'EnvironmentProperty',
    'generate_environment_extensions_xml',
    'generate_env_extensions_from_package',
    
    # Orchestrator
    'RESTAPIOrchestrator',
    'ConversionResult',
    'ImplementationStep',
    'ConversionSummary',
    'AutomationLevel',
    'ComponentType',
    'convert_rest_api_package',
    'generate_implementation_steps'
]
