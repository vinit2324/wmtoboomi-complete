import zipfile
import os
from pathlib import Path
from datetime import datetime
import shutil

PACKAGE_NAME = "enterprise_integration_suite_v3"
OUTPUT_ZIP = f"/Users/vinitverma/wmtoboomi-complete/{PACKAGE_NAME}.zip"

temp_dir = Path(f"/tmp/{PACKAGE_NAME}")
if temp_dir.exists():
    shutil.rmtree(temp_dir)
temp_dir.mkdir(parents=True)

def create_flow(path, name, desc, steps):
    svc_dir = temp_dir / path / name
    svc_dir.mkdir(parents=True, exist_ok=True)
    
    steps_xml = ""
    for s in steps:
        t = s.get('t', '')
        n = s.get('n', 'step')
        svc = s.get('s', 'pub.flow:savePipeline')
        sw = s.get('sw', '$docType')
        on = s.get('on', 'items')
        
        if t == 'SEQ':
            steps_xml += f'      <SEQUENCE label="{n}">\n'
        elif t == 'ESEQ':
            steps_xml += '      </SEQUENCE>\n'
        elif t == 'INV':
            steps_xml += f'        <INVOKE label="{n}"><SERVICE name="{svc}"/><INPUT><record javaclass="com.wm.util.Values"><value name="doc">%doc%</value></record></INPUT><OUTPUT name="result"/></INVOKE>\n'
        elif t == 'MAP':
            steps_xml += f'        <MAP label="{n}"><MAPSOURCE><record name="src"/></MAPSOURCE><MAPTARGET><record name="tgt"/></MAPTARGET></MAP>\n'
        elif t == 'BR':
            steps_xml += f'        <BRANCH label="{n}" switch="{sw}">\n'
        elif t == 'EBR':
            steps_xml += '        </BRANCH>\n'
        elif t == 'LP':
            steps_xml += f'        <LOOP label="{n}" on="{on}">\n'
        elif t == 'ELP':
            steps_xml += '        </LOOP>\n'
        elif t == 'REP':
            steps_xml += f'        <REPEAT label="{n}" count="3">\n'
        elif t == 'EREP':
            steps_xml += '        </REPEAT>\n'
        elif t == 'EX':
            steps_xml += f'        <EXIT label="{n}" signal="SUCCESS"/>\n'
    
    flow = f'''<?xml version="1.0" encoding="UTF-8"?>
<FLOW VERSION="3.0" CLEANUP="true">
  <service name="{path.replace('/','.')}.{name}">
    <description>{desc}</description>
    <inVars><var name="inputDoc" type="record"/><var name="partnerId" type="string"/></inVars>
    <outVars><var name="outputDoc" type="record"/><var name="status" type="string"/></outVars>
    <SEQUENCE label="Main">
{steps_xml}
    </SEQUENCE>
  </service>
</FLOW>'''
    (svc_dir / "flow.xml").write_text(flow)
    (svc_dir / "node.ndf").write_text('<Values version="2.0"><value name="node_type">service</value><value name="svc_type">flow</value><value name="is_public">true</value></Values>')

def create_doc(path, name, fields):
    doc_dir = temp_dir / path / name
    doc_dir.mkdir(parents=True, exist_ok=True)
    fxml = "".join([f'<value name="{f}"/>' for f in fields])
    (doc_dir / "node.ndf").write_text(f'<Values version="2.0"><value name="node_type">record</value><record name="fields">{fxml}</record></Values>')

def create_java(path, name, desc):
    svc_dir = temp_dir / path / name
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "java.frag").write_text(f'// {name}\n// {desc}\npackage {path.replace("/",".")};\nimport com.wm.data.*;\npublic class {name} {{ public static void main(IData p) throws Exception {{ }} }}')
    (svc_dir / "node.ndf").write_text('<Values version="2.0"><value name="node_type">service</value><value name="svc_type">java</value></Values>')

print("Creating Enterprise Integration Suite...")

