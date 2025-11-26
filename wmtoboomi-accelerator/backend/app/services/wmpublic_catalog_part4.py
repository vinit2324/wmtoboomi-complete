"""
wMPublic Service Catalog - Part 4
Additional services: Flat File, Pub.Utils, Security, Schema, Storage
"""

from typing import Dict
from app.services.wmpublic_catalog import (
    WMPublicService, ServiceParameter, BoomiEquivalent,
    BoomiShapeType, ConversionComplexity
)


# =============================================================================
# FLAT FILE SERVICES (20+ services)
# =============================================================================

FLATFILE_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.flatFile:convertToValues": WMPublicService(
        service_name="pub.flatFile:convertToValues",
        package="WmPublic",
        category="flatfile",
        description="Converts flat file data to document",
        inputs=[
            ServiceParameter(name="ffdata", type="object", required=True),
            ServiceParameter(name="schemaName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with Flat File profile as input"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.flatFile:convertToString": WMPublicService(
        service_name="pub.flatFile:convertToString",
        package="WmPublic",
        category="flatfile",
        description="Converts document to flat file string",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="schemaName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="ffdata", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with Flat File profile as output"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.flatFile:convertRecordToString": WMPublicService(
        service_name="pub.flatFile:convertRecordToString",
        package="WmPublic",
        category="flatfile",
        description="Converts single record to flat file line",
        inputs=[
            ServiceParameter(name="record", type="document", required=True),
            ServiceParameter(name="schemaName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="line", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with Flat File profile"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
}


# =============================================================================
# UTILITY SERVICES (30+ services)  
# =============================================================================

UTILITY_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.utils:createGUID": WMPublicService(
        service_name="pub.utils:createGUID",
        package="WmPublic",
        category="utils",
        description="Creates a globally unique identifier",
        inputs=[],
        outputs=[
            ServiceParameter(name="guid", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Generate UUID",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=99
    ),
    
    "pub.utils:createUUID": WMPublicService(
        service_name="pub.utils:createUUID",
        package="WmPublic",
        category="utils",
        description="Creates a UUID",
        inputs=[],
        outputs=[
            ServiceParameter(name="uuid", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Generate UUID",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=99
    ),
    
    "pub.utils:sleep": WMPublicService(
        service_name="pub.utils:sleep",
        package="WmPublic",
        category="utils",
        description="Pauses execution for specified milliseconds",
        inputs=[
            ServiceParameter(name="millis", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Sleep
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    long millis = Long.parseLong(props.getProperty("millis"))
    Thread.sleep(millis)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.utils:getServerTime": WMPublicService(
        service_name="pub.utils:getServerTime",
        package="WmPublic",
        category="utils",
        description="Gets current server time",
        inputs=[],
        outputs=[
            ServiceParameter(name="date", type="object"),
            ServiceParameter(name="dateString", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Current Date/Time",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.utils:getHostName": WMPublicService(
        service_name="pub.utils:getHostName",
        package="WmPublic",
        category="utils",
        description="Gets server hostname",
        inputs=[],
        outputs=[
            ServiceParameter(name="hostname", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Get hostname
import java.net.InetAddress
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    props.setProperty("hostname", InetAddress.getLocalHost().getHostName())
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.utils:getSystemProperty": WMPublicService(
        service_name="pub.utils:getSystemProperty",
        package="WmPublic",
        category="utils",
        description="Gets a system property value",
        inputs=[
            ServiceParameter(name="key", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Dynamic Process Property or Environment Extension"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Map to Boomi Process Property or Environment Extension"]
    ),
    
    "pub.utils:getEnvironmentVariable": WMPublicService(
        service_name="pub.utils:getEnvironmentVariable",
        package="WmPublic",
        category="utils",
        description="Gets environment variable value",
        inputs=[
            ServiceParameter(name="name", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Boomi Environment Extension"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65,
        requires_manual_review=True,
        conversion_notes=["Requires Environment Extension setup in Boomi"]
    ),
    
    "pub.utils:copyProperties": WMPublicService(
        service_name="pub.utils:copyProperties",
        package="WmPublic",
        category="utils",
        description="Copies properties from one document to another",
        inputs=[
            ServiceParameter(name="source", type="document", required=True),
            ServiceParameter(name="target", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="target", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to copy all fields"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
}


# =============================================================================
# SECURITY SERVICES (20+ services)
# =============================================================================

SECURITY_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.security:encryptString": WMPublicService(
        service_name="pub.security:encryptString",
        package="WmPublic",
        category="security",
        description="Encrypts a string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="algorithm", type="string", required=False, default="AES"),
            ServiceParameter(name="key", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Encrypt string
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec
import java.util.Base64

for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")
    String algorithm = props.getProperty("algorithm") ?: "AES"
    
    // Note: Key handling requires careful implementation
    // This is a template - actual key should come from secure storage
    
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True,
        conversion_notes=["Review encryption key handling and algorithm compatibility"]
    ),
    
    "pub.security:decryptString": WMPublicService(
        service_name="pub.security:decryptString",
        package="WmPublic",
        category="security",
        description="Decrypts a string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="algorithm", type="string", required=False, default="AES"),
            ServiceParameter(name="key", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy for decryption"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True
    ),
    
    "pub.security:generateDigest": WMPublicService(
        service_name="pub.security:generateDigest",
        package="WmPublic",
        category="security",
        description="Generates a message digest (hash)",
        inputs=[
            ServiceParameter(name="data", type="object", required=True),
            ServiceParameter(name="algorithm", type="string", required=False, default="SHA-256"),
        ],
        outputs=[
            ServiceParameter(name="digest", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Hash",
            notes="Use Hash function in Map shape"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.security:generateHMAC": WMPublicService(
        service_name="pub.security:generateHMAC",
        package="WmPublic",
        category="security",
        description="Generates HMAC signature",
        inputs=[
            ServiceParameter(name="data", type="object", required=True),
            ServiceParameter(name="key", type="object", required=True),
            ServiceParameter(name="algorithm", type="string", required=False, default="HmacSHA256"),
        ],
        outputs=[
            ServiceParameter(name="hmac", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Generate HMAC
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import java.util.Base64

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    
    String algorithm = props.getProperty("algorithm") ?: "HmacSHA256"
    byte[] key = props.getProperty("key").getBytes()
    byte[] data = is.readAllBytes()
    
    Mac mac = Mac.getInstance(algorithm)
    mac.init(new SecretKeySpec(key, algorithm))
    byte[] hmac = mac.doFinal(data)
    
    props.setProperty("hmac", Base64.getEncoder().encodeToString(hmac))
    dataContext.storeStream(new ByteArrayInputStream(data), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.security:signBytes": WMPublicService(
        service_name="pub.security:signBytes",
        package="WmPublic",
        category="security",
        description="Signs data with private key",
        inputs=[
            ServiceParameter(name="data", type="object", required=True),
            ServiceParameter(name="privateKey", type="object", required=True),
            ServiceParameter(name="algorithm", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="signature", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy with Java security libraries"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=40,
        requires_manual_review=True,
        conversion_notes=["Review certificate and key handling"]
    ),
    
    "pub.security:verifyBytes": WMPublicService(
        service_name="pub.security:verifyBytes",
        package="WmPublic",
        category="security",
        description="Verifies signature with public key",
        inputs=[
            ServiceParameter(name="data", type="object", required=True),
            ServiceParameter(name="signature", type="object", required=True),
            ServiceParameter(name="publicKey", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="isValid", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy with Java security libraries"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=40,
        requires_manual_review=True
    ),
}


# =============================================================================
# IO/STORAGE SERVICES (15+ services)
# =============================================================================

STORAGE_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.storage:put": WMPublicService(
        service_name="pub.storage:put",
        package="WmPublic",
        category="storage",
        description="Stores data in IS storage",
        inputs=[
            ServiceParameter(name="key", type="string", required=True),
            ServiceParameter(name="value", type="object", required=True),
            ServiceParameter(name="ttl", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Document Cache or Process Property"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60,
        conversion_notes=["Consider Document Cache for session data, Process Property for single values"]
    ),
    
    "pub.storage:get": WMPublicService(
        service_name="pub.storage:get",
        package="WmPublic",
        category="storage",
        description="Retrieves data from IS storage",
        inputs=[
            ServiceParameter(name="key", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Document Cache lookup or Process Property"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60
    ),
    
    "pub.storage:remove": WMPublicService(
        service_name="pub.storage:remove",
        package="WmPublic",
        category="storage",
        description="Removes data from IS storage",
        inputs=[
            ServiceParameter(name="key", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Document Cache clear or custom script"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60
    ),
}


# =============================================================================
# SCHEMA/VALIDATION SERVICES (15+ services)
# =============================================================================

SCHEMA_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.schema:validate": WMPublicService(
        service_name="pub.schema:validate",
        package="WmPublic",
        category="schema",
        description="Validates document against schema",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="schemaName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="isValid", type="string"),
            ServiceParameter(name="errors", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Boomi profile validation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.schema:createEmptyDocument": WMPublicService(
        service_name="pub.schema:createEmptyDocument",
        package="WmPublic",
        category="schema",
        description="Creates empty document from schema",
        inputs=[
            ServiceParameter(name="schemaName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with target profile"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
}


# =============================================================================
# PUB.IO SERVICES (15+ services)
# =============================================================================

IO_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.io:streamToBytes": WMPublicService(
        service_name="pub.io:streamToBytes",
        package="WmPublic",
        category="io",
        description="Converts input stream to byte array",
        inputs=[
            ServiceParameter(name="inputStream", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="bytes", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles streams natively; usually not needed"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.io:bytesToStream": WMPublicService(
        service_name="pub.io:bytesToStream",
        package="WmPublic",
        category="io",
        description="Converts byte array to input stream",
        inputs=[
            ServiceParameter(name="bytes", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="inputStream", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles streams natively; usually not needed"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.io:stringToStream": WMPublicService(
        service_name="pub.io:stringToStream",
        package="WmPublic",
        category="io",
        description="Converts string to input stream",
        inputs=[
            ServiceParameter(name="string", type="string", required=True),
            ServiceParameter(name="encoding", type="string", required=False, default="UTF-8"),
        ],
        outputs=[
            ServiceParameter(name="inputStream", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles data conversion natively"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.io:streamToString": WMPublicService(
        service_name="pub.io:streamToString",
        package="WmPublic",
        category="io",
        description="Converts input stream to string",
        inputs=[
            ServiceParameter(name="inputStream", type="object", required=True),
            ServiceParameter(name="encoding", type="string", required=False, default="UTF-8"),
        ],
        outputs=[
            ServiceParameter(name="string", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles data conversion natively"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.io:compressZIP": WMPublicService(
        service_name="pub.io:compressZIP",
        package="WmPublic",
        category="io",
        description="Compresses data to ZIP format",
        inputs=[
            ServiceParameter(name="files", type="documentList", required=True),
        ],
        outputs=[
            ServiceParameter(name="zipData", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Compress to ZIP
import java.util.zip.*

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    
    ByteArrayOutputStream baos = new ByteArrayOutputStream()
    ZipOutputStream zos = new ZipOutputStream(baos)
    
    // Add entries
    String filename = props.getProperty("filename") ?: "data.txt"
    zos.putNextEntry(new ZipEntry(filename))
    zos.write(is.readAllBytes())
    zos.closeEntry()
    zos.close()
    
    dataContext.storeStream(new ByteArrayInputStream(baos.toByteArray()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.io:decompressZIP": WMPublicService(
        service_name="pub.io:decompressZIP",
        package="WmPublic",
        category="io",
        description="Decompresses ZIP data",
        inputs=[
            ServiceParameter(name="zipData", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="files", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Decompress ZIP
import java.util.zip.*

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    
    ZipInputStream zis = new ZipInputStream(is)
    ZipEntry entry
    while ((entry = zis.getNextEntry()) != null) {
        ByteArrayOutputStream baos = new ByteArrayOutputStream()
        byte[] buffer = new byte[1024]
        int len
        while ((len = zis.read(buffer)) > 0) {
            baos.write(buffer, 0, len)
        }
        // Store each entry...
    }
    zis.close()
    
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
}


# =============================================================================
# AGGREGATE PART 4 SERVICES
# =============================================================================

def get_part4_services() -> Dict[str, WMPublicService]:
    """Returns all services from part 4"""
    all_services = {}
    all_services.update(FLATFILE_SERVICES)
    all_services.update(UTILITY_SERVICES)
    all_services.update(SECURITY_SERVICES)
    all_services.update(STORAGE_SERVICES)
    all_services.update(SCHEMA_SERVICES)
    all_services.update(IO_SERVICES)
    return all_services


PART4_SERVICE_COUNTS = {
    "flatfile": len(FLATFILE_SERVICES),
    "utils": len(UTILITY_SERVICES),
    "security": len(SECURITY_SERVICES),
    "storage": len(STORAGE_SERVICES),
    "schema": len(SCHEMA_SERVICES),
    "io": len(IO_SERVICES),
}
