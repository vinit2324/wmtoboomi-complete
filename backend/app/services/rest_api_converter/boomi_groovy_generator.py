"""
Boomi Groovy Script Generator
=============================
Converts webMethods Java services to Boomi Groovy scripts.

Handles common patterns:
- IData/Pipeline operations → Dynamic Process Properties
- GlobalVariables → Environment Extensions
- String manipulation
- URL building
- HTTP request preparation

Author: Jade Global Inc.
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


# Java to Groovy conversion patterns
JAVA_TO_GROOVY_PATTERNS = [
    # IData operations
    (r'IDataUtil\.getString\s*\(\s*\w+\s*,\s*["\']([^"\']+)["\']\s*\)', 
     r'ExecutionUtil.getDynamicProcessProperty("\1")'),
    (r'IDataUtil\.put\s*\(\s*\w+\s*,\s*["\']([^"\']+)["\']\s*,\s*([^)]+)\s*\)', 
     r'ExecutionUtil.setDynamicProcessProperty("\1", \2, false)'),
    (r'IDataUtil\.get\s*\(\s*\w+\s*,\s*["\']([^"\']+)["\']\s*\)',
     r'ExecutionUtil.getDynamicProcessProperty("\1")'),
    
    # Cursor operations (remove - not needed in Groovy)
    (r'IDataCursor\s+\w+\s*=\s*\w+\.getCursor\s*\(\s*\)\s*;', ''),
    (r'\w+\.destroy\s*\(\s*\)\s*;', ''),
    (r'IDataCursor\s+\w+\s*=\s*pipeline\.getCursor\s*\(\s*\)\s*;', ''),
    
    # Global Variables
    (r'GlobalVariables\.getString\s*\(\s*["\']([^"\']+)["\']\s*\)', 
     r'ExecutionUtil.getDynamicProcessProperty("\1")'),
    (r'GlobalVariables\.getValue\s*\(\s*["\']([^"\']+)["\']\s*\)',
     r'ExecutionUtil.getDynamicProcessProperty("\1")'),
    (r'ServerAPI\.getGlobalVariableValue\s*\(\s*["\']([^"\']+)["\']\s*\)',
     r'ExecutionUtil.getDynamicProcessProperty("\1")'),
    
    # Service context
    (r'Service\.getPackageName\s*\(\s*\)', '"${PACKAGE_NAME}"'),
    (r'Service\.getServiceName\s*\(\s*\)', '"${SERVICE_NAME}"'),
    
    # Null handling - Groovy style
    (r'(\w+)\s*==\s*null\s*\?\s*["\']([^"\']*)["\']?\s*:\s*\1', r'\1 ?: "\2"'),
    (r'if\s*\(\s*(\w+)\s*==\s*null\s*\)\s*\{\s*\1\s*=\s*["\']([^"\']*)["\'];\s*\}', r'\1 = \1 ?: "\2"'),
    (r'(\w+)\s*!=\s*null\s*&&\s*!\1\.isEmpty\s*\(\s*\)', r'\1'),
    
    # Type conversions
    (r'String\.valueOf\s*\(\s*([^)]+)\s*\)', r'\1.toString()'),
    (r'Integer\.parseInt\s*\(\s*([^)]+)\s*\)', r'\1.toInteger()'),
    (r'Integer\.valueOf\s*\(\s*([^)]+)\s*\)', r'\1.toInteger()'),
    (r'Double\.parseDouble\s*\(\s*([^)]+)\s*\)', r'\1.toDouble()'),
    (r'Boolean\.parseBoolean\s*\(\s*([^)]+)\s*\)', r'\1.toBoolean()'),
    
    # StringBuilder
    (r'new\s+StringBuilder\s*\(\s*\)', '""'),
    (r'(\w+)\.append\s*\(\s*([^)]+)\s*\)', r'\1 += \2'),
    (r'(\w+)\.toString\s*\(\s*\)', r'\1'),
    
    # Logging
    (r'ServerAPI\.logError\s*\(\s*([^)]+)\s*\)', r'ExecutionUtil.getBaseLogger().severe(\1)'),
    (r'JournalLogger\.log\s*\([^,]+,\s*[^,]+,\s*[^,]+,\s*([^)]+)\s*\)', 
     r'ExecutionUtil.getBaseLogger().info(\1)'),
]


@dataclass
class GroovyConversionResult:
    """Result of Java to Groovy conversion"""
    groovy_code: str
    confidence: int = 100
    automation_level: str = "AUTO"
    warnings: List[str] = field(default_factory=list)
    manual_review_items: List[str] = field(default_factory=list)
    patterns_applied: List[str] = field(default_factory=list)
    variables_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'groovyCode': self.groovy_code,
            'confidence': self.confidence,
            'automationLevel': self.automation_level,
            'warnings': self.warnings,
            'manualReviewItems': self.manual_review_items,
            'patternsApplied': self.patterns_applied,
            'variablesUsed': self.variables_used
        }


class BoomiGroovyGenerator:
    """
    Converts webMethods Java services to Boomi Groovy scripts.
    """
    
    def __init__(self):
        self.patterns_applied = []
        self.warnings = []
        self.manual_review_items = []
        self.variables_used = []
    
    def convert(self, java_code: str, service_name: str = "") -> GroovyConversionResult:
        """
        Convert Java service code to Groovy script.
        
        Args:
            java_code: Original Java service code
            service_name: Name of the service for context
            
        Returns:
            GroovyConversionResult with converted code and metadata
        """
        self.patterns_applied = []
        self.warnings = []
        self.manual_review_items = []
        self.variables_used = []
        
        groovy_code = java_code
        
        # Step 1: Add Boomi imports
        groovy_code = self._add_boomi_imports(groovy_code)
        
        # Step 2: Remove Java boilerplate
        groovy_code = self._remove_java_boilerplate(groovy_code)
        
        # Step 3: Apply conversion patterns
        groovy_code = self._apply_conversion_patterns(groovy_code)
        
        # Step 4: Simplify null checks
        groovy_code = self._simplify_null_checks(groovy_code)
        
        # Step 5: Convert string operations
        groovy_code = self._convert_string_operations(groovy_code)
        
        # Step 6: Extract and track variables
        self._extract_variables(groovy_code)
        
        # Step 7: Detect unsupported patterns
        self._detect_unsupported_patterns(groovy_code)
        
        # Step 8: Clean up code
        groovy_code = self._cleanup_code(groovy_code)
        
        # Calculate confidence
        confidence = self._calculate_confidence()
        automation_level = "AUTO" if confidence >= 80 else "SEMI" if confidence >= 50 else "MANUAL"
        
        return GroovyConversionResult(
            groovy_code=groovy_code,
            confidence=confidence,
            automation_level=automation_level,
            warnings=self.warnings,
            manual_review_items=self.manual_review_items,
            patterns_applied=self.patterns_applied,
            variables_used=self.variables_used
        )
    
    def _add_boomi_imports(self, code: str) -> str:
        """Add standard Boomi Groovy imports"""
        imports = '''import com.boomi.execution.ExecutionUtil
import java.util.Properties
import java.text.SimpleDateFormat
import java.net.URLEncoder
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

'''
        # Remove existing webMethods imports
        code = re.sub(r'import\s+com\.wm\..*?;\s*\n', '', code)
        code = re.sub(r'import\s+wm\..*?;\s*\n', '', code)
        code = re.sub(r'import\s+com\.softwareag\..*?;\s*\n', '', code)
        
        return imports + code
    
    def _remove_java_boilerplate(self, code: str) -> str:
        """Remove Java class/method boilerplate"""
        # Remove package declaration
        code = re.sub(r'package\s+[\w.]+\s*;', '', code)
        
        # Remove class declaration
        code = re.sub(r'public\s+(?:final\s+)?class\s+\w+\s*\{', '', code)
        
        # Remove static IDataKey declarations
        code = re.sub(r'public\s+static\s+final\s+IDataKey\s+\w+\s*=\s*[^;]+;', '', code)
        
        # Convert main method signature
        code = re.sub(
            r'public\s+static\s+(?:final\s+)?void\s+\w+\s*\(\s*IData\s+pipeline\s*\)\s*(?:throws\s+[\w,\s]+\s*)?\{',
            '// Main script logic',
            code
        )
        
        # Remove trailing class brace
        code = re.sub(r'\}\s*$', '', code.rstrip())
        
        self.patterns_applied.append("Removed Java boilerplate")
        return code
    
    def _apply_conversion_patterns(self, code: str) -> str:
        """Apply all Java to Groovy conversion patterns"""
        for pattern, replacement in JAVA_TO_GROOVY_PATTERNS:
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                self.patterns_applied.append(f"Applied pattern: {pattern[:40]}...")
        
        return code
    
    def _simplify_null_checks(self, code: str) -> str:
        """Simplify null checks to Groovy style"""
        # Convert if-null-then-default to Elvis operator
        code = re.sub(
            r'if\s*\(\s*(\w+)\s*==\s*null\s*\|\|\s*\1\.isEmpty\s*\(\s*\)\s*\)\s*\{\s*\1\s*=\s*([^;]+);\s*\}',
            r'\1 = \1 ?: \2',
            code
        )
        
        # Convert ternary null checks
        code = re.sub(
            r'(\w+)\s*!=\s*null\s*\?\s*\1\s*:\s*([^;]+)',
            r'\1 ?: \2',
            code
        )
        
        return code
    
    def _convert_string_operations(self, code: str) -> str:
        """Convert Java string operations to Groovy"""
        # String concatenation to GString where possible
        code = re.sub(
            r'"([^"]*?)"\s*\+\s*(\w+)\s*\+\s*"([^"]*?)"',
            r'"\1${\2}\3"',
            code
        )
        
        return code
    
    def _extract_variables(self, code: str) -> None:
        """Extract Dynamic Process Property variables used"""
        dpp_pattern = r'getDynamicProcessProperty\s*\(\s*["\']([^"\']+)["\']\s*\)'
        matches = re.findall(dpp_pattern, code)
        self.variables_used = list(set(matches))
    
    def _detect_unsupported_patterns(self, code: str) -> None:
        """Detect patterns that need manual review"""
        unsupported = [
            (r'Session\.', 'Session object - needs manual conversion'),
            (r'ServiceThread\.', 'ServiceThread - not available in Boomi'),
            (r'InvokeState\.', 'InvokeState - needs manual conversion'),
            (r'NSService\.', 'NSService - needs manual conversion'),
            (r'\.getPackage\(\)', 'Package access - needs reconfiguration'),
            (r'Service\.doInvoke\s*\(', 'Service invocation - use Process Call shape'),
            (r'Service\.doThreadInvoke\s*\(', 'Async invocation - use Flow Control shape'),
        ]
        
        for pattern, message in unsupported:
            if re.search(pattern, code):
                self.warnings.append(message)
        
        # Detect complex patterns needing review
        complex_patterns = [
            (r'synchronized\s*\(', 'Synchronized block - review thread safety'),
            (r'Thread\s*\.\s*sleep', 'Thread.sleep - consider Boomi timing options'),
            (r'while\s*\(', 'While loop - verify loop logic'),
            (r'for\s*\([^)]*;[^)]*;', 'For loop - verify iteration logic'),
            (r'try\s*\{', 'Try-catch - verify exception handling'),
        ]
        
        for pattern, message in complex_patterns:
            if re.search(pattern, code):
                self.manual_review_items.append(message)
    
    def _cleanup_code(self, code: str) -> str:
        """Clean up converted code"""
        # Remove empty lines (more than 2 consecutive)
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        # Remove trailing whitespace
        code = '\n'.join(line.rstrip() for line in code.split('\n'))
        
        # Remove empty comments
        code = re.sub(r'//\s*\n', '', code)
        
        return code.strip()
    
    def _calculate_confidence(self) -> int:
        """Calculate conversion confidence score"""
        confidence = 100
        
        # Reduce for warnings
        confidence -= len(self.warnings) * 15
        
        # Reduce for manual review items
        confidence -= len(self.manual_review_items) * 5
        
        # Ensure within bounds
        return max(0, min(100, confidence))
    
    def generate_url_builder_script(self, script_type: str, variables: List[str]) -> str:
        """
        Generate URL builder Groovy script for REST API calls.
        """
        if script_type == 'coordinates':
            return self._generate_coordinates_url_builder()
        elif script_type == 'zip':
            return self._generate_zip_url_builder()
        elif script_type == 'store_id':
            return self._generate_store_id_url_builder()
        else:
            return self._generate_generic_url_builder(variables)
    
    def _generate_coordinates_url_builder(self) -> str:
        return '''import com.boomi.execution.ExecutionUtil
import java.net.URLEncoder

// Get Environment Extensions (Process Properties)
def baseURL = ExecutionUtil.getDynamicProcessProperty("DPP_BaseURL")
def apiKey = ExecutionUtil.getDynamicProcessProperty("DPP_ApiKey")
def version = ExecutionUtil.getDynamicProcessProperty("DPP_Version") ?: "v1"

// Get input parameters
def lat = ExecutionUtil.getDynamicProcessProperty("lat")
def lng = ExecutionUtil.getDynamicProcessProperty("lng")
def count = ExecutionUtil.getDynamicProcessProperty("count") ?: "10"
def radius = ExecutionUtil.getDynamicProcessProperty("radius") ?: "25"
def fields = ExecutionUtil.getDynamicProcessProperty("fields") ?: ""
def filter = ExecutionUtil.getDynamicProcessProperty("filter") ?: ""

// Build the URI
def uri = "${baseURL}/geosearch?api_key=${apiKey}&v=${version}"
uri += "&location=${lat},${lng}&limit=${count}&radius=${radius}"

if (fields) {
    uri += "&fields=${fields}"
}
if (filter) {
    uri += "&filter=${URLEncoder.encode(filter, 'UTF-8')}"
}

// Set output for HTTP Connector
ExecutionUtil.setDynamicProcessProperty("DPP_RequestURI", uri, false)
ExecutionUtil.getBaseLogger().info("Built URI: ${uri}")
'''
    
    def _generate_zip_url_builder(self) -> str:
        return '''import com.boomi.execution.ExecutionUtil
import java.net.URLEncoder

// Get Environment Extensions (Process Properties)
def baseURL = ExecutionUtil.getDynamicProcessProperty("DPP_BaseURL")
def apiKey = ExecutionUtil.getDynamicProcessProperty("DPP_ApiKey")
def version = ExecutionUtil.getDynamicProcessProperty("DPP_Version") ?: "v1"

// Get input parameters - zip takes priority over city
def zip = ExecutionUtil.getDynamicProcessProperty("zip")
def city = ExecutionUtil.getDynamicProcessProperty("city")
def country = ExecutionUtil.getDynamicProcessProperty("country") ?: "US"
def count = ExecutionUtil.getDynamicProcessProperty("count") ?: "10"
def radius = ExecutionUtil.getDynamicProcessProperty("radius") ?: "25"

// Determine location parameter
def location = zip ?: city
if (!location) {
    throw new Exception("Either zip or city must be provided")
}

// Build the URI
def encodedLocation = URLEncoder.encode(location, "UTF-8")
def uri = "${baseURL}/geosearch?api_key=${apiKey}&v=${version}"
uri += "&location=${encodedLocation}&country=${country}&limit=${count}&radius=${radius}"

// Set output for HTTP Connector
ExecutionUtil.setDynamicProcessProperty("DPP_RequestURI", uri, false)
ExecutionUtil.getBaseLogger().info("Built URI: ${uri}")
'''
    
    def _generate_store_id_url_builder(self) -> str:
        return '''import com.boomi.execution.ExecutionUtil

// Get Environment Extensions (Process Properties)
def baseURL = ExecutionUtil.getDynamicProcessProperty("DPP_BaseURL")
def apiKey = ExecutionUtil.getDynamicProcessProperty("DPP_ApiKey")
def version = ExecutionUtil.getDynamicProcessProperty("DPP_Version") ?: "v1"

// Get store ID from input
def storeId = ExecutionUtil.getDynamicProcessProperty("storeId")
if (!storeId) {
    throw new Exception("storeId is required")
}

// Build the URI for single store lookup
def uri = "${baseURL}/${storeId}?api_key=${apiKey}&v=${version}"

// Set output for HTTP Connector
ExecutionUtil.setDynamicProcessProperty("DPP_RequestURI", uri, false)
ExecutionUtil.getBaseLogger().info("Built URI: ${uri}")
'''
    
    def _generate_generic_url_builder(self, variables: List[str]) -> str:
        var_declarations = '\n'.join([
            f'def {v} = ExecutionUtil.getDynamicProcessProperty("{v}")'
            for v in variables
        ])
        
        return f'''import com.boomi.execution.ExecutionUtil
import java.net.URLEncoder

// Get Environment Extensions (Process Properties)
def baseURL = ExecutionUtil.getDynamicProcessProperty("DPP_BaseURL")
def apiKey = ExecutionUtil.getDynamicProcessProperty("DPP_ApiKey")
def version = ExecutionUtil.getDynamicProcessProperty("DPP_Version") ?: "v1"

// Get input parameters
{var_declarations}

// Build the URI
def uri = "${{baseURL}}/api/${{version}}/resource?api_key=${{apiKey}}"

// Add query parameters as needed
// uri += "&param=${{value}}"

// Set output for HTTP Connector
ExecutionUtil.setDynamicProcessProperty("DPP_RequestURI", uri, false)
ExecutionUtil.getBaseLogger().info("Built URI: ${{uri}}")
'''


def convert_java_to_groovy(java_code: str, service_name: str = "") -> Dict[str, Any]:
    """Factory function to convert Java service to Groovy script."""
    generator = BoomiGroovyGenerator()
    result = generator.convert(java_code, service_name)
    return result.to_dict()


def generate_url_builder_scripts(variables: List[str]) -> Dict[str, str]:
    """Generate all URL builder scripts for REST API package."""
    generator = BoomiGroovyGenerator()
    
    return {
        'coordinates': generator.generate_url_builder_script('coordinates', variables),
        'zip': generator.generate_url_builder_script('zip', variables),
        'store_id': generator.generate_url_builder_script('store_id', variables),
        'generic': generator.generate_url_builder_script('generic', variables)
    }