# Integration 1: EDI 850 Purchase Order Inbound
create_flow("NS/enterprise/b2b/edi/inbound", "processEDI850_PurchaseOrder",
    "Inbound EDI 850 Purchase Order - Parse EDI, validate, map to canonical order, create ERP sales order",
    [{'t':'SEQ','n':'ParseEDI'},{'t':'INV','n':'ConvertEDItoValues','s':'wm.b2b.edi:convertToValues'},{'t':'INV','n':'ValidateEDI','s':'wm.b2b.edi:validate'},{'t':'INV','n':'GetTradingPartner','s':'wm.tn:getPartnerProfile'},{'t':'ESEQ'},{'t':'SEQ','n':'TransformOrder'},{'t':'MAP','n':'MapPOHeader'},{'t':'LP','n':'ProcessLineItems','on':'POLines'},{'t':'MAP','n':'MapLineItem'},{'t':'INV','n':'CheckInventory','s':'pub.client:http'},{'t':'ELP'},{'t':'ESEQ'},{'t':'SEQ','n':'CreateERPOrder'},{'t':'INV','n':'CreateSalesOrder','s':'pub.sap:call'},{'t':'INV','n':'Send997Ack','s':'wm.b2b.edi:send997'},{'t':'ESEQ'}])

# Integration 2: EDI 856 ASN Outbound
create_flow("NS/enterprise/b2b/edi/outbound", "generateEDI856_ASN",
    "Generate EDI 856 Advance Ship Notice - Get shipment data, build EDI, transmit to trading partner",
    [{'t':'SEQ','n':'GetShipmentData'},{'t':'INV','n':'QueryShipments','s':'pub.db:query'},{'t':'INV','n':'GetCarrierDetails','s':'pub.client:http'},{'t':'ESEQ'},{'t':'SEQ','n':'BuildASN'},{'t':'MAP','n':'MapShipmentHeader'},{'t':'LP','n':'ProcessPackages','on':'packages'},{'t':'MAP','n':'MapPackageDetails'},{'t':'LP','n':'ProcessItems','on':'lineItems'},{'t':'MAP','n':'MapItemDetails'},{'t':'ELP'},{'t':'ELP'},{'t':'ESEQ'},{'t':'SEQ','n':'TransmitASN'},{'t':'INV','n':'ConvertToEDI','s':'wm.b2b.edi:convertToString'},{'t':'INV','n':'TransmitAS2','s':'wm.b2b.as2:send'},{'t':'INV','n':'LogTransaction','s':'wm.tn:logActivity'},{'t':'ESEQ'}])

# Integration 3: EDI 810 Invoice Outbound
create_flow("NS/enterprise/b2b/edi/outbound", "generateEDI810_Invoice",
    "Generate EDI 810 Invoice - Get billing data from ERP, generate invoice, transmit",
    [{'t':'SEQ','n':'GetInvoiceData'},{'t':'INV','n':'QueryBillingDocs','s':'pub.sap:call'},{'t':'INV','n':'GetCustomerProfile','s':'wm.tn:getPartnerProfile'},{'t':'BR','n':'CheckInvoiceType','sw':'$invoiceType'},{'t':'MAP','n':'MapCreditMemo'},{'t':'MAP','n':'MapDebitMemo'},{'t':'MAP','n':'MapStandardInvoice'},{'t':'EBR'},{'t':'ESEQ'},{'t':'SEQ','n':'GenerateEDI'},{'t':'LP','n':'ProcessInvoiceLines','on':'invoiceLines'},{'t':'MAP','n':'MapLineCharges'},{'t':'MAP','n':'CalculateTaxes'},{'t':'ELP'},{'t':'INV','n':'BuildEDI810','s':'wm.b2b.edi:convertToString'},{'t':'ESEQ'},{'t':'INV','n':'TransmitInvoice','s':'wm.b2b.as2:send'}])

# Integration 4: EDI 940 Warehouse Order
create_flow("NS/enterprise/b2b/edi/outbound", "generateEDI940_WarehouseOrder",
    "Generate EDI 940 Warehouse Shipping Order to 3PL",
    [{'t':'SEQ','n':'PrepareWarehouseOrder'},{'t':'INV','n':'GetSalesOrder','s':'pub.sap:call'},{'t':'INV','n':'GetInventoryLocation','s':'pub.db:query'},{'t':'INV','n':'Get3PLProfile','s':'wm.tn:getPartnerProfile'},{'t':'ESEQ'},{'t':'MAP','n':'MapWarehouseHeader'},{'t':'LP','n':'ProcessOrderLines','on':'orderLines'},{'t':'MAP','n':'MapPickDetails'},{'t':'BR','n':'CheckHazmat','sw':'$hazmatFlag'},{'t':'MAP','n':'AddHazmatInfo'},{'t':'EBR'},{'t':'ELP'},{'t':'INV','n':'Build940','s':'wm.b2b.edi:convertToString'},{'t':'INV','n':'SendTo3PL','s':'wm.b2b.sftp:put'}])

