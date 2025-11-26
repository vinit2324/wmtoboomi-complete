"""
wMPublic Service Catalog - Part 3
Database, HTTP Client, FTP, EDI services
"""

from app.services.wmpublic_catalog import (
    WMPublicService, ServiceParameter, BoomiEquivalent,
    BoomiShapeType, ConversionComplexity
)
from typing import Dict


# =============================================================================
# DATABASE SERVICES (25+ services)
# =============================================================================

DATABASE_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.db:query": WMPublicService(
        service_name="pub.db:query",
        package="WmPublic",
        category="database",
        description="Executes SELECT query",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True, description="Database alias"),
            ServiceParameter(name="$query", type="string", required=True, description="SQL SELECT statement"),
            ServiceParameter(name="$maxRows", type="string", required=False),
            ServiceParameter(name="$timeout", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="results", type="documentList"),
            ServiceParameter(name="rowCount", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Query"},
            notes="Use Database connector with Query operation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        conversion_notes=[
            "Create Database Connection in Boomi",
            "Map SQL query to Database operation",
            "Complex queries with JOINs may need review"
        ]
    ),
    
    "pub.db:insert": WMPublicService(
        service_name="pub.db:insert",
        package="WmPublic",
        category="database",
        description="Inserts row into table",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
            ServiceParameter(name="$table", type="string", required=True),
            ServiceParameter(name="$data", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="rowsAffected", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Create"},
            notes="Use Database connector with Create operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.db:update": WMPublicService(
        service_name="pub.db:update",
        package="WmPublic",
        category="database",
        description="Updates rows in table",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
            ServiceParameter(name="$table", type="string", required=True),
            ServiceParameter(name="$data", type="document", required=True),
            ServiceParameter(name="$where", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="rowsAffected", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Update"},
            notes="Use Database connector with Update operation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.db:delete": WMPublicService(
        service_name="pub.db:delete",
        package="WmPublic",
        category="database",
        description="Deletes rows from table",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
            ServiceParameter(name="$table", type="string", required=True),
            ServiceParameter(name="$where", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="rowsAffected", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Delete"},
            notes="Use Database connector with Delete operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.db:call": WMPublicService(
        service_name="pub.db:call",
        package="WmPublic",
        category="database",
        description="Calls stored procedure",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
            ServiceParameter(name="$procedure", type="string", required=True),
            ServiceParameter(name="$inputParams", type="documentList", required=False),
        ],
        outputs=[
            ServiceParameter(name="$outputParams", type="documentList"),
            ServiceParameter(name="results", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Stored Procedure"},
            notes="Use Database connector with Stored Procedure operation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Map stored procedure parameters correctly"]
    ),
    
    "pub.db:execSQL": WMPublicService(
        service_name="pub.db:execSQL",
        package="WmPublic",
        category="database",
        description="Executes arbitrary SQL",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
            ServiceParameter(name="$sql", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="rowsAffected", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATABASE,
            connector_type="Database Connector",
            configuration={"operation": "Execute"},
            notes="Use Database connector with Execute operation for DDL/DML"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65,
        requires_manual_review=True,
        conversion_notes=["Review SQL for compatibility"]
    ),
    
    "pub.db:beginTransaction": WMPublicService(
        service_name="pub.db:beginTransaction",
        package="WmPublic",
        category="database",
        description="Begins database transaction",
        inputs=[
            ServiceParameter(name="$dbAlias", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="$txid", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRY_CATCH,
            notes="Boomi handles transactions at process level or via connector"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True,
        conversion_notes=[
            "Boomi transaction handling differs",
            "Consider using Process Transaction or connector-level transactions"
        ]
    ),
    
    "pub.db:commit": WMPublicService(
        service_name="pub.db:commit",
        package="WmPublic",
        category="database",
        description="Commits database transaction",
        inputs=[
            ServiceParameter(name="$txid", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRY_CATCH,
            notes="Automatic commit in Boomi or configure explicit"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True
    ),
    
    "pub.db:rollback": WMPublicService(
        service_name="pub.db:rollback",
        package="WmPublic",
        category="database",
        description="Rolls back database transaction",
        inputs=[
            ServiceParameter(name="$txid", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.EXCEPTION,
            notes="Use Exception shape in Catch block"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True
    ),
}


# =============================================================================
# HTTP CLIENT SERVICES (20+ services)
# =============================================================================

HTTP_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.client:http": WMPublicService(
        service_name="pub.client:http",
        package="WmPublic",
        category="http",
        description="Makes HTTP request",
        inputs=[
            ServiceParameter(name="url", type="string", required=True),
            ServiceParameter(name="method", type="string", required=False, default="GET"),
            ServiceParameter(name="data", type="object", required=False),
            ServiceParameter(name="headers", type="document", required=False),
            ServiceParameter(name="auth", type="document", required=False),
            ServiceParameter(name="timeout", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="output", type="object"),
            ServiceParameter(name="statusCode", type="string"),
            ServiceParameter(name="statusMessage", type="string"),
            ServiceParameter(name="headers", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.HTTP,
            connector_type="HTTP Client Connector",
            notes="Use HTTP Client connector with appropriate method"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.client:soapHTTP": WMPublicService(
        service_name="pub.client:soapHTTP",
        package="WmPublic",
        category="http",
        description="Makes SOAP HTTP request",
        inputs=[
            ServiceParameter(name="url", type="string", required=True),
            ServiceParameter(name="soapAction", type="string", required=False),
            ServiceParameter(name="data", type="object", required=True),
            ServiceParameter(name="headers", type="document", required=False),
        ],
        outputs=[
            ServiceParameter(name="output", type="object"),
            ServiceParameter(name="statusCode", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SOAP,
            connector_type="Web Services SOAP Client",
            notes="Use Web Services SOAP Client connector"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        conversion_notes=["Import WSDL to create SOAP connector operation"]
    ),
    
    "pub.client:soapRPC": WMPublicService(
        service_name="pub.client:soapRPC",
        package="WmPublic",
        category="http",
        description="Makes SOAP RPC request",
        inputs=[
            ServiceParameter(name="url", type="string", required=True),
            ServiceParameter(name="soapAction", type="string", required=True),
            ServiceParameter(name="encodingStyle", type="string", required=False),
            ServiceParameter(name="data", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="output", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SOAP,
            connector_type="Web Services SOAP Client",
            notes="Use SOAP connector; RPC style may need adjustment"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
    
    "pub.soap:addHeaderEntry": WMPublicService(
        service_name="pub.soap:addHeaderEntry",
        package="WmPublic",
        category="http",
        description="Adds SOAP header entry",
        inputs=[
            ServiceParameter(name="headerEntryName", type="string", required=True),
            ServiceParameter(name="headerEntryContent", type="document", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Dynamic Document Properties or SOAP connector headers"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
    
    "pub.soap:getHeaderEntry": WMPublicService(
        service_name="pub.soap:getHeaderEntry",
        package="WmPublic",
        category="http",
        description="Gets SOAP header entry",
        inputs=[
            ServiceParameter(name="headerEntryName", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="headerEntryContent", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Access headers through connector response profile"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
}


# =============================================================================
# FTP/SFTP SERVICES (15+ services)
# =============================================================================

FTP_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.client.ftp:get": WMPublicService(
        service_name="pub.client.ftp:get",
        package="WmPublic",
        category="ftp",
        description="Downloads file via FTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotefile", type="string", required=True),
            ServiceParameter(name="localfile", type="string", required=False),
            ServiceParameter(name="transfermode", type="string", required=False, default="binary"),
        ],
        outputs=[
            ServiceParameter(name="content", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.FTP,
            connector_type="FTP Connector",
            configuration={"operation": "Get"},
            notes="Use FTP connector with Get operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client.ftp:put": WMPublicService(
        service_name="pub.client.ftp:put",
        package="WmPublic",
        category="ftp",
        description="Uploads file via FTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotefile", type="string", required=True),
            ServiceParameter(name="content", type="object", required=True),
            ServiceParameter(name="transfermode", type="string", required=False, default="binary"),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.FTP,
            connector_type="FTP Connector",
            configuration={"operation": "Send"},
            notes="Use FTP connector with Send operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client.ftp:delete": WMPublicService(
        service_name="pub.client.ftp:delete",
        package="WmPublic",
        category="ftp",
        description="Deletes file via FTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotefile", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.FTP,
            connector_type="FTP Connector",
            configuration={"operation": "Delete"},
            notes="Use FTP connector with Delete operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client.ftp:ls": WMPublicService(
        service_name="pub.client.ftp:ls",
        package="WmPublic",
        category="ftp",
        description="Lists directory via FTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotedirectory", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="files", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.FTP,
            connector_type="FTP Connector",
            configuration={"operation": "List"},
            notes="Use FTP connector with Directory operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client.sftp:get": WMPublicService(
        service_name="pub.client.sftp:get",
        package="WmPublic",
        category="sftp",
        description="Downloads file via SFTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotefile", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="content", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SFTP,
            connector_type="SFTP Connector",
            configuration={"operation": "Get"},
            notes="Use SFTP connector with Get operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client.sftp:put": WMPublicService(
        service_name="pub.client.sftp:put",
        package="WmPublic",
        category="sftp",
        description="Uploads file via SFTP",
        inputs=[
            ServiceParameter(name="serveralias", type="string", required=True),
            ServiceParameter(name="remotefile", type="string", required=True),
            ServiceParameter(name="content", type="object", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SFTP,
            connector_type="SFTP Connector",
            configuration={"operation": "Send"},
            notes="Use SFTP connector with Send operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
}


# =============================================================================
# EDI SERVICES (30+ services)
# =============================================================================

EDI_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.edi:convertToValues": WMPublicService(
        service_name="pub.edi:convertToValues",
        package="WmPublic",
        category="edi",
        description="Converts EDI to document",
        inputs=[
            ServiceParameter(name="edidata", type="object", required=True),
            ServiceParameter(name="schema", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with EDI profile as input"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80,
        conversion_notes=["Create EDI profile in Boomi"]
    ),
    
    "pub.edi:convertToString": WMPublicService(
        service_name="pub.edi:convertToString",
        package="WmPublic",
        category="edi",
        description="Converts document to EDI string",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="schema", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="edidata", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with EDI profile as output"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=80
    ),
    
    "pub.estd.X12:X12EnvelopeToDocument": WMPublicService(
        service_name="pub.estd.X12:X12EnvelopeToDocument",
        package="WmPublic",
        category="edi",
        description="Parses X12 envelope",
        inputs=[
            ServiceParameter(name="X12Envelope", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
            ServiceParameter(name="ISA", type="document"),
            ServiceParameter(name="GS", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Use Trading Partner shape with X12 profile"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        requires_manual_review=True,
        conversion_notes=["Configure Trading Partner in Boomi"]
    ),
    
    "pub.estd.X12:documentToX12Envelope": WMPublicService(
        service_name="pub.estd.X12:documentToX12Envelope",
        package="WmPublic",
        category="edi",
        description="Creates X12 envelope",
        inputs=[
            ServiceParameter(name="document", type="document", required=True),
            ServiceParameter(name="ISA", type="document", required=True),
            ServiceParameter(name="GS", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="X12Envelope", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Use Trading Partner shape with X12 envelope"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        requires_manual_review=True
    ),
    
    "pub.estd.EDIFACT:EDIFACTEnvelopeToDocument": WMPublicService(
        service_name="pub.estd.EDIFACT:EDIFACTEnvelopeToDocument",
        package="WmPublic",
        category="edi",
        description="Parses EDIFACT envelope",
        inputs=[
            ServiceParameter(name="EDIFACTEnvelope", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="document", type="document"),
            ServiceParameter(name="UNB", type="document"),
            ServiceParameter(name="UNG", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Use Trading Partner shape with EDIFACT profile"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        requires_manual_review=True
    ),
    
    "pub.edi.validate": WMPublicService(
        service_name="pub.edi.validate",
        package="WmPublic",
        category="edi",
        description="Validates EDI document",
        inputs=[
            ServiceParameter(name="edidata", type="object", required=True),
            ServiceParameter(name="schema", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="isValid", type="string"),
            ServiceParameter(name="errors", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Map shape with validation; errors in document property"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Configure EDI profile validation in Boomi"]
    ),
}


# =============================================================================
# JMS SERVICES (15+ services)
# =============================================================================

JMS_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.jms:send": WMPublicService(
        service_name="pub.jms:send",
        package="WmPublic",
        category="jms",
        description="Sends JMS message",
        inputs=[
            ServiceParameter(name="connectionAliasName", type="string", required=True),
            ServiceParameter(name="destinationName", type="string", required=True),
            ServiceParameter(name="destinationType", type="string", required=True, description="queue or topic"),
            ServiceParameter(name="body", type="object", required=True),
            ServiceParameter(name="JMSMessage", type="document", required=False),
        ],
        outputs=[
            ServiceParameter(name="JMSMessage", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.JMS,
            connector_type="JMS Connector",
            configuration={"operation": "Send"},
            notes="Use JMS connector with Send operation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75,
        conversion_notes=["Configure JMS connection in Boomi"]
    ),
    
    "pub.jms:receive": WMPublicService(
        service_name="pub.jms:receive",
        package="WmPublic",
        category="jms",
        description="Receives JMS message",
        inputs=[
            ServiceParameter(name="connectionAliasName", type="string", required=True),
            ServiceParameter(name="destinationName", type="string", required=True),
            ServiceParameter(name="destinationType", type="string", required=True),
            ServiceParameter(name="timeout", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="body", type="object"),
            ServiceParameter(name="JMSMessage", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.JMS,
            connector_type="JMS Connector",
            configuration={"operation": "Listen"},
            notes="Use JMS connector with Listen operation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=75
    ),
    
    "pub.jms:reply": WMPublicService(
        service_name="pub.jms:reply",
        package="WmPublic",
        category="jms",
        description="Sends JMS reply message",
        inputs=[
            ServiceParameter(name="connectionAliasName", type="string", required=True),
            ServiceParameter(name="JMSMessage", type="document", required=True),
            ServiceParameter(name="body", type="object", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.JMS,
            connector_type="JMS Connector",
            configuration={"operation": "Send"},
            notes="Use JMS connector; set JMSReplyTo destination"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
}


# =============================================================================
# MAIL SERVICES (10+ services)
# =============================================================================

MAIL_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.client:smtp": WMPublicService(
        service_name="pub.client:smtp",
        package="WmPublic",
        category="mail",
        description="Sends email via SMTP",
        inputs=[
            ServiceParameter(name="to", type="string", required=True),
            ServiceParameter(name="from", type="string", required=True),
            ServiceParameter(name="subject", type="string", required=True),
            ServiceParameter(name="body", type="string", required=True),
            ServiceParameter(name="cc", type="string", required=False),
            ServiceParameter(name="bcc", type="string", required=False),
            ServiceParameter(name="attachments", type="documentList", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAIL,
            connector_type="Mail Connector",
            configuration={"operation": "Send"},
            notes="Use Mail connector with Send operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "pub.client:pop3": WMPublicService(
        service_name="pub.client:pop3",
        package="WmPublic",
        category="mail",
        description="Receives email via POP3",
        inputs=[
            ServiceParameter(name="server", type="string", required=True),
            ServiceParameter(name="user", type="string", required=True),
            ServiceParameter(name="password", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="messages", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAIL,
            connector_type="Mail Connector",
            configuration={"operation": "Get"},
            notes="Use Mail connector with Get operation"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
    
    "pub.client:imap": WMPublicService(
        service_name="pub.client:imap",
        package="WmPublic",
        category="mail",
        description="Receives email via IMAP",
        inputs=[
            ServiceParameter(name="server", type="string", required=True),
            ServiceParameter(name="user", type="string", required=True),
            ServiceParameter(name="password", type="string", required=True),
            ServiceParameter(name="folder", type="string", required=False, default="INBOX"),
        ],
        outputs=[
            ServiceParameter(name="messages", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAIL,
            connector_type="Mail Connector",
            configuration={"operation": "Get"},
            notes="Use Mail connector with Get operation and IMAP settings"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
}


# =============================================================================
# AGGREGATE PART 3 SERVICES
# =============================================================================

def get_part3_services() -> Dict[str, WMPublicService]:
    """Returns all services from part 3"""
    all_services = {}
    all_services.update(DATABASE_SERVICES)
    all_services.update(HTTP_SERVICES)
    all_services.update(FTP_SERVICES)
    all_services.update(EDI_SERVICES)
    all_services.update(JMS_SERVICES)
    all_services.update(MAIL_SERVICES)
    return all_services


PART3_SERVICE_COUNTS = {
    "database": len(DATABASE_SERVICES),
    "http": len(HTTP_SERVICES),
    "ftp": len(FTP_SERVICES),
    "edi": len(EDI_SERVICES),
    "jms": len(JMS_SERVICES),
    "mail": len(MAIL_SERVICES),
}
