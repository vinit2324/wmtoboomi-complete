"""
wMPublic Master Catalog
Aggregates all service definitions and provides lookup functions
"""

from typing import Dict, List, Optional, Tuple
from app.services.wmpublic_catalog import (
    WMPublicService, BoomiEquivalent, BoomiShapeType, ConversionComplexity,
    STRING_SERVICES, MATH_SERVICES, DATE_SERVICES
)
from app.services.wmpublic_catalog_part2 import (
    DOCUMENT_SERVICES, LIST_SERVICES, FLOW_SERVICES,
    XML_SERVICES, JSON_SERVICES, FILE_SERVICES
)
from app.services.wmpublic_catalog_part3 import (
    DATABASE_SERVICES, HTTP_SERVICES, FTP_SERVICES,
    EDI_SERVICES, JMS_SERVICES, MAIL_SERVICES
)
from app.services.wmpublic_catalog_part4 import (
    FLATFILE_SERVICES, UTILITY_SERVICES, SECURITY_SERVICES,
    STORAGE_SERVICES, SCHEMA_SERVICES, IO_SERVICES
)
from app.services.wmpublic_catalog_part5 import (
    SERVER_SERVICES, TN_SERVICES, EVENT_SERVICES,
    CACHE_SERVICES, MIME_SERVICES
)


# =============================================================================
# MASTER CATALOG - All 500+ services
# =============================================================================