# Integration 5: EDI 945 Warehouse Advice Inbound
create_flow("NS/enterprise/b2b/edi/inbound", "processEDI945_WarehouseAdvice",
    "Process EDI 945 Warehouse Shipping Advice from 3PL - Update inventory, trigger ASN",
    [{'t':'SEQ','n':'ReceiveAdvice'},{'t':'INV','n':'ParseEDI945','s':'wm.b2b.edi:convertToValues'},{'t':'INV','n':'ValidateAdvice','s':'wm.b2b.edi:validate'},{'t':'ESEQ'},{'t':'SEQ','n':'UpdateInventory'},{'t':'LP','n':'ProcessShippedItems','on':'shippedItems'},{'t':'INV','n':'DecrementInventory','s':'pub.db:update'},{'t':'INV','n':'UpdateSAPStock','s':'pub.sap:call'},{'t':'ELP'},{'t':'ESEQ'},{'t':'SEQ','n':'TriggerDownstream'},{'t':'INV','n':'PublishShipEvent','s':'pub.jms:send'},{'t':'INV','n':'TriggerASNGeneration','s':'pub.flow:invokeService'},{'t':'ESEQ'}])

# Integration 6: SAP Sales Order Sync
create_flow("NS/enterprise/erp/sap/orders", "syncSalesOrder",
    "Sync sales orders between systems - Real-time order replication to SAP SD",
    [{'t':'SEQ','n':'ValidateOrder'},{'t':'INV','n':'SchemaValidation','s':'pub.schema:validate'},{'t':'INV','n':'CheckCustomerCredit','s':'pub.sap:call'},{'t':'BR','n':'CreditCheck','sw':'$creditStatus'},{'t':'INV','n':'HoldOrder','s':'pub.flow:throwException'},{'t':'MAP','n':'ProceedWithOrder'},{'t':'EBR'},{'t':'ESEQ'},{'t':'SEQ','n':'CreateSAPOrder'},{'t':'MAP','n':'MapToSAPIDOC'},{'t':'INV','n':'PostVA01','s':'pub.sap:call'},{'t':'INV','n':'GetOrderNumber','s':'pub.sap:call'},{'t':'ESEQ'},{'t':'SEQ','n':'Confirmation'},{'t':'INV','n':'UpdateSourceSystem','s':'pub.client:http'},{'t':'INV','n':'SendNotification','s':'pub.client:smtp'},{'t':'ESEQ'}])

# Integration 7: SAP Goods Receipt
create_flow("NS/enterprise/erp/sap/inventory", "processGoodsReceipt",
    "Process Goods Receipt from SAP - Update inventory, notify WMS",
    [{'t':'INV','n':'ReceiveIDOC','s':'pub.sap:listen'},{'t':'MAP','n':'ParseGoodsReceipt'},{'t':'SEQ','n':'UpdateInventory'},{'t':'LP','n':'ProcessMaterials','on':'materials'},{'t':'INV','n':'UpdateStockTable','s':'pub.db:update'},{'t':'BR','n':'CheckReorderPoint','sw':'$belowMin'},{'t':'INV','n':'TriggerReorder','s':'pub.jms:send'},{'t':'EBR'},{'t':'ELP'},{'t':'ESEQ'},{'t':'INV','n':'NotifyWMS','s':'pub.client:http'},{'t':'INV','n':'LogReceipt','s':'pub.db:insert'}])

# Integration 8: SAP Invoice Posting
create_flow("NS/enterprise/erp/sap/finance", "postInvoiceToSAP",
    "Post customer invoice to SAP FI - Create accounting document",
    [{'t':'SEQ','n':'PrepareInvoice'},{'t':'INV','n':'ValidateInvoice','s':'pub.schema:validate'},{'t':'INV','n':'GetGLAccounts','s':'pub.sap:call'},{'t':'INV','n':'CalculateTax','s':'pub.client:http'},{'t':'ESEQ'},{'t':'MAP','n':'MapToFIDocument'},{'t':'SEQ','n':'PostDocument'},{'t':'INV','n':'PostFB01','s':'pub.sap:call'},{'t':'BR','n':'CheckPostingResult','sw':'$status'},{'t':'INV','n':'HandleError','s':'pub.flow:throwException'},{'t':'INV','n':'GetDocNumber','s':'pub.sap:call'},{'t':'EBR'},{'t':'ESEQ'},{'t':'INV','n':'UpdateBillingStatus','s':'pub.db:update'}])

