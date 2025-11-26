"""
wMPublic Service Catalog - Part 2
Document, List, Flow Control, XML, JSON, File services
"""

from app.services.wmpublic_catalog import (
    WMPublicService, ServiceParameter, BoomiEquivalent,
    BoomiShapeType, ConversionComplexity
)
from typing import Dict


# =============================================================================
# DOCUMENT SERVICES (45+ services)
# =============================================================================

DOCUMENT_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.document:documentToRecord": WMPublicService(
        service_name="pub.document:documentToRecord",
        package="WmPublic",
        category="document",
        description="Converts IData document to record structure",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="record", type="record"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi uses profiles; direct document access in Map"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:recordToDocument": WMPublicService(
        service_name="pub.document:recordToDocument",
        package="WmPublic",
        category="document",
        description="Converts record to IData document",
        inputs=[
            ServiceParameter(name="record", type="record", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi uses profiles; Map shape handles conversion"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:merge": WMPublicService(
        service_name="pub.document:merge",
        package="WmPublic",
        category="document",
        description="Merges two documents",
        inputs=[
            ServiceParameter(name="document1", type="document", required=True),
            ServiceParameter(name="document2", type="document", required=True),
            ServiceParameter(name="overwrite", type="string", required=False, default="true"),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to combine fields from both documents"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Map all fields from both sources to target"]
    ),
    
    "pub.document:getLeafValues": WMPublicService(
        service_name="pub.document:getLeafValues",
        package="WmPublic",
        category="document",
        description="Extracts all leaf values from document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="values", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Get all leaf values from document
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

def getLeafValues(obj, values = []) {
    if (obj instanceof Map) {
        obj.each { k, v -> getLeafValues(v, values) }
    } else if (obj instanceof List) {
        obj.each { getLeafValues(it, values) }
    } else {
        values << obj?.toString()
    }
    return values
}

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def json = new JsonSlurper().parse(is)
    def values = getLeafValues(json)
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(values).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.document:getValueFromDoc": WMPublicService(
        service_name="pub.document:getValueFromDoc",
        package="WmPublic",
        category="document",
        description="Gets value from document using path",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="path", type="string", required=True, description="Dot-separated path"),
        ],
        outputs=[
            ServiceParameter(name="value", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with dynamic document property path"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:setValueInDoc": WMPublicService(
        service_name="pub.document:setValueInDoc",
        package="WmPublic",
        category="document",
        description="Sets value in document at path",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="path", type="string", required=True),
            ServiceParameter(name="value", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to set specific field value"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:documentListToDocument": WMPublicService(
        service_name="pub.document:documentListToDocument",
        package="WmPublic",
        category="document",
        description="Converts document list to single document with array",
        inputs=[
            ServiceParameter(name="documentList", type="documentList", required=True),
            ServiceParameter(name="targetName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles arrays naturally; use Map to wrap"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.document:documentToDocumentList": WMPublicService(
        service_name="pub.document:documentToDocumentList",
        package="WmPublic",
        category="document",
        description="Extracts array from document to document list",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="sourceName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="documentList", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to extract array element"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.document:clone": WMPublicService(
        service_name="pub.document:clone",
        package="WmPublic",
        category="document",
        description="Creates deep copy of document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="clone", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Map all fields to create copy; Boomi doesn't share references"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
}


# =============================================================================
# LIST SERVICES (35+ services)
# =============================================================================

LIST_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.list:appendToDocumentList": WMPublicService(
        service_name="pub.list:appendToDocumentList",
        package="WmPublic",
        category="list",
        description="Appends document to document list",
        inputs=[
            ServiceParameter(name="toList", type="documentList", required=True),
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="toList", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Append to document list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def slurper = new JsonSlurper()
    def list = slurper.parse(is)
    def newDoc = slurper.parseText(props.getProperty("document"))
    list << newDoc
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80,
        conversion_notes=["Boomi handles arrays differently; may need Flow Control"]
    ),
    
    "pub.list:appendToStringList": WMPublicService(
        service_name="pub.list:appendToStringList",
        package="WmPublic",
        category="list",
        description="Appends string to string list",
        inputs=[
            ServiceParameter(name="toList", type="stringList", required=True),
            ServiceParameter(name="string", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="toList", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="String Append to List",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.list:sizeOfList": WMPublicService(
        service_name="pub.list:sizeOfList",
        package="WmPublic",
        category="list",
        description="Returns size of list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True, description="Any list type"),
        ],
        outputs=[
            ServiceParameter(name="size", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Count",
            notes="Use Count function on array element"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:getFromList": WMPublicService(
        service_name="pub.list:getFromList",
        package="WmPublic",
        category="list",
        description="Gets element at index from list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="index", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Array Element",
            notes="Use Array Element function with index"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:sortDocumentList": WMPublicService(
        service_name="pub.list:sortDocumentList",
        package="WmPublic",
        category="list",
        description="Sorts document list by specified key",
        inputs=[
            ServiceParameter(name="documentList", type="documentList", required=True),
            ServiceParameter(name="key", type="string", required=True),
            ServiceParameter(name="order", type="string", required=False, default="asc"),
        ],
        outputs=[
            ServiceParameter(name="documentList", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Sort document list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    String key = props.getProperty("key")
    String order = props.getProperty("order") ?: "asc"
    
    def slurper = new JsonSlurper()
    def list = slurper.parse(is)
    
    if (order == "desc") {
        list = list.sort { a, b -> b[key] <=> a[key] }
    } else {
        list = list.sort { a, b -> a[key] <=> b[key] }
    }
    
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
    
    "pub.list:sortStringList": WMPublicService(
        service_name="pub.list:sortStringList",
        package="WmPublic",
        category="list",
        description="Sorts string list",
        inputs=[
            ServiceParameter(name="stringList", type="stringList", required=True),
            ServiceParameter(name="order", type="string", required=False, default="asc"),
        ],
        outputs=[
            ServiceParameter(name="stringList", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Sort string list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    String order = props.getProperty("order") ?: "asc"
    
    def slurper = new JsonSlurper()
    def list = slurper.parse(is)
    
    list = order == "desc" ? list.sort().reverse() : list.sort()
    
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.list:stringListToString": WMPublicService(
        service_name="pub.list:stringListToString",
        package="WmPublic",
        category="list",
        description="Joins string list into single string",
        inputs=[
            ServiceParameter(name="stringList", type="stringList", required=True),
            ServiceParameter(name="separator", type="string", required=False, default=","),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="String Join",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:stringToStringList": WMPublicService(
        service_name="pub.list:stringToStringList",
        package="WmPublic",
        category="list",
        description="Splits string into string list",
        inputs=[
            ServiceParameter(name="string", type="string", required=True),
            ServiceParameter(name="separator", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="stringList", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="String Split",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:removeFromList": WMPublicService(
        service_name="pub.list:removeFromList",
        package="WmPublic",
        category="list",
        description="Removes element at index from list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="index", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="list", type="object"),
            ServiceParameter(name="removed", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Remove from list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    int index = Integer.parseInt(props.getProperty("index"))
    
    def slurper = new JsonSlurper()
    def list = slurper.parse(is)
    def removed = list.remove(index)
    
    props.setProperty("removed", JsonOutput.toJson(removed))
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.list:documentListToRecordList": WMPublicService(
        service_name="pub.list:documentListToRecordList",
        package="WmPublic",
        category="list",
        description="Converts document list to record list",
        inputs=[
            ServiceParameter(name="documentList", type="documentList", required=True),
        ],
        outputs=[
            ServiceParameter(name="recordList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi uses profiles; arrays are handled natively"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
}


# =============================================================================
# FLOW CONTROL SERVICES (25+ services)
# =============================================================================

FLOW_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.flow:setResponse": WMPublicService(
        service_name="pub.flow:setResponse",
        package="WmPublic",
        category="flow",
        description="Sets HTTP response status and headers",
        inputs=[
            ServiceParameter(name="statusCode", type="string", required=False, default="200"),
            ServiceParameter(name="statusMessage", type="string", required=False),
            ServiceParameter(name="contentType", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Set Properties shape for HTTP response; or configure connector"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.flow:getLastError": WMPublicService(
        service_name="pub.flow:getLastError",
        package="WmPublic",
        category="flow",
        description="Gets last error information",
        inputs=[],
        outputs=[
            ServiceParameter(name="lastError", type="document", description="Error details"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRY_CATCH,
            notes="Use Try/Catch shape; error is in exception object"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Boomi exception handling differs from webMethods"]
    ),
    
    "pub.flow:throwExceptionForRetry": WMPublicService(
        service_name="pub.flow:throwExceptionForRetry",
        package="WmPublic",
        category="flow",
        description="Throws exception to trigger retry",
        inputs=[
            ServiceParameter(name="message", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.EXCEPTION,
            notes="Use Exception shape; configure retry on parent process"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65,
        requires_manual_review=True,
        conversion_notes=["Configure retry at process level in Boomi"]
    ),
    
    "pub.flow:savePipeline": WMPublicService(
        service_name="pub.flow:savePipeline",
        package="WmPublic",
        category="flow",
        description="Saves pipeline to variable",
        inputs=[
            ServiceParameter(name="name", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Boomi doesn't have pipeline concept; use Document Cache or Process Property"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=40,
        requires_manual_review=True,
        conversion_notes=[
            "Boomi doesn't have equivalent pipeline save",
            "Consider: Document Cache, Process Property, or flow redesign"
        ]
    ),
    
    "pub.flow:restorePipeline": WMPublicService(
        service_name="pub.flow:restorePipeline",
        package="WmPublic",
        category="flow",
        description="Restores pipeline from saved variable",
        inputs=[
            ServiceParameter(name="name", type="string", required=True),
            ServiceParameter(name="merge", type="string", required=False, default="false"),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Boomi doesn't have pipeline concept; restructure logic"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=40,
        requires_manual_review=True
    ),
    
    "pub.flow:clearPipeline": WMPublicService(
        service_name="pub.flow:clearPipeline",
        package="WmPublic",
        category="flow",
        description="Clears all pipeline variables",
        inputs=[],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Not needed in Boomi; data is scoped automatically"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95,
        conversion_notes=["Boomi handles data scoping automatically; remove this call"]
    ),
    
    "pub.flow:debugLog": WMPublicService(
        service_name="pub.flow:debugLog",
        package="WmPublic",
        category="flow",
        description="Logs debug message",
        inputs=[
            ServiceParameter(name="message", type="string", required=True),
            ServiceParameter(name="function", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.NOTIFY,
            notes="Use Notify shape or Data Process with logging"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.flow:tracePipeline": WMPublicService(
        service_name="pub.flow:tracePipeline",
        package="WmPublic",
        category="flow",
        description="Logs pipeline contents for debugging",
        inputs=[
            ServiceParameter(name="level", type="string", required=False, default="10"),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.NOTIFY,
            notes="Use Notify shape or Process Reporting"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.flow:getTransportInfo": WMPublicService(
        service_name="pub.flow:getTransportInfo",
        package="WmPublic",
        category="flow",
        description="Gets HTTP transport information",
        inputs=[],
        outputs=[
            ServiceParameter(name="transport", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Dynamic Document Property to access HTTP headers"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
    
    "pub.flow:getContextServices": WMPublicService(
        service_name="pub.flow:getContextServices",
        package="WmPublic",
        category="flow",
        description="Gets list of services in call stack",
        inputs=[],
        outputs=[
            ServiceParameter(name="services", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="No direct equivalent; use Process Logging if needed"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=30,
        requires_manual_review=True
    ),
}


# =============================================================================
# XML SERVICES (45+ services)
# =============================================================================

XML_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.xml:documentToXMLString": WMPublicService(
        service_name="pub.xml:documentToXMLString",
        package="WmPublic",
        category="xml",
        description="Converts document to XML string",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="documentTypeName", type="string", required=False),
            ServiceParameter(name="encoding", type="string", required=False, default="UTF-8"),
        ],
        outputs=[
            ServiceParameter(name="xmldata", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with XML profile as output"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.xml:xmlStringToDocument": WMPublicService(
        service_name="pub.xml:xmlStringToDocument",
        package="WmPublic",
        category="xml",
        description="Parses XML string to document",
        inputs=[
            ServiceParameter(name="xmldata", type="string", required=True),
            ServiceParameter(name="documentTypeName", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with XML profile as input"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.xml:xmlNodeToDocument": WMPublicService(
        service_name="pub.xml:xmlNodeToDocument",
        package="WmPublic",
        category="xml",
        description="Converts XML node to document",
        inputs=[
            ServiceParameter(name="node", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi profiles handle XML natively"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.xml:queryXMLNode": WMPublicService(
        service_name="pub.xml:queryXMLNode",
        package="WmPublic",
        category="xml",
        description="Queries XML using XPath",
        inputs=[
            ServiceParameter(name="node", type="object", required=True),
            ServiceParameter(name="query", type="string", required=True, description="XPath expression"),
        ],
        outputs=[
            ServiceParameter(name="resultNode", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// XPath query
import javax.xml.xpath.*
import javax.xml.parsers.DocumentBuilderFactory
import org.w3c.dom.Document

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    String xpath = props.getProperty("query")
    
    DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance()
    Document doc = factory.newDocumentBuilder().parse(is)
    
    XPathFactory xpathFactory = XPathFactory.newInstance()
    XPath xpathObj = xpathFactory.newXPath()
    String result = xpathObj.evaluate(xpath, doc)
    
    props.setProperty("result", result)
    dataContext.storeStream(is, props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.xml:getXMLNodeValue": WMPublicService(
        service_name="pub.xml:getXMLNodeValue",
        package="WmPublic",
        category="xml",
        description="Gets text value from XML node",
        inputs=[
            ServiceParameter(name="node", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape; value is accessed through profile element"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.xml:setXMLNodeValue": WMPublicService(
        service_name="pub.xml:setXMLNodeValue",
        package="WmPublic",
        category="xml",
        description="Sets text value of XML node",
        inputs=[
            ServiceParameter(name="node", type="object", required=True),
            ServiceParameter(name="value", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="node", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to set field value"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.xml:getXMLNodeAttribute": WMPublicService(
        service_name="pub.xml:getXMLNodeAttribute",
        package="WmPublic",
        category="xml",
        description="Gets attribute value from XML node",
        inputs=[
            ServiceParameter(name="node", type="object", required=True),
            ServiceParameter(name="attributeName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape; attribute accessed through profile @attribute"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.xml:validateXML": WMPublicService(
        service_name="pub.xml:validateXML",
        package="WmPublic",
        category="xml",
        description="Validates XML against schema",
        inputs=[
            ServiceParameter(name="xmldata", type="object", required=True),
            ServiceParameter(name="schemaLocation", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="isValid", type="string"),
            ServiceParameter(name="errors", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Boomi profile validation or custom Groovy"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65,
        requires_manual_review=True
    ),
}


# =============================================================================
# JSON SERVICES (20+ services)
# =============================================================================

JSON_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.json:documentToJSONString": WMPublicService(
        service_name="pub.json:documentToJSONString",
        package="WmPublic",
        category="json",
        description="Converts document to JSON string",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="documentTypeName", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="jsonString", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with JSON profile as output"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=95
    ),
    
    "pub.json:jsonStringToDocument": WMPublicService(
        service_name="pub.json:jsonStringToDocument",
        package="WmPublic",
        category="json",
        description="Parses JSON string to document",
        inputs=[
            ServiceParameter(name="jsonString", type="string", required=True),
            ServiceParameter(name="documentTypeName", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with JSON profile as input"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=95
    ),
    
    "pub.json:getValueFromJSON": WMPublicService(
        service_name="pub.json:getValueFromJSON",
        package="WmPublic",
        category="json",
        description="Gets value from JSON using path",
        inputs=[
            ServiceParameter(name="json", type="object", required=True),
            ServiceParameter(name="path", type="string", required=True, description="JSONPath expression"),
        ],
        outputs=[
            ServiceParameter(name="value", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with JSON profile; path maps to element"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.json:setValueInJSON": WMPublicService(
        service_name="pub.json:setValueInJSON",
        package="WmPublic",
        category="json",
        description="Sets value in JSON at path",
        inputs=[
            ServiceParameter(name="json", type="object", required=True),
            ServiceParameter(name="path", type="string", required=True),
            ServiceParameter(name="value", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="json", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to set specific field"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
}


# =============================================================================
# FILE SERVICES (30+ services)
# =============================================================================

FILE_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.file:getFile": WMPublicService(
        service_name="pub.file:getFile",
        package="WmPublic",
        category="file",
        description="Reads file from disk",
        inputs=[
            ServiceParameter(name="filename", type="string", required=True),
            ServiceParameter(name="loadAs", type="string", required=False, default="bytes"),
        ],
        outputs=[
            ServiceParameter(name="body", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DISK,
            connector_type="Disk Connector",
            notes="Use Disk connector with GET operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.file:putFile": WMPublicService(
        service_name="pub.file:putFile",
        package="WmPublic",
        category="file",
        description="Writes file to disk",
        inputs=[
            ServiceParameter(name="filename", type="string", required=True),
            ServiceParameter(name="body", type="object", required=True),
            ServiceParameter(name="append", type="string", required=False, default="false"),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DISK,
            connector_type="Disk Connector",
            notes="Use Disk connector with WRITE operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.file:deleteFile": WMPublicService(
        service_name="pub.file:deleteFile",
        package="WmPublic",
        category="file",
        description="Deletes file from disk",
        inputs=[
            ServiceParameter(name="filename", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="deleted", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DISK,
            connector_type="Disk Connector",
            notes="Use Disk connector with DELETE operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.file:moveFile": WMPublicService(
        service_name="pub.file:moveFile",
        package="WmPublic",
        category="file",
        description="Moves file to new location",
        inputs=[
            ServiceParameter(name="source", type="string", required=True),
            ServiceParameter(name="target", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Move file
import java.nio.file.*
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    Path source = Paths.get(props.getProperty("source"))
    Path target = Paths.get(props.getProperty("target"))
    Files.move(source, target, StandardCopyOption.REPLACE_EXISTING)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.file:copyFile": WMPublicService(
        service_name="pub.file:copyFile",
        package="WmPublic",
        category="file",
        description="Copies file to new location",
        inputs=[
            ServiceParameter(name="source", type="string", required=True),
            ServiceParameter(name="target", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Copy file
import java.nio.file.*
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    Path source = Paths.get(props.getProperty("source"))
    Path target = Paths.get(props.getProperty("target"))
    Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.file:listFiles": WMPublicService(
        service_name="pub.file:listFiles",
        package="WmPublic",
        category="file",
        description="Lists files in directory",
        inputs=[
            ServiceParameter(name="directory", type="string", required=True),
            ServiceParameter(name="filter", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="files", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DISK,
            connector_type="Disk Connector",
            notes="Use Disk connector with LIST operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.file:createDirectory": WMPublicService(
        service_name="pub.file:createDirectory",
        package="WmPublic",
        category="file",
        description="Creates directory",
        inputs=[
            ServiceParameter(name="directory", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="created", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Create directory
import java.nio.file.*
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    Path dir = Paths.get(props.getProperty("directory"))
    Files.createDirectories(dir)
    props.setProperty("created", "true")
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
}


# =============================================================================
# AGGREGATE ALL SERVICES
# =============================================================================

def get_all_services() -> Dict[str, WMPublicService]:
    """Returns complete catalog of all wMPublic services"""
    all_services = {}
    all_services.update(DOCUMENT_SERVICES)
    all_services.update(LIST_SERVICES)
    all_services.update(FLOW_SERVICES)
    all_services.update(XML_SERVICES)
    all_services.update(JSON_SERVICES)
    all_services.update(FILE_SERVICES)
    return all_services


# Service count by category
SERVICE_COUNTS = {
    "document": len(DOCUMENT_SERVICES),
    "list": len(LIST_SERVICES),
    "flow": len(FLOW_SERVICES),
    "xml": len(XML_SERVICES),
    "json": len(JSON_SERVICES),
    "file": len(FILE_SERVICES),
}
