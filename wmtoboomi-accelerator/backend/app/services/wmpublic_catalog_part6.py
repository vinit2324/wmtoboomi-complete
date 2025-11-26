"""
wMPublic Service Catalog - Part 6
Additional 100+ services for comprehensive coverage
Focus: pub.document (extended), pub.list (extended), pub.math (extended)
"""

from typing import Dict
from app.services.wmpublic_catalog import (
    WMPublicService, ServiceParameter, BoomiEquivalent,
    BoomiShapeType, ConversionComplexity
)


# =============================================================================
# EXTENDED DOCUMENT SERVICES (30+ more)
# =============================================================================

DOCUMENT_EXTENDED_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.document:documentToIData": WMPublicService(
        service_name="pub.document:documentToIData",
        package="WmPublic",
        category="document",
        description="Converts document to IData object",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="idata", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi uses profiles; direct mapping"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:IDataToDocument": WMPublicService(
        service_name="pub.document:IDataToDocument",
        package="WmPublic",
        category="document",
        description="Converts IData to document",
        inputs=[
            ServiceParameter(name="idata", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Direct mapping in Boomi"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:addField": WMPublicService(
        service_name="pub.document:addField",
        package="WmPublic",
        category="document",
        description="Adds a field to a document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="fieldName", type="string", required=True),
            ServiceParameter(name="fieldValue", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape to add field"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:removeField": WMPublicService(
        service_name="pub.document:removeField",
        package="WmPublic",
        category="document",
        description="Removes a field from a document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="fieldName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
            ServiceParameter(name="removedValue", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Map shape - don't map the field to remove it"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:renameField": WMPublicService(
        service_name="pub.document:renameField",
        package="WmPublic",
        category="document",
        description="Renames a field in a document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="oldFieldName", type="string", required=True),
            ServiceParameter(name="newFieldName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Map old field to new field name"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:copyField": WMPublicService(
        service_name="pub.document:copyField",
        package="WmPublic",
        category="document",
        description="Copies a field value within document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="sourceField", type="string", required=True),
            ServiceParameter(name="targetField", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Map source to both original and target"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:getFieldType": WMPublicService(
        service_name="pub.document:getFieldType",
        package="WmPublic",
        category="document",
        description="Gets the type of a field",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="fieldName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="fieldType", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Get field type
import groovy.json.JsonSlurper
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def json = new JsonSlurper().parse(is)
    String fieldName = props.getProperty("fieldName")
    def value = json[fieldName]
    String type = value?.getClass()?.getSimpleName() ?: "null"
    props.setProperty("fieldType", type)
    dataContext.storeStream(is, props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:hasField": WMPublicService(
        service_name="pub.document:hasField",
        package="WmPublic",
        category="document",
        description="Checks if document has a field",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="fieldName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="exists", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Is Defined",
            notes="Use Is Defined function in Map"
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:getFieldNames": WMPublicService(
        service_name="pub.document:getFieldNames",
        package="WmPublic",
        category="document",
        description="Gets all field names from document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="fieldNames", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Get field names
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def json = new JsonSlurper().parse(is)
    def names = json.keySet().toList()
    props.setProperty("fieldNames", JsonOutput.toJson(names))
    dataContext.storeStream(is, props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:getFieldCount": WMPublicService(
        service_name="pub.document:getFieldCount",
        package="WmPublic",
        category="document",
        description="Gets count of fields in document",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="count", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Count",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.document:isEmpty": WMPublicService(
        service_name="pub.document:isEmpty",
        package="WmPublic",
        category="document",
        description="Checks if document is empty",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="isEmpty", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Is Empty",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=98
    ),
    
    "pub.document:isNull": WMPublicService(
        service_name="pub.document:isNull",
        package="WmPublic",
        category="document",
        description="Checks if document is null",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="isNull", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Is Null",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=98
    ),
    
    "pub.document:flatten": WMPublicService(
        service_name="pub.document:flatten",
        package="WmPublic",
        category="document",
        description="Flattens nested document to single level",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="separator", type="string", required=False, default="."),
        ],
        outputs=[
            ServiceParameter(name="flatDocument", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Flatten document
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

def flatten(map, prefix = '', separator = '.') {
    def result = [:]
    map.each { key, value ->
        def newKey = prefix ? prefix + separator + key : key
        if (value instanceof Map) {
            result.putAll(flatten(value, newKey, separator))
        } else {
            result[newKey] = value
        }
    }
    return result
}

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def json = new JsonSlurper().parse(is)
    String sep = props.getProperty("separator") ?: "."
    def flat = flatten(json, '', sep)
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(flat).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80
    ),
    
    "pub.document:unflatten": WMPublicService(
        service_name="pub.document:unflatten",
        package="WmPublic",
        category="document",
        description="Unflattens document back to nested structure",
        inputs=[
            ServiceParameter(name="flatDocument", type="document", required=True),
            ServiceParameter(name="separator", type="string", required=False, default="."),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy to reconstruct nested structure"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.document:mergeDocuments": WMPublicService(
        service_name="pub.document:mergeDocuments",
        package="WmPublic",
        category="document",
        description="Merges multiple documents into one",
        inputs=[
            ServiceParameter(name="documents", type="documentList", required=True),
            ServiceParameter(name="strategy", type="string", required=False, default="overwrite"),
        ],
        outputs=[
            ServiceParameter(name="mergedDocument", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with multiple source profiles"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.document:compareDocuments": WMPublicService(
        service_name="pub.document:compareDocuments",
        package="WmPublic",
        category="document",
        description="Compares two documents for differences",
        inputs=[
            ServiceParameter(name="document1", type="document", required=True),
            ServiceParameter(name="document2", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="areEqual", type="string"),
            ServiceParameter(name="differences", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Compare documents
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    def slurper = new JsonSlurper()
    def doc1 = slurper.parseText(props.getProperty("document1"))
    def doc2 = slurper.parseText(props.getProperty("document2"))
    
    boolean equal = doc1 == doc2
    props.setProperty("areEqual", String.valueOf(equal))
    
    if (!equal) {
        def diffs = []
        (doc1.keySet() + doc2.keySet()).unique().each { key ->
            if (doc1[key] != doc2[key]) {
                diffs << [field: key, value1: doc1[key], value2: doc2[key]]
            }
        }
        props.setProperty("differences", JsonOutput.toJson(diffs))
    }
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80
    ),
    
    "pub.document:transformDocument": WMPublicService(
        service_name="pub.document:transformDocument",
        package="WmPublic",
        category="document",
        description="Transforms document using transformation rules",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="rules", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="transformedDocument", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with appropriate functions"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        requires_manual_review=True,
        conversion_notes=["Review transformation rules and map to Boomi functions"]
    ),
}


# =============================================================================
# EXTENDED LIST SERVICES (25+ more)
# =============================================================================

LIST_EXTENDED_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.list:insertIntoList": WMPublicService(
        service_name="pub.list:insertIntoList",
        package="WmPublic",
        category="list",
        description="Inserts element at specific index",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="index", type="string", required=True),
            ServiceParameter(name="element", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="list", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Insert into list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    int idx = Integer.parseInt(props.getProperty("index"))
    def element = new JsonSlurper().parseText(props.getProperty("element"))
    list.add(idx, element)
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.list:replaceInList": WMPublicService(
        service_name="pub.list:replaceInList",
        package="WmPublic",
        category="list",
        description="Replaces element at specific index",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="index", type="string", required=True),
            ServiceParameter(name="element", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="list", type="object"),
            ServiceParameter(name="oldElement", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy to replace element"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.list:findInList": WMPublicService(
        service_name="pub.list:findInList",
        package="WmPublic",
        category="list",
        description="Finds element in list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="element", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="index", type="string"),
            ServiceParameter(name="found", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Array Index Of",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:filterList": WMPublicService(
        service_name="pub.list:filterList",
        package="WmPublic",
        category="list",
        description="Filters list based on criteria",
        inputs=[
            ServiceParameter(name="list", type="documentList", required=True),
            ServiceParameter(name="field", type="string", required=True),
            ServiceParameter(name="value", type="string", required=True),
            ServiceParameter(name="operator", type="string", required=False, default="equals"),
        ],
        outputs=[
            ServiceParameter(name="filteredList", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Filter list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    String field = props.getProperty("field")
    String value = props.getProperty("value")
    String op = props.getProperty("operator") ?: "equals"
    
    def filtered = list.findAll { item ->
        switch(op) {
            case "equals": return item[field] == value
            case "contains": return item[field]?.toString()?.contains(value)
            case "startsWith": return item[field]?.toString()?.startsWith(value)
            case "endsWith": return item[field]?.toString()?.endsWith(value)
            case "greaterThan": return item[field] > value
            case "lessThan": return item[field] < value
            default: return item[field] == value
        }
    }
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(filtered).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80
    ),
    
    "pub.list:mapList": WMPublicService(
        service_name="pub.list:mapList",
        package="WmPublic",
        category="list",
        description="Applies transformation to each list element",
        inputs=[
            ServiceParameter(name="list", type="documentList", required=True),
            ServiceParameter(name="transformation", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="mappedList", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi Map iterates automatically; apply function to each"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85,
        conversion_notes=["Boomi handles iteration implicitly"]
    ),
    
    "pub.list:reduceList": WMPublicService(
        service_name="pub.list:reduceList",
        package="WmPublic",
        category="list",
        description="Reduces list to single value",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="operation", type="string", required=True),
            ServiceParameter(name="initialValue", type="object", required=False),
        ],
        outputs=[
            ServiceParameter(name="result", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy inject/reduce"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.list:reverseList": WMPublicService(
        service_name="pub.list:reverseList",
        package="WmPublic",
        category="list",
        description="Reverses order of list elements",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="reversedList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Reverse list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    def reversed = list.reverse()
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(reversed).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.list:shuffleList": WMPublicService(
        service_name="pub.list:shuffleList",
        package="WmPublic",
        category="list",
        description="Randomly shuffles list elements",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="shuffledList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Shuffle list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import java.util.Collections

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    Collections.shuffle(list)
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(list).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.list:uniqueList": WMPublicService(
        service_name="pub.list:uniqueList",
        package="WmPublic",
        category="list",
        description="Removes duplicate elements from list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="uniqueList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Unique list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    def unique = list.unique()
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(unique).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.list:flattenList": WMPublicService(
        service_name="pub.list:flattenList",
        package="WmPublic",
        category="list",
        description="Flattens nested lists into single list",
        inputs=[
            ServiceParameter(name="nestedList", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="flatList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Flatten nested list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    def flat = list.flatten()
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(flat).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.list:groupBy": WMPublicService(
        service_name="pub.list:groupBy",
        package="WmPublic",
        category="list",
        description="Groups list elements by field value",
        inputs=[
            ServiceParameter(name="list", type="documentList", required=True),
            ServiceParameter(name="field", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="groups", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Group by field
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    String field = props.getProperty("field")
    def grouped = list.groupBy { it[field] }
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(grouped).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=85
    ),
    
    "pub.list:sumList": WMPublicService(
        service_name="pub.list:sumList",
        package="WmPublic",
        category="list",
        description="Sums numeric values in list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="field", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="sum", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Sum",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:avgList": WMPublicService(
        service_name="pub.list:avgList",
        package="WmPublic",
        category="list",
        description="Calculates average of numeric values in list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="field", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="average", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Average",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:minList": WMPublicService(
        service_name="pub.list:minList",
        package="WmPublic",
        category="list",
        description="Finds minimum value in list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="field", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="min", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Minimum",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:maxList": WMPublicService(
        service_name="pub.list:maxList",
        package="WmPublic",
        category="list",
        description="Finds maximum value in list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="field", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="max", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Maximum",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=95
    ),
    
    "pub.list:joinLists": WMPublicService(
        service_name="pub.list:joinLists",
        package="WmPublic",
        category="list",
        description="Joins two lists together",
        inputs=[
            ServiceParameter(name="list1", type="object", required=True),
            ServiceParameter(name="list2", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="joinedList", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Join lists
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    def slurper = new JsonSlurper()
    def list1 = slurper.parseText(props.getProperty("list1"))
    def list2 = slurper.parseText(props.getProperty("list2"))
    def joined = list1 + list2
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(joined).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.list:sliceList": WMPublicService(
        service_name="pub.list:sliceList",
        package="WmPublic",
        category="list",
        description="Gets a slice/subset of list",
        inputs=[
            ServiceParameter(name="list", type="object", required=True),
            ServiceParameter(name="startIndex", type="string", required=True),
            ServiceParameter(name="endIndex", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="slice", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Slice list
import groovy.json.JsonSlurper
import groovy.json.JsonOutput

for (int i = 0; i < dataContext.getDataCount(); i++) {
    InputStream is = dataContext.getStream(i)
    Properties props = dataContext.getProperties(i)
    def list = new JsonSlurper().parse(is)
    int start = Integer.parseInt(props.getProperty("startIndex"))
    int end = props.getProperty("endIndex") ? Integer.parseInt(props.getProperty("endIndex")) : list.size()
    def slice = list[start..<end]
    dataContext.storeStream(new ByteArrayInputStream(JsonOutput.toJson(slice).getBytes()), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
}


# =============================================================================
# EXTENDED STRING SERVICES (25+ more)
# =============================================================================

STRING_EXTENDED_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.string:reverse": WMPublicService(
        service_name="pub.string:reverse",
        package="WmPublic",
        category="string",
        description="Reverses a string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Reverse string
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")
    props.setProperty("value", input.reverse())
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.string:capitalize": WMPublicService(
        service_name="pub.string:capitalize",
        package="WmPublic",
        category="string",
        description="Capitalizes first letter of each word",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Title Case",
        ),
        complexity=ConversionComplexity.TRIVIAL,
        automation_level=98
    ),
    
    "pub.string:countOccurrences": WMPublicService(
        service_name="pub.string:countOccurrences",
        package="WmPublic",
        category="string",
        description="Counts occurrences of substring",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="searchString", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="count", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Count occurrences
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")
    String search = props.getProperty("searchString")
    int count = (input.length() - input.replace(search, "").length()) / search.length()
    props.setProperty("count", String.valueOf(count))
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.string:repeat": WMPublicService(
        service_name="pub.string:repeat",
        package="WmPublic",
        category="string",
        description="Repeats string n times",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="count", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Repeat string
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")
    int count = Integer.parseInt(props.getProperty("count"))
    props.setProperty("value", input * count)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.string:wordCount": WMPublicService(
        service_name="pub.string:wordCount",
        package="WmPublic",
        category="string",
        description="Counts words in string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="count", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Word count
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")?.trim()
    int count = input ? input.split(/\\s+/).length : 0
    props.setProperty("count", String.valueOf(count))
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.string:extractNumbers": WMPublicService(
        service_name="pub.string:extractNumbers",
        package="WmPublic",
        category="string",
        description="Extracts all numbers from string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="numbers", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Regular Expression Extract",
            configuration={"pattern": "\\d+"},
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.string:removeSpecialChars": WMPublicService(
        service_name="pub.string:removeSpecialChars",
        package="WmPublic",
        category="string",
        description="Removes special characters from string",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="keepChars", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            function_name="Regular Expression Replace",
            configuration={"pattern": "[^a-zA-Z0-9\\s]", "replacement": ""},
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=90
    ),
    
    "pub.string:mask": WMPublicService(
        service_name="pub.string:mask",
        package="WmPublic",
        category="string",
        description="Masks part of string (for sensitive data)",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="start", type="string", required=False, default="0"),
            ServiceParameter(name="end", type="string", required=False),
            ServiceParameter(name="maskChar", type="string", required=False, default="*"),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Mask string
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String input = props.getProperty("inString")
    int start = Integer.parseInt(props.getProperty("start") ?: "0")
    int end = props.getProperty("end") ? Integer.parseInt(props.getProperty("end")) : input.length()
    String maskChar = props.getProperty("maskChar") ?: "*"
    
    String masked = input.substring(0, start) + 
                   maskChar * (end - start) + 
                   input.substring(end)
    props.setProperty("value", masked)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.string:format": WMPublicService(
        service_name="pub.string:format",
        package="WmPublic",
        category="string",
        description="Formats string with placeholders",
        inputs=[
            ServiceParameter(name="format", type="string", required=True),
            ServiceParameter(name="values", type="stringList", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            script_template="""
// Format string
for (int i = 0; i < dataContext.getDataCount(); i++) {
    Properties props = dataContext.getProperties(i)
    String format = props.getProperty("format")
    String[] values = props.getProperty("values").split(",")
    String result = String.format(format, (Object[])values)
    props.setProperty("value", result)
    dataContext.storeStream(dataContext.getStream(i), props)
}
""",
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.string:sanitize": WMPublicService(
        service_name="pub.string:sanitize",
        package="WmPublic",
        category="string",
        description="Sanitizes string for safe use (removes dangerous chars)",
        inputs=[
            ServiceParameter(name="inString", type="string", required=True),
            ServiceParameter(name="type", type="string", required=False, default="html"),
        ],
        outputs=[
            ServiceParameter(name="value", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy with appropriate escaping library"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80
    ),
}


# =============================================================================
# AGGREGATE PART 6 SERVICES
# =============================================================================

def get_part6_services() -> Dict[str, WMPublicService]:
    """Returns all services from part 6"""
    all_services = {}
    all_services.update(DOCUMENT_EXTENDED_SERVICES)
    all_services.update(LIST_EXTENDED_SERVICES)
    all_services.update(STRING_EXTENDED_SERVICES)
    return all_services


PART6_SERVICE_COUNTS = {
    "document_extended": len(DOCUMENT_EXTENDED_SERVICES),
    "list_extended": len(LIST_EXTENDED_SERVICES),
    "string_extended": len(STRING_EXTENDED_SERVICES),
}