# Integration 9: Salesforce Opportunity Sync
create_flow("NS/enterprise/crm/salesforce", "syncOpportunityToOrder",
    "Sync closed-won opportunities to order management system",
    [{'t':'SEQ','n':'ReceiveOpportunity'},{'t':'INV','n':'ParseSFDCWebhook','s':'pub.json:jsonStringToDocument'},{'t':'INV','n':'QueryOpportunityDetails','s':'pub.client:http'},{'t':'INV','n':'GetAccountInfo','s':'pub.client:http'},{'t':'ESEQ'},{'t':'BR','n':'CheckOppStage','sw':'$stage'},{'t':'SEQ','n':'ProcessClosedWon'},{'t':'MAP','n':'MapOppToOrder'},{'t':'LP','n':'ProcessLineItems','on':'oppProducts'},{'t':'MAP','n':'MapProduct'},{'t':'INV','n':'CheckInventory','s':'pub.db:query'},{'t':'ELP'},{'t':'INV','n':'CreateOrderInERP','s':'pub.sap:call'},{'t':'ESEQ'},{'t':'EBR'},{'t':'INV','n':'UpdateSFDCOpp','s':'pub.client:http'}])

# Integration 10: Salesforce Customer 360
create_flow("NS/enterprise/crm/salesforce", "updateCustomer360",
    "Update Customer 360 view in Salesforce with order and service data",
    [{'t':'INV','n':'ReceiveEvent','s':'pub.jms:receive'},{'t':'MAP','n':'ParseCustomerEvent'},{'t':'SEQ','n':'AggregateData'},{'t':'INV','n':'GetOrderHistory','s':'pub.db:query'},{'t':'INV','n':'GetServiceCases','s':'pub.client:http'},{'t':'INV','n':'GetLoyaltyPoints','s':'pub.client:http'},{'t':'INV','n':'CalculateLifetimeValue','s':'pub.flow:invokeService'},{'t':'ESEQ'},{'t':'MAP','n':'BuildCustomer360'},{'t':'INV','n':'UpdateSFDCAccount','s':'pub.client:http'},{'t':'INV','n':'LogSync','s':'pub.db:insert'}])

# Integration 11: Shopify Order Ingestion
create_flow("NS/enterprise/ecommerce/shopify", "ingestShopifyOrder",
    "Real-time order ingestion from Shopify - Validate, transform, route to fulfillment",
    [{'t':'SEQ','n':'ReceiveOrder'},{'t':'INV','n':'ParseWebhook','s':'pub.json:jsonStringToDocument'},{'t':'INV','n':'ValidateHMAC','s':'pub.security:verifyHMAC'},{'t':'INV','n':'DedupCheck','s':'pub.db:query'},{'t':'ESEQ'},{'t':'SEQ','n':'EnrichOrder'},{'t':'INV','n':'GetCustomerProfile','s':'pub.db:query'},{'t':'INV','n':'ValidateTax','s':'pub.client:http'},{'t':'INV','n':'CheckFraud','s':'pub.client:http'},{'t':'BR','n':'FraudCheck','sw':'$fraudScore'},{'t':'INV','n':'HoldForReview','s':'pub.jms:send'},{'t':'MAP','n':'ProceedNormal'},{'t':'EBR'},{'t':'ESEQ'},{'t':'MAP','n':'MapToCanonicalOrder'},{'t':'INV','n':'RouteToFulfillment','s':'pub.jms:send'},{'t':'INV','n':'UpdateShopify','s':'pub.client:http'}])

# Integration 12: Inventory Sync
create_flow("NS/enterprise/ecommerce/inventory", "syncInventoryLevels",
    "Real-time inventory sync across all channels - ERP to ecommerce platforms",
    [{'t':'INV','n':'ReceiveInventoryEvent','s':'pub.jms:receive'},{'t':'MAP','n':'ParseInventoryUpdate'},{'t':'SEQ','n':'UpdateChannels'},{'t':'LP','n':'ProcessChannels','on':'channels'},{'t':'BR','n':'RouteByChannel','sw':'$channelType'},{'t':'INV','n':'UpdateShopify','s':'pub.client:http'},{'t':'INV','n':'UpdateMagento','s':'pub.client:http'},{'t':'INV','n':'UpdateAmazon','s':'pub.client:http'},{'t':'INV','n':'UpdateEbay','s':'pub.client:http'},{'t':'EBR'},{'t':'ELP'},{'t':'ESEQ'},{'t':'INV','n':'LogSyncResults','s':'pub.db:insert'}])