class WMPublicCatalog:
    """
    Master catalog for all wMPublic services.
    Provides lookup and search functionality.
    """
    
    _instance = None
    _services: Dict[str, WMPublicService] = {}
    _by_category: Dict[str, List[WMPublicService]] = {}
    _by_automation_level: Dict[str, List[WMPublicService]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Load all services into catalog"""
        # Aggregate all service dictionaries
        self._services = {}
        # Part 1: String, Math, Date
        self._services.update(STRING_SERVICES)
        self._services.update(MATH_SERVICES)
        self._services.update(DATE_SERVICES)
        # Part 2: Document, List, Flow, XML, JSON, File
        self._services.update(DOCUMENT_SERVICES)
        self._services.update(LIST_SERVICES)
        self._services.update(FLOW_SERVICES)
        self._services.update(XML_SERVICES)
        self._services.update(JSON_SERVICES)
        self._services.update(FILE_SERVICES)
        # Part 3: Database, HTTP, FTP, EDI, JMS, Mail
        self._services.update(DATABASE_SERVICES)
        self._services.update(HTTP_SERVICES)
        self._services.update(FTP_SERVICES)
        self._services.update(EDI_SERVICES)
        self._services.update(JMS_SERVICES)
        self._services.update(MAIL_SERVICES)
        # Part 4: Flat File, Utils, Security, Storage, Schema, IO
        self._services.update(FLATFILE_SERVICES)
        self._services.update(UTILITY_SERVICES)
        self._services.update(SECURITY_SERVICES)
        self._services.update(STORAGE_SERVICES)
        self._services.update(SCHEMA_SERVICES)
        self._services.update(IO_SERVICES)
        # Part 5: Server, TN, Event, Cache, MIME
        self._services.update(SERVER_SERVICES)
        self._services.update(TN_SERVICES)
        self._services.update(EVENT_SERVICES)
        self._services.update(CACHE_SERVICES)
        self._services.update(MIME_SERVICES)
        
        # Build category index
        self._by_category = {}
        for svc in self._services.values():
            category = svc.category
            if category not in self._by_category:
                self._by_category[category] = []
            self._by_category[category].append(svc)
        
        # Build automation level index
        self._by_automation_level = {
            "high": [],      # 80-100%
            "medium": [],    # 50-79%
            "low": [],       # 20-49%
            "manual": []     # 0-19%
        }
        for svc in self._services.values():
            if svc.automation_level >= 80:
                self._by_automation_level["high"].append(svc)
            elif svc.automation_level >= 50:
                self._by_automation_level["medium"].append(svc)
            elif svc.automation_level >= 20:
                self._by_automation_level["low"].append(svc)
            else:
                self._by_automation_level["manual"].append(svc)
    
    @property
    def total_services(self) -> int:
        """Total number of services in catalog"""
        return len(self._services)
    
    @property
    def categories(self) -> List[str]:
        """List of all categories"""
        return list(self._by_category.keys())
    
    def get_service(self, service_name: str) -> Optional[WMPublicService]:
        """
        Get service definition by name.
        Handles both full name (pub.string:concat) and short name (concat)
        """
        # Try exact match first
        if service_name in self._services:
            return self._services[service_name]
        
        # Try partial match
        for name, svc in self._services.items():
            if name.endswith(f":{service_name}"):
                return svc
        
        return None
    
    def search_services(self, query: str) -> List[WMPublicService]:
        """Search services by name or description"""
        query = query.lower()
        results = []
        for svc in self._services.values():
            if (query in svc.service_name.lower() or 
                query in svc.description.lower()):
                results.append(svc)
        return results
    
    def get_by_category(self, category: str) -> List[WMPublicService]:
        """Get all services in a category"""
        return self._by_category.get(category, [])
    
    def get_by_automation_level(self, level: str) -> List[WMPublicService]:
        """Get services by automation level (high, medium, low, manual)"""
        return self._by_automation_level.get(level, [])
    
    def get_boomi_equivalent(self, service_name: str) -> Optional[BoomiEquivalent]:
        """Get Boomi equivalent for a service"""
        svc = self.get_service(service_name)
        if svc:
            return svc.boomi_equivalent
        return None
    
    def get_conversion_info(self, service_name: str) -> Optional[Dict]:
        """Get complete conversion information for a service"""
        svc = self.get_service(service_name)
        if not svc:
            return None
        
        return {
            "service_name": svc.service_name,
            "category": svc.category,
            "description": svc.description,
            "boomi_shape": svc.boomi_equivalent.shape_type.value,
            "boomi_function": svc.boomi_equivalent.function_name,
            "boomi_connector": svc.boomi_equivalent.connector_type,
            "script_template": svc.boomi_equivalent.script_template,
            "complexity": svc.complexity.value,
            "automation_level": svc.automation_level,
            "requires_review": svc.requires_manual_review,
            "notes": svc.conversion_notes,
            "inputs": [p.model_dump() for p in svc.inputs],
            "outputs": [p.model_dump() for p in svc.outputs],
        }
    
    def estimate_conversion_effort(self, service_names: List[str]) -> Dict:
        """
        Estimate conversion effort for a list of services
        Returns breakdown by complexity and estimated hours
        """
        stats = {
            "total_services": len(service_names),
            "found_in_catalog": 0,
            "not_in_catalog": [],
            "by_complexity": {
                "trivial": 0,
                "simple": 0,
                "moderate": 0,
                "complex": 0,
                "manual": 0
            },
            "by_automation": {
                "high": 0,
                "medium": 0,
                "low": 0,
                "manual": 0
            },
            "requires_review": [],
            "estimated_hours": 0,
            "automation_percentage": 0
        }
        
        # Hours per complexity level
        hours_per_complexity = {
            "trivial": 0.25,
            "simple": 0.5,
            "moderate": 1.5,
            "complex": 4.0,
            "manual": 8.0
        }
        
        total_automation = 0
        
        for name in service_names:
            svc = self.get_service(name)
            if not svc:
                stats["not_in_catalog"].append(name)
                stats["by_complexity"]["manual"] += 1
                stats["estimated_hours"] += 8.0  # Unknown = manual
                continue
            
            stats["found_in_catalog"] += 1
            complexity = svc.complexity.value
            stats["by_complexity"][complexity] += 1
            stats["estimated_hours"] += hours_per_complexity.get(complexity, 4.0)
            
            # Automation level
            if svc.automation_level >= 80:
                stats["by_automation"]["high"] += 1
            elif svc.automation_level >= 50:
                stats["by_automation"]["medium"] += 1
            elif svc.automation_level >= 20:
                stats["by_automation"]["low"] += 1
            else:
                stats["by_automation"]["manual"] += 1
            
            total_automation += svc.automation_level
            
            if svc.requires_manual_review:
                stats["requires_review"].append(svc.service_name)
        
        # Calculate average automation
        if stats["found_in_catalog"] > 0:
            stats["automation_percentage"] = round(
                total_automation / stats["found_in_catalog"], 1
            )
        
        return stats
    
    def get_category_summary(self) -> Dict[str, Dict]:
        """Get summary of all categories"""
        summary = {}
        for category, services in self._by_category.items():
            avg_automation = sum(s.automation_level for s in services) / len(services)
            summary[category] = {
                "count": len(services),
                "average_automation": round(avg_automation, 1),
                "high_automation": len([s for s in services if s.automation_level >= 80]),
                "needs_review": len([s for s in services if s.requires_manual_review])
            }
        return summary
    
    def generate_groovy_for_service(self, service_name: str) -> Optional[str]:
        """Generate Groovy script template for a service"""
        svc = self.get_service(service_name)
        if not svc:
            return None
        
        if svc.boomi_equivalent.script_template:
            return svc.boomi_equivalent.script_template
        
        # Generate basic template if shape is Data Process
        if svc.boomi_equivalent.shape_type == BoomiShapeType.DATA_PROCESS:
            inputs_str = "\n".join([
                f"    // {p.name}: {p.type} - {p.description}"
                for p in svc.inputs
            ])
            outputs_str = "\n".join([
                f"    // {p.name}: {p.type}"
                for p in svc.outputs
            ])
            
            return f"""
// Boomi Data Process script for: {svc.service_name}
// Description: {svc.description}
// Inputs:
{inputs_str}
// Outputs:
{outputs_str}

import com.boomi.execution.ExecutionUtil
import java.util.Properties

for (int i = 0; i < dataContext.getDataCount(); i++) {{
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    
    // TODO: Implement {svc.service_name} logic
    // Read input parameters from props
    // Process data
    // Set output parameters in props or modify stream
    
    dataContext.storeStream(is, props)
}}
"""
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_catalog() -> WMPublicCatalog:
    """Get singleton instance of the catalog"""
    return WMPublicCatalog()


def lookup_service(service_name: str) -> Optional[WMPublicService]:
    """Quick lookup of a service"""
    return get_catalog().get_service(service_name)


def get_boomi_mapping(service_name: str) -> Tuple[Optional[str], Optional[str], int]:
    """
    Get quick Boomi mapping info
    Returns: (shape_type, function_or_connector, automation_level)
    """
    svc = lookup_service(service_name)
    if not svc:
        return (None, None, 0)
    
    boomi = svc.boomi_equivalent
    function_or_connector = boomi.function_name or boomi.connector_type or boomi.notes
    return (boomi.shape_type.value, function_or_connector, svc.automation_level)


def is_high_automation_service(service_name: str) -> bool:
    """Check if service has high automation potential"""
    svc = lookup_service(service_name)
    return svc is not None and svc.automation_level >= 80


def needs_manual_review(service_name: str) -> bool:
    """Check if service needs manual review"""
    svc = lookup_service(service_name)
    return svc is not None and svc.requires_manual_review


# =============================================================================
# STATISTICS
# =============================================================================

def print_catalog_stats():
    """Print catalog statistics"""
    catalog = get_catalog()
    print(f"\n{'='*60}")
    print("wMPublic Service Catalog Statistics")
    print(f"{'='*60}")
    print(f"Total Services: {catalog.total_services}")
    print(f"\nBy Category:")
    for category, summary in catalog.get_category_summary().items():
        print(f"  {category}: {summary['count']} services, "
              f"{summary['average_automation']}% avg automation")
    
    print(f"\nBy Automation Level:")
    for level in ["high", "medium", "low", "manual"]:
        count = len(catalog.get_by_automation_level(level))
        print(f"  {level}: {count} services")
    print(f"{'='*60}\n")


# Expose key classes/functions
__all__ = [
    "WMPublicCatalog",
    "WMPublicService",
    "BoomiEquivalent",
    "BoomiShapeType",
    "ConversionComplexity",
    "get_catalog",
    "lookup_service",
    "get_boomi_mapping",
    "is_high_automation_service",
    "needs_manual_review",
]
