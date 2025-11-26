"""
Services package - webMethods to Boomi Migration Accelerator

This package contains all backend services for:
- wMPublic service catalog (500+ services)
- Deep parser engine (node.ndf, flow.xml)
- Conversion engine (Boomi XML generation)
- Boomi API integration
- AI assistant

Services are imported on-demand to avoid circular dependencies.
"""

# Lazy imports - services loaded when accessed
def get_logging_service():
    from app.services.logging_service import LoggingService
    return LoggingService

def get_customer_service():
    from app.services.customer_service import CustomerService
    return CustomerService

def get_parser_service():
    from app.services.parser_service import WebMethodsParser
    return WebMethodsParser

def get_analysis_service():
    from app.services.analysis_service import AnalysisService
    return AnalysisService

def get_conversion_service():
    from app.services.conversion_service import ConversionService
    return ConversionService

def get_boomi_service():
    from app.services.boomi_service import BoomiAPIService
    return BoomiAPIService

def get_ai_service():
    from app.services.ai_service import AIService
    return AIService

def get_project_service():
    from app.services.project_service import ProjectService
    return ProjectService

def get_wmpublic_catalog():
    from app.services.wmpublic_master import WMPublicCatalog
    return WMPublicCatalog()

def get_deep_parser():
    from app.services.deep_parser_main import DeepPackageParser
    return DeepPackageParser

__all__ = [
    "get_logging_service",
    "get_customer_service",
    "get_parser_service",
    "get_analysis_service",
    "get_conversion_service",
    "get_boomi_service",
    "get_ai_service",
    "get_project_service",
    "get_wmpublic_catalog",
    "get_deep_parser",
]