# Integration 13: FedEx Shipping
create_flow("NS/enterprise/logistics/shipping", "processFedExShipment",
    "Create FedEx shipment - Generate labels, track packages",
    [{'t':'SEQ','n':'PrepareShipment'},{'t':'INV','n':'GetOrderDetails','s':'pub.db:query'},{'t':'INV','n':'ValidateAddress','s':'pub.client:http'},{'t':'INV','n':'GetRates','s':'pub.client:http'},{'t':'BR','n':'SelectService','sw':'$priority'},{'t':'MAP','n':'UseFedExGround'},{'t':'MAP','n':'UseFedExExpress'},{'t':'MAP','n':'UseFedExOvernight'},{'t':'EBR'},{'t':'ESEQ'},{'t':'SEQ','n':'CreateShipment'},{'t':'INV','n':'AuthenticateFedEx','s':'pub.client:http'},{'t':'INV','n':'CreateShipmentRequest','s':'pub.client:http'},{'t':'INV','n':'GetTrackingNumber','s':'pub.xml:queryXMLNode'},{'t':'INV','n':'DownloadLabel','s':'pub.client:http'},{'t':'ESEQ'},{'t':'INV','n':'UpdateOrder','s':'pub.db:update'},{'t':'INV','n':'SendTrackingEmail','s':'pub.client:smtp'}])

# Integration 14: Returns Processing
create_flow("NS/enterprise/logistics/returns", "processReturnRequest",
    "Process customer return/RMA - Validate, create label, update inventory",
    [{'t':'SEQ','n':'ValidateReturn'},{'t':'INV','n':'GetOriginalOrder','s':'pub.db:query'},{'t':'INV','n':'CheckReturnWindow','s':'pub.flow:invokeService'},{'t':'BR','n':'ValidReturnWindow','sw':'$isValid'},{'t':'INV','n':'RejectReturn','s':'pub.client:http'},{'t':'EX','n':'ExitRejected'},{'t':'EBR'},{'t':'ESEQ'},{'t':'SEQ','n':'CreateRMA'},{'t':'INV','n':'GenerateRMANumber','s':'pub.db:insert'},{'t':'INV','n':'CreateReturnLabel','s':'pub.client:http'},{'t':'ESEQ'},{'t':'SEQ','n':'ProcessRefund'},{'t':'BR','n':'RefundMethod','sw':'$paymentMethod'},{'t':'INV','n':'RefundCreditCard','s':'pub.client:http'},{'t':'INV','n':'RefundPayPal','s':'pub.client:http'},{'t':'INV','n':'IssueStoreCredit','s':'pub.db:insert'},{'t':'EBR'},{'t':'ESEQ'},{'t':'INV','n':'NotifyCustomer','s':'pub.client:smtp'},{'t':'INV','n':'UpdateCRM','s':'pub.client:http'}])

# Integration 15: Payment Processing
create_flow("NS/enterprise/finance/payments", "processPayment",
    "Process payment through gateway - Auth, capture, record",
    [{'t':'SEQ','n':'ValidatePayment'},{'t':'INV','n':'ValidateCard','s':'pub.flow:invokeService'},{'t':'INV','n':'CheckFraud','s':'pub.client:http'},{'t':'BR','n':'FraudResult','sw':'$fraudDecision'},{'t':'INV','n':'RejectPayment','s':'pub.db:insert'},{'t':'EX','n':'ExitFraud'},{'t':'EBR'},{'t':'ESEQ'},{'t':'SEQ','n':'ProcessAuthorization'},{'t':'INV','n':'ConnectStripe','s':'pub.client:http'},{'t':'INV','n':'AuthorizePayment','s':'pub.client:http'},{'t':'BR','n':'AuthResult','sw':'$authCode'},{'t':'INV','n':'HandleDecline','s':'pub.flow:invokeService'},{'t':'SEQ','n':'CapturePayment'},{'t':'INV','n':'CaptureTransaction','s':'pub.client:http'},{'t':'INV','n':'RecordPayment','s':'pub.db:insert'},{'t':'ESEQ'},{'t':'EBR'},{'t':'ESEQ'},{'t':'INV','n':'SendReceipt','s':'pub.client:smtp'}])

# Integration 16: Tax Calculation
create_flow("NS/enterprise/finance/tax", "calculateSalesTax",
    "Real-time tax calculation using Avalara/Vertex",
    [{'t':'SEQ','n':'PrepareRequest'},{'t':'INV','n':'GetOrderDetails','s':'pub.flow:invokeService'},{'t':'INV','n':'ValidateAddresses','s':'pub.client:http'},{'t':'MAP','n':'BuildTaxRequest'},{'t':'ESEQ'},{'t':'SEQ','n':'CalculateTax'},{'t':'REP','n':'RetryLoop'},{'t':'INV','n':'CallAvalara','s':'pub.client:http'},{'t':'EREP'},{'t':'MAP','n':'ParseTaxResponse'},{'t':'ESEQ'},{'t':'LP','n':'ApplyTaxToLines','on':'lineItems'},{'t':'MAP','n':'SetLineTax'},{'t':'ELP'},{'t':'INV','n':'CacheTaxResult','s':'pub.cache:put'}])

