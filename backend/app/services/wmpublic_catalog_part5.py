"""
wMPublic Service Catalog - Part 5
Specialized services: Server, Trading Partner, Event, Cache, MIME
"""

from typing import Dict
from app.services.wmpublic_catalog import (
    WMPublicService, ServiceParameter, BoomiEquivalent,
    BoomiShapeType, ConversionComplexity
)


# =============================================================================
# WM.SERVER SERVICES (20+ services)
# =============================================================================

SERVER_SERVICES: Dict[str, WMPublicService] = {
    
    "wm.server:getSession": WMPublicService(
        service_name="wm.server:getSession",
        package="WmRoot",
        category="server",
        description="Gets current session information",
        inputs=[],
        outputs=[
            ServiceParameter(name="session", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Execution Properties in Boomi"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60,
        conversion_notes=["Session handling differs in Boomi; use execution context"]
    ),
    
    "wm.server:getUser": WMPublicService(
        service_name="wm.server:getUser",
        package="WmRoot",
        category="server",
        description="Gets current user information",
        inputs=[],
        outputs=[
            ServiceParameter(name="user", type="string"),
            ServiceParameter(name="groups", type="stringList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Dynamic Document Properties for user context"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=55,
        requires_manual_review=True,
        conversion_notes=["User context handling varies by Boomi connector used"]
    ),
    
    "wm.server:log": WMPublicService(
        service_name="wm.server:log",
        package="WmRoot",
        category="server",
        description="Writes to server log",
        inputs=[
            ServiceParameter(name="message", type="string", required=True),
            ServiceParameter(name="level", type="string", required=False, default="INFO"),
            ServiceParameter(name="function", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.NOTIFY,
            notes="Use Notify shape or Process Logging"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=85
    ),
    
    "wm.server:getServerInfo": WMPublicService(
        service_name="wm.server:getServerInfo",
        package="WmRoot",
        category="server",
        description="Gets server information",
        inputs=[],
        outputs=[
            ServiceParameter(name="serverInfo", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy to get Atom info"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60
    ),
    
    "wm.server:shutdown": WMPublicService(
        service_name="wm.server:shutdown",
        package="WmRoot",
        category="server",
        description="Shuts down the server",
        inputs=[
            ServiceParameter(name="delay", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.STOP,
            notes="No equivalent - Boomi Atoms are managed differently"
        ),
        complexity=ConversionComplexity.MANUAL,
        automation_level=0,
        requires_manual_review=True,
        conversion_notes=["Server management not applicable in Boomi"]
    ),
}


# =============================================================================
# TRADING PARTNER SERVICES (WM.TN) (25+ services)
# =============================================================================

TN_SERVICES: Dict[str, WMPublicService] = {
    
    "wm.tn:receive": WMPublicService(
        service_name="wm.tn:receive",
        package="WmTN",
        category="tn",
        description="Receives a document from Trading Network",
        inputs=[
            ServiceParameter(name="bizdoc", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="bizdoc", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Use Trading Partner Management connector"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True,
        conversion_notes=["Configure Trading Partner in Boomi; review document type mapping"]
    ),
    
    "wm.tn:send": WMPublicService(
        service_name="wm.tn:send",
        package="WmTN",
        category="tn",
        description="Sends a document through Trading Network",
        inputs=[
            ServiceParameter(name="bizdoc", type="document", required=True),
            ServiceParameter(name="receiverId", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="bizdoc", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Use Trading Partner Management connector"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=50,
        requires_manual_review=True
    ),
    
    "wm.tn.profile:getProfileByID": WMPublicService(
        service_name="wm.tn.profile:getProfileByID",
        package="WmTN",
        category="tn",
        description="Gets Trading Partner profile",
        inputs=[
            ServiceParameter(name="profileId", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="profile", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.TRADING_PARTNER,
            notes="Trading Partner lookup in Boomi"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60
    ),
    
    "wm.tn.route:route": WMPublicService(
        service_name="wm.tn.route:route",
        package="WmTN",
        category="tn",
        description="Routes document through TN rules",
        inputs=[
            ServiceParameter(name="bizdoc", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="routingResults", type="document"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DECISION,
            notes="Routing logic must be rebuilt in Boomi process"
        ),
        complexity=ConversionComplexity.COMPLEX,
        automation_level=30,
        requires_manual_review=True,
        conversion_notes=["TN routing rules must be analyzed and recreated in Boomi"]
    ),
}


# =============================================================================
# EVENT/SCHEDULER SERVICES (15+ services)
# =============================================================================

EVENT_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.event:publishEvent": WMPublicService(
        service_name="pub.event:publishEvent",
        package="WmPublic",
        category="event",
        description="Publishes event to broker",
        inputs=[
            ServiceParameter(name="event", type="document", required=True),
            ServiceParameter(name="eventTypeName", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.JMS,
            connector_type="Event connector or JMS",
            notes="Use appropriate message connector"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65,
        conversion_notes=["Map event publishing to JMS or appropriate connector"]
    ),
    
    "pub.event:subscribeToEvent": WMPublicService(
        service_name="pub.event:subscribeToEvent",
        package="WmPublic",
        category="event",
        description="Subscribes to events",
        inputs=[
            ServiceParameter(name="eventTypeName", type="string", required=True),
            ServiceParameter(name="filter", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.JMS,
            notes="Configure as listener/polling in Boomi"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60,
        requires_manual_review=True
    ),
    
    "pub.scheduler:addTask": WMPublicService(
        service_name="pub.scheduler:addTask",
        package="WmPublic",
        category="event",
        description="Adds scheduled task",
        inputs=[
            ServiceParameter(name="service", type="string", required=True),
            ServiceParameter(name="schedule", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="taskId", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.PROCESS_CALL,
            notes="Configure as scheduled process in Boomi"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60,
        conversion_notes=["Create scheduled process in Boomi"]
    ),
    
    "pub.scheduler:removeTask": WMPublicService(
        service_name="pub.scheduler:removeTask",
        package="WmPublic",
        category="event",
        description="Removes scheduled task",
        inputs=[
            ServiceParameter(name="taskId", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.STOP,
            notes="Manage schedule through Boomi UI or API"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=50
    ),
}


# =============================================================================
# CACHE SERVICES (10+ services)
# =============================================================================

CACHE_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.cache:put": WMPublicService(
        service_name="pub.cache:put",
        package="WmPublic",
        category="cache",
        description="Puts value in cache",
        inputs=[
            ServiceParameter(name="cacheName", type="string", required=True),
            ServiceParameter(name="key", type="string", required=True),
            ServiceParameter(name="value", type="object", required=True),
            ServiceParameter(name="ttl", type="string", required=False),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.SET_PROPERTIES,
            notes="Use Document Cache in Boomi"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70,
        conversion_notes=["Configure Document Cache component"]
    ),
    
    "pub.cache:get": WMPublicService(
        service_name="pub.cache:get",
        package="WmPublic",
        category="cache",
        description="Gets value from cache",
        inputs=[
            ServiceParameter(name="cacheName", type="string", required=True),
            ServiceParameter(name="key", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="value", type="object"),
            ServiceParameter(name="exists", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Use Document Cache lookup"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=70
    ),
    
    "pub.cache:remove": WMPublicService(
        service_name="pub.cache:remove",
        package="WmPublic",
        category="cache",
        description="Removes value from cache",
        inputs=[
            ServiceParameter(name="cacheName", type="string", required=True),
            ServiceParameter(name="key", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Document Cache doesn't have explicit remove; use TTL"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=60
    ),
    
    "pub.cache:clear": WMPublicService(
        service_name="pub.cache:clear",
        package="WmPublic",
        category="cache",
        description="Clears entire cache",
        inputs=[
            ServiceParameter(name="cacheName", type="string", required=True),
        ],
        outputs=[],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="No direct equivalent; cache expires by TTL"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=50
    ),
}


# =============================================================================
# MIME/MULTIPART SERVICES (15+ services)
# =============================================================================

MIME_SERVICES: Dict[str, WMPublicService] = {
    
    "pub.mime:createMimeData": WMPublicService(
        service_name="pub.mime:createMimeData",
        package="WmPublic",
        category="mime",
        description="Creates MIME multipart message",
        inputs=[
            ServiceParameter(name="parts", type="documentList", required=True),
            ServiceParameter(name="boundary", type="string", required=False),
        ],
        outputs=[
            ServiceParameter(name="mimeData", type="object"),
            ServiceParameter(name="contentType", type="string"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy for MIME construction"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65
    ),
    
    "pub.mime:parseMimeData": WMPublicService(
        service_name="pub.mime:parseMimeData",
        package="WmPublic",
        category="mime",
        description="Parses MIME multipart message",
        inputs=[
            ServiceParameter(name="mimeData", type="object", required=True),
            ServiceParameter(name="contentType", type="string", required=True),
        ],
        outputs=[
            ServiceParameter(name="parts", type="documentList"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy for MIME parsing"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65
    ),
    
    "pub.mime:addMimePart": WMPublicService(
        service_name="pub.mime:addMimePart",
        package="WmPublic",
        category="mime",
        description="Adds part to MIME message",
        inputs=[
            ServiceParameter(name="mimeData", type="object", required=True),
            ServiceParameter(name="part", type="document", required=True),
        ],
        outputs=[
            ServiceParameter(name="mimeData", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.DATA_PROCESS,
            notes="Use Groovy for MIME manipulation"
        ),
        complexity=ConversionComplexity.MODERATE,
        automation_level=65
    ),
    
    "pub.mime:getEnvelopeStream": WMPublicService(
        service_name="pub.mime:getEnvelopeStream",
        package="WmPublic",
        category="mime",
        description="Gets MIME envelope as stream",
        inputs=[
            ServiceParameter(name="mimeData", type="object", required=True),
        ],
        outputs=[
            ServiceParameter(name="stream", type="object"),
        ],
        boomi_equivalent=BoomiEquivalent(
            shape_type=BoomiShapeType.MAP,
            notes="Boomi handles streaming natively"
        ),
        complexity=ConversionComplexity.SIMPLE,
        automation_level=80
    ),
}


# =============================================================================
# AGGREGATE PART 5 SERVICES
# =============================================================================

def get_part5_services() -> Dict[str, WMPublicService]:
    """Returns all services from part 5"""
    all_services = {}
    all_services.update(SERVER_SERVICES)
    all_services.update(TN_SERVICES)
    all_services.update(EVENT_SERVICES)
    all_services.update(CACHE_SERVICES)
    all_services.update(MIME_SERVICES)
    return all_services


PART5_SERVICE_COUNTS = {
    "server": len(SERVER_SERVICES),
    "tn": len(TN_SERVICES),
    "event": len(EVENT_SERVICES),
    "cache": len(CACHE_SERVICES),
    "mime": len(MIME_SERVICES),
}