# Integration 17: Warehouse Management
create_flow("NS/enterprise/logistics/wms", "syncWarehouseInventory",
    "Sync inventory with Manhattan WMS - Bidirectional updates",
    [{'t':'INV','n':'ReceiveWMSMessage','s':'pub.jms:receive'},{'t':'MAP','n':'ParseWMSFormat'},{'t':'BR','n':'MessageType','sw':'$msgType'},{'t':'SEQ','n':'ProcessReceipt'},{'t':'INV','n':'UpdateERPInventory','s':'pub.sap:call'},{'t':'ESEQ'},{'t':'SEQ','n':'ProcessAdjustment'},{'t':'INV','n':'RecordAdjustment','s':'pub.db:insert'},{'t':'INV','n':'PostAdjustmentSAP','s':'pub.sap:call'},{'t':'ESEQ'},{'t':'SEQ','n':'ProcessCycleCount'},{'t':'LP','n':'ProcessCountItems','on':'countItems'},{'t':'INV','n':'UpdateCount','s':'pub.db:update'},{'t':'ELP'},{'t':'ESEQ'},{'t':'EBR'},{'t':'INV','n':'PublishInventoryEvent','s':'pub.jms:send'}])

# Integration 18: Customer Master Sync
create_flow("NS/enterprise/master/customer", "syncCustomerMaster",
    "Sync customer master data across ERP, CRM, eCommerce",
    [{'t':'INV','n':'ReceiveCustomerEvent','s':'pub.jms:receive'},{'t':'MAP','n':'ParseCustomerData'},{'t':'SEQ','n':'ValidateCustomer'},{'t':'INV','n':'ValidateAddress','s':'pub.client:http'},{'t':'INV','n':'DedupCheck','s':'pub.db:query'},{'t':'INV','n':'EnrichData','s':'pub.client:http'},{'t':'ESEQ'},{'t':'SEQ','n':'SyncSystems'},{'t':'INV','n':'UpdateSAP','s':'pub.sap:call'},{'t':'INV','n':'UpdateSalesforce','s':'pub.client:http'},{'t':'INV','n':'UpdateShopify','s':'pub.client:http'},{'t':'INV','n':'UpdateMagento','s':'pub.client:http'},{'t':'ESEQ'},{'t':'INV','n':'PublishMDMEvent','s':'pub.jms:send'}])

# Integration 19: Product Information Management
create_flow("NS/enterprise/master/product", "syncProductCatalog",
    "Sync product catalog from PIM to all sales channels",
    [{'t':'SEQ','n':'GetProductUpdates'},{'t':'INV','n':'QueryPIMChanges','s':'pub.client:http'},{'t':'INV','n':'GetProductDetails','s':'pub.client:http'},{'t':'INV','n':'GetPricing','s':'pub.db:query'},{'t':'INV','n':'GetInventoryLevels','s':'pub.db:query'},{'t':'ESEQ'},{'t':'LP','n':'ProcessProducts','on':'products'},{'t':'MAP','n':'TransformProduct'},{'t':'SEQ','n':'PublishToChannels'},{'t':'INV','n':'UpdateShopifyProduct','s':'pub.client:http'},{'t':'INV','n':'UpdateMagentoProduct','s':'pub.client:http'},{'t':'INV','n':'UpdateAmazonListing','s':'pub.client:http'},{'t':'INV','n':'UpdateGoogleShopping','s':'pub.client:http'},{'t':'ESEQ'},{'t':'ELP'},{'t':'INV','n':'LogCatalogSync','s':'pub.db:insert'}])

# Integration 20: Order Status Notifications
create_flow("NS/enterprise/notifications", "sendOrderStatusUpdate",
    "Send order status notifications via email, SMS, push",
    [{'t':'INV','n':'ReceiveStatusEvent','s':'pub.jms:receive'},{'t':'MAP','n':'ParseStatusUpdate'},{'t':'SEQ','n':'GetCustomerPrefs'},{'t':'INV','n':'GetCustomer','s':'pub.db:query'},{'t':'INV','n':'GetPreferences','s':'pub.db:query'},{'t':'ESEQ'},{'t':'BR','n':'NotificationType','sw':'$statusCode'},{'t':'MAP','n':'BuildShippedMessage'},{'t':'MAP','n':'BuildDeliveredMessage'},{'t':'MAP','n':'BuildDelayedMessage'},{'t':'EBR'},{'t':'SEQ','n':'SendNotifications'},{'t':'BR','n':'ChannelPreference','sw':'$prefChannel'},{'t':'INV','n':'SendEmail','s':'pub.client:smtp'},{'t':'INV','n':'SendSMS','s':'pub.client:http'},{'t':'INV','n':'SendPush','s':'pub.client:http'},{'t':'EBR'},{'t':'ESEQ'},{'t':'INV','n':'LogNotification','s':'pub.db:insert'}])

# Supporting services
create_flow("NS/enterprise/b2b/edi/inbound", "processEDI997_Acknowledgment", "Process functional acknowledgment", [{'t':'INV','n':'ParseEDI','s':'wm.b2b.edi:convertToValues'},{'t':'MAP','n':'ExtractAckStatus'},{'t':'INV','n':'UpdateTransactionStatus','s':'pub.db:update'}])
create_flow("NS/enterprise/b2b/edi/outbound", "generateEDI855_POAck", "Generate PO acknowledgment", [{'t':'INV','n':'GetOrderStatus','s':'pub.db:query'},{'t':'MAP','n':'Build855'},{'t':'INV','n':'ConvertToEDI','s':'wm.b2b.edi:convertToString'},{'t':'INV','n':'Transmit','s':'wm.b2b.sftp:put'}])
create_flow("NS/enterprise/b2b/tn", "routeInboundEDI", "Route inbound EDI by partner and doctype", [{'t':'INV','n':'IdentifyPartner','s':'wm.tn:recognize'},{'t':'BR','n':'RouteByDocType','sw':'$docType'},{'t':'INV','n':'Route850','s':'pub.flow:invokeService'},{'t':'INV','n':'Route945','s':'pub.flow:invokeService'},{'t':'INV','n':'Route997','s':'pub.flow:invokeService'},{'t':'EBR'}])
create_flow("NS/enterprise/b2b/tn", "lookupTradingPartner", "Lookup trading partner profile", [{'t':'INV','n':'QueryPartner','s':'wm.tn:getPartnerProfile'},{'t':'MAP','n':'ExtractPartnerConfig'}])
create_flow("NS/enterprise/erp/sap/inventory", "syncInventoryToSAP", "Sync inventory adjustments to SAP MM", [{'t':'INV','n':'ReceiveAdjustment','s':'pub.jms:receive'},{'t':'MAP','n':'BuildMB1A'},{'t':'INV','n':'PostMB1A','s':'pub.sap:call'}])
create_flow("NS/enterprise/ecommerce/shopify", "syncOrderStatus", "Push order status back to Shopify", [{'t':'INV','n':'GetOrderUpdate','s':'pub.jms:receive'},{'t':'MAP','n':'BuildShopifyUpdate'},{'t':'INV','n':'UpdateShopify','s':'pub.client:http'}])
create_flow("NS/enterprise/logistics/shipping", "processUPSShipment", "Create UPS shipment", [{'t':'INV','n':'GetShipment','s':'pub.db:query'},{'t':'INV','n':'CreateUPSShip','s':'pub.client:http'},{'t':'INV','n':'GetLabel','s':'pub.client:http'}])
create_flow("NS/enterprise/finance/payments", "processRefund", "Process payment refund", [{'t':'INV','n':'GetOriginalPayment','s':'pub.db:query'},{'t':'INV','n':'RefundViaGateway','s':'pub.client:http'},{'t':'INV','n':'RecordRefund','s':'pub.db:insert'}])

# Document Types
create_doc("NS/enterprise/documents", "CanonicalOrder", ["orderId","orderDate","customerId","customerName","shipToAddress","billToAddress","orderTotal","currency","lineItems","status","source"])
create_doc("NS/enterprise/documents", "CanonicalCustomer", ["customerId","firstName","lastName","email","phone","addressLine1","addressLine2","city","state","postalCode","country","customerType","creditLimit"])
create_doc("NS/enterprise/documents", "CanonicalProduct", ["productId","sku","name","description","category","price","currency","inventory","weight","dimensions","imageUrl","status"])
create_doc("NS/enterprise/documents", "CanonicalShipment", ["shipmentId","orderId","carrier","trackingNumber","shipDate","estimatedDelivery","status","packages","weight"])
create_doc("NS/enterprise/documents", "CanonicalInvoice", ["invoiceId","orderId","customerId","invoiceDate","dueDate","lineItems","subtotal","tax","total","currency","status"])
create_doc("NS/enterprise/documents", "CanonicalPayment", ["paymentId","orderId","amount","currency","method","status","transactionId","processedDate"])
create_doc("NS/enterprise/documents", "EDI850_PurchaseOrder", ["senderId","receiverId","poNumber","poDate","shipTo","billTo","lineItems","totalAmount"])
create_doc("NS/enterprise/documents", "EDI856_ASN", ["senderId","receiverId","shipmentId","asnDate","carrier","trackingNumber","packages","lineItems"])
create_doc("NS/enterprise/documents", "EDI810_Invoice", ["senderId","receiverId","invoiceNumber","invoiceDate","poReference","lineItems","total"])
create_doc("NS/enterprise/documents", "EDI940_WarehouseOrder", ["orderId","warehouseId","shipTo","lineItems","priority","carrier"])
create_doc("NS/enterprise/documents", "TradingPartnerProfile", ["partnerId","partnerName","isaId","gsId","communicationProtocol","ftpHost","ftpUser","as2Id"])
create_doc("NS/enterprise/documents", "SAPSalesOrder", ["salesOrg","distributionChannel","division","soldTo","shipTo","poNumber","lineItems","netValue"])
create_doc("NS/enterprise/documents", "SFDCOpportunity", ["opportunityId","accountId","amount","stage","closeDate","products","probability"])

# Java Services
create_java("NS/enterprise/utils/security", "generateHMAC", "Generate HMAC signature for webhook validation")
create_java("NS/enterprise/utils/security", "encryptData", "AES encryption for sensitive data")
create_java("NS/enterprise/utils/security", "decryptData", "AES decryption for sensitive data")
create_java("NS/enterprise/utils/transform", "xmlToJson", "Convert XML to JSON")
create_java("NS/enterprise/utils/transform", "jsonToXml", "Convert JSON to XML")
create_java("NS/enterprise/utils/validation", "validateEDI", "Custom EDI validation rules")

# Create README
readme = """ENTERPRISE INTEGRATION SUITE v3
================================
Production-grade webMethods integration package for enterprise retail.

INTEGRATIONS (20 Core + 8 Supporting):
--------------------------------------
B2B/EDI:
1. EDI 850 Purchase Order Inbound
2. EDI 856 ASN Outbound
3. EDI 810 Invoice Outbound
4. EDI 940 Warehouse Order
5. EDI 945 Warehouse Advice
6. EDI 997 Acknowledgment
7. EDI 855 PO Acknowledgment
8. Trading Partner Routing

ERP (SAP):
9. Sales Order Sync (SD)
10. Goods Receipt (MM)
11. Invoice Posting (FI)
12. Inventory Sync (MM)

CRM (Salesforce):
13. Opportunity to Order
14. Customer 360 Update

eCommerce:
15. Shopify Order Ingestion
16. Multi-Channel Inventory Sync
17. Order Status Sync

Logistics:
18. FedEx Shipping
19. UPS Shipping
20. Returns/RMA Processing
21. Warehouse Management (WMS)

Finance:
22. Payment Processing (Stripe)
23. Tax Calculation (Avalara)
24. Refund Processing

Master Data:
25. Customer Master Sync
26. Product Catalog Sync

Notifications:
27. Order Status Notifications

ADAPTERS: JDBC, SAP, HTTP, JMS, SFTP, SMTP, AS2
DOCUMENT TYPES: 13
JAVA SERVICES: 6

For Jade Global Migration Accelerator Demo
"""
(temp_dir / "README.txt").write_text(readme)

# Create ZIP
print("Creating ZIP file...")
with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
    for file_path in temp_dir.rglob('*'):
        if file_path.is_file():
            arcname = str(file_path.relative_to(temp_dir.parent))
            zf.write(file_path, arcname)

flow_count = len(list(temp_dir.rglob('flow.xml')))
java_count = len(list(temp_dir.rglob('java.frag')))
doc_count = len([d for d in temp_dir.rglob('node.ndf') if 'documents' in str(d)])

print(f"\n✅ Package created: {OUTPUT_ZIP}")
print(f"\nPACKAGE CONTENTS:")
print(f"  Flow Services: {flow_count}")
print(f"  Java Services: {java_count}")
print(f"  Document Types: {doc_count}")
print(f"\nUpload this file to the Migration Accelerator!")

shutil.rmtree(temp_dir)
