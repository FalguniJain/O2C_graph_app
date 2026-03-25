"""
SAP Order-to-Cash Graph System - Backend API
"""

import json
import os
import glob
import sqlite3
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Load .env FIRST ──
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Groq setup ──
try:
    from groq import Groq
    _api_key = os.environ.get("GROQ_API_KEY", "")
    if not _api_key:
        _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(_env_path):
            with open(_env_path) as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line.startswith("GROQ_API_KEY="):
                        _api_key = _line.split("=", 1)[1].strip()
                        break
    if _api_key:
        _groq_client = Groq(api_key=_api_key)
        LLM_AVAILABLE = True
        print(f"✅ Groq ready. Key: {_api_key[:12]}...")
    else:
        LLM_AVAILABLE = False
        print("❌ WARNING: GROQ_API_KEY not found in backend/.env")
except ImportError:
    LLM_AVAILABLE = False
    print("❌ WARNING: Run: pip install groq")

app = Flask(__name__)
CORS(app)

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sap-o2c-data'))

def load_jsonl(folder):
    records = []
    pattern = os.path.join(DATA_DIR, folder, "*.jsonl")
    for f in glob.glob(pattern):
        with open(f, "r") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return records

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'o2c.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_order_headers (
        salesOrder TEXT PRIMARY KEY, salesOrderType TEXT, salesOrganization TEXT,
        distributionChannel TEXT, organizationDivision TEXT, salesGroup TEXT,
        salesOffice TEXT, soldToParty TEXT, creationDate TEXT, createdByUser TEXT,
        lastChangeDateTime TEXT, totalNetAmount REAL, overallDeliveryStatus TEXT,
        overallOrdReltdBillgStatus TEXT, overallSdDocReferenceStatus TEXT,
        transactionCurrency TEXT, pricingDate TEXT, requestedDeliveryDate TEXT,
        headerBillingBlockReason TEXT, deliveryBlockReason TEXT,
        incotermsClassification TEXT, incotermsLocation1 TEXT,
        customerPaymentTerms TEXT, totalCreditCheckStatus TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_order_items (
        salesOrder TEXT, salesOrderItem TEXT, salesOrderItemCategory TEXT,
        material TEXT, requestedQuantity REAL, requestedQuantityUnit TEXT,
        transactionCurrency TEXT, netAmount REAL, materialGroup TEXT,
        productionPlant TEXT, storageLocation TEXT, salesDocumentRjcnReason TEXT,
        itemBillingBlockReason TEXT,
        PRIMARY KEY (salesOrder, salesOrderItem)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_order_schedule_lines (
        salesOrder TEXT, salesOrderItem TEXT, scheduleLine TEXT,
        confirmedDeliveryDate TEXT, orderQuantityUnit TEXT,
        confdOrderQtyByMatlAvailCheck REAL,
        PRIMARY KEY (salesOrder, salesOrderItem, scheduleLine)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS billing_document_headers (
        billingDocument TEXT PRIMARY KEY, billingDocumentType TEXT,
        creationDate TEXT, creationTime TEXT, lastChangeDateTime TEXT,
        billingDocumentDate TEXT, billingDocumentIsCancelled TEXT,
        cancelledBillingDocument TEXT, totalNetAmount REAL,
        transactionCurrency TEXT, companyCode TEXT, fiscalYear TEXT,
        accountingDocument TEXT, soldToParty TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS billing_document_items (
        billingDocument TEXT, billingDocumentItem TEXT,
        material TEXT, billingQuantity REAL, billingQuantityUnit TEXT,
        netAmount REAL, transactionCurrency TEXT,
        referenceSdDocument TEXT, referenceSdDocumentItem TEXT,
        PRIMARY KEY (billingDocument, billingDocumentItem)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS outbound_delivery_headers (
        deliveryDocument TEXT PRIMARY KEY, actualGoodsMovementDate TEXT,
        actualGoodsMovementTime TEXT, creationDate TEXT, creationTime TEXT,
        deliveryBlockReason TEXT, hdrGeneralIncompletionStatus TEXT,
        headerBillingBlockReason TEXT, lastChangeDate TEXT,
        overallGoodsMovementStatus TEXT, overallPickingStatus TEXT,
        overallProofOfDeliveryStatus TEXT, shippingPoint TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS outbound_delivery_items (
        deliveryDocument TEXT, deliveryDocumentItem TEXT,
        actualDeliveryQuantity REAL, batch TEXT, deliveryQuantityUnit TEXT,
        itemBillingBlockReason TEXT, lastChangeDate TEXT, plant TEXT,
        referenceSdDocument TEXT, referenceSdDocumentItem TEXT,
        storageLocation TEXT,
        PRIMARY KEY (deliveryDocument, deliveryDocumentItem)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS payments (
        companyCode TEXT, fiscalYear TEXT, accountingDocument TEXT,
        accountingDocumentItem TEXT, clearingDate TEXT,
        clearingAccountingDocument TEXT, clearingDocFiscalYear TEXT,
        amountInTransactionCurrency REAL, transactionCurrency TEXT,
        amountInCompanyCodeCurrency REAL, companyCodeCurrency TEXT,
        customer TEXT, invoiceReference TEXT, invoiceReferenceFiscalYear TEXT,
        salesDocument TEXT, salesDocumentItem TEXT, postingDate TEXT,
        documentDate TEXT, assignmentReference TEXT, glAccount TEXT,
        financialAccountType TEXT, profitCenter TEXT, costCenter TEXT,
        PRIMARY KEY (accountingDocument, accountingDocumentItem, fiscalYear)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS journal_entries (
        companyCode TEXT, fiscalYear TEXT, accountingDocument TEXT,
        glAccount TEXT, referenceDocument TEXT, costCenter TEXT,
        profitCenter TEXT, transactionCurrency TEXT,
        amountInTransactionCurrency REAL, companyCodeCurrency TEXT,
        amountInCompanyCodeCurrency REAL, postingDate TEXT,
        documentDate TEXT, accountingDocumentType TEXT,
        accountingDocumentItem TEXT, assignmentReference TEXT,
        lastChangeDateTime TEXT, customer TEXT, financialAccountType TEXT,
        clearingDate TEXT, clearingAccountingDocument TEXT,
        clearingDocFiscalYear TEXT,
        PRIMARY KEY (accountingDocument, accountingDocumentItem, fiscalYear)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS business_partners (
        businessPartner TEXT PRIMARY KEY, customer TEXT,
        businessPartnerCategory TEXT, businessPartnerFullName TEXT,
        businessPartnerGrouping TEXT, businessPartnerName TEXT,
        correspondenceLanguage TEXT, createdByUser TEXT,
        creationDate TEXT, creationTime TEXT, firstName TEXT,
        formOfAddress TEXT, industry TEXT, lastChangeDate TEXT,
        lastName TEXT, organizationBpName1 TEXT, organizationBpName2 TEXT,
        businessPartnerIsBlocked TEXT, isMarkedForArchiving TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS business_partner_addresses (
        businessPartner TEXT, addressId TEXT,
        cityName TEXT, country TEXT, postalCode TEXT,
        region TEXT, streetName TEXT,
        PRIMARY KEY (businessPartner, addressId)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS customer_company_assignments (
        customer TEXT, companyCode TEXT, paymentTerms TEXT,
        reconciliationAccount TEXT, customerAccountGroup TEXT,
        PRIMARY KEY (customer, companyCode)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS customer_sales_area_assignments (
        customer TEXT, salesOrganization TEXT, distributionChannel TEXT,
        division TEXT, currency TEXT, customerPaymentTerms TEXT,
        deliveryPriority TEXT, shippingCondition TEXT, supplyingPlant TEXT,
        PRIMARY KEY (customer, salesOrganization, distributionChannel, division)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS plants (
        plant TEXT PRIMARY KEY, plantName TEXT, valuationArea TEXT,
        plantCustomer TEXT, plantSupplier TEXT, factoryCalendar TEXT,
        defaultPurchasingOrganization TEXT, salesOrganization TEXT,
        addressId TEXT, plantCategory TEXT, distributionChannel TEXT,
        division TEXT, language TEXT, isMarkedForArchiving TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        product TEXT PRIMARY KEY, productType TEXT, crossPlantStatus TEXT,
        creationDate TEXT, grossWeight REAL, weightUnit TEXT,
        netWeight REAL, productGroup TEXT, baseUnit TEXT,
        division TEXT, industrySector TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS product_descriptions (
        product TEXT, language TEXT, productDescription TEXT,
        PRIMARY KEY (product, language)
    )""")

    conn.commit()
    return conn

def populate_db():
    conn = init_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sales_order_headers")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    def safe_insert(table, records, fields):
        placeholders = ",".join(["?" for _ in fields])
        field_str = ",".join(fields)
        sql = f"INSERT OR REPLACE INTO {table} ({field_str}) VALUES ({placeholders})"
        for r in records:
            values = [r.get(f) for f in fields]
            try:
                cur.execute(sql, values)
            except Exception:
                pass

    safe_insert("sales_order_headers", load_jsonl("sales_order_headers"), [
        "salesOrder","salesOrderType","salesOrganization","distributionChannel",
        "organizationDivision","salesGroup","salesOffice","soldToParty",
        "creationDate","createdByUser","lastChangeDateTime","totalNetAmount",
        "overallDeliveryStatus","overallOrdReltdBillgStatus",
        "overallSdDocReferenceStatus","transactionCurrency","pricingDate",
        "requestedDeliveryDate","headerBillingBlockReason","deliveryBlockReason",
        "incotermsClassification","incotermsLocation1","customerPaymentTerms",
        "totalCreditCheckStatus"])

    safe_insert("sales_order_items", load_jsonl("sales_order_items"), [
        "salesOrder","salesOrderItem","salesOrderItemCategory","material",
        "requestedQuantity","requestedQuantityUnit","transactionCurrency",
        "netAmount","materialGroup","productionPlant","storageLocation",
        "salesDocumentRjcnReason","itemBillingBlockReason"])

    safe_insert("sales_order_schedule_lines", load_jsonl("sales_order_schedule_lines"), [
        "salesOrder","salesOrderItem","scheduleLine","confirmedDeliveryDate",
        "orderQuantityUnit","confdOrderQtyByMatlAvailCheck"])

    bdh_fields = ["billingDocument","billingDocumentType","creationDate","creationTime",
                  "lastChangeDateTime","billingDocumentDate","billingDocumentIsCancelled",
                  "cancelledBillingDocument","totalNetAmount","transactionCurrency",
                  "companyCode","fiscalYear","accountingDocument","soldToParty"]
    safe_insert("billing_document_headers", load_jsonl("billing_document_headers"), bdh_fields)
    safe_insert("billing_document_headers", load_jsonl("billing_document_cancellations"), bdh_fields)

    safe_insert("billing_document_items", load_jsonl("billing_document_items"), [
        "billingDocument","billingDocumentItem","material","billingQuantity",
        "billingQuantityUnit","netAmount","transactionCurrency",
        "referenceSdDocument","referenceSdDocumentItem"])

    safe_insert("outbound_delivery_headers", load_jsonl("outbound_delivery_headers"), [
        "deliveryDocument","actualGoodsMovementDate","actualGoodsMovementTime",
        "creationDate","creationTime","deliveryBlockReason",
        "hdrGeneralIncompletionStatus","headerBillingBlockReason",
        "lastChangeDate","overallGoodsMovementStatus","overallPickingStatus",
        "overallProofOfDeliveryStatus","shippingPoint"])

    safe_insert("outbound_delivery_items", load_jsonl("outbound_delivery_items"), [
        "deliveryDocument","deliveryDocumentItem","actualDeliveryQuantity",
        "batch","deliveryQuantityUnit","itemBillingBlockReason",
        "lastChangeDate","plant","referenceSdDocument",
        "referenceSdDocumentItem","storageLocation"])

    safe_insert("payments", load_jsonl("payments_accounts_receivable"), [
        "companyCode","fiscalYear","accountingDocument","accountingDocumentItem",
        "clearingDate","clearingAccountingDocument","clearingDocFiscalYear",
        "amountInTransactionCurrency","transactionCurrency",
        "amountInCompanyCodeCurrency","companyCodeCurrency","customer",
        "invoiceReference","invoiceReferenceFiscalYear","salesDocument",
        "salesDocumentItem","postingDate","documentDate","assignmentReference",
        "glAccount","financialAccountType","profitCenter","costCenter"])

    safe_insert("journal_entries", load_jsonl("journal_entry_items_accounts_receivable"), [
        "companyCode","fiscalYear","accountingDocument","glAccount",
        "referenceDocument","costCenter","profitCenter","transactionCurrency",
        "amountInTransactionCurrency","companyCodeCurrency",
        "amountInCompanyCodeCurrency","postingDate","documentDate",
        "accountingDocumentType","accountingDocumentItem","assignmentReference",
        "lastChangeDateTime","customer","financialAccountType","clearingDate",
        "clearingAccountingDocument","clearingDocFiscalYear"])

    safe_insert("business_partners", load_jsonl("business_partners"), [
        "businessPartner","customer","businessPartnerCategory","businessPartnerFullName",
        "businessPartnerGrouping","businessPartnerName","correspondenceLanguage",
        "createdByUser","creationDate","creationTime","firstName","formOfAddress",
        "industry","lastChangeDate","lastName","organizationBpName1",
        "organizationBpName2","businessPartnerIsBlocked","isMarkedForArchiving"])

    safe_insert("business_partner_addresses", load_jsonl("business_partner_addresses"), [
        "businessPartner","addressId","cityName","country","postalCode",
        "region","streetName"])

    safe_insert("customer_company_assignments", load_jsonl("customer_company_assignments"), [
        "customer","companyCode","paymentTerms","reconciliationAccount","customerAccountGroup"])

    safe_insert("customer_sales_area_assignments", load_jsonl("customer_sales_area_assignments"), [
        "customer","salesOrganization","distributionChannel","division","currency",
        "customerPaymentTerms","deliveryPriority","shippingCondition","supplyingPlant"])

    safe_insert("plants", load_jsonl("plants"), [
        "plant","plantName","valuationArea","plantCustomer","plantSupplier",
        "factoryCalendar","defaultPurchasingOrganization","salesOrganization",
        "addressId","plantCategory","distributionChannel","division",
        "language","isMarkedForArchiving"])

    safe_insert("products", load_jsonl("products"), [
        "product","productType","crossPlantStatus","creationDate","grossWeight",
        "weightUnit","netWeight","productGroup","baseUnit","division","industrySector"])

    safe_insert("product_descriptions", load_jsonl("product_descriptions"), [
        "product","language","productDescription"])

    conn.commit()
    conn.close()
    print("Database populated successfully!")

def build_graph():
    conn = get_db()
    cur = conn.cursor()
    nodes = {}
    edges = []

    def add_node(node_id, label, node_type, properties={}):
        if node_id and node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": label, "type": node_type, "properties": properties}

    def add_edge(source, target, relation):
        if source and target and source in nodes and target in nodes:
            edges.append({"source": source, "target": target, "relation": relation})

    cur.execute("SELECT * FROM sales_order_headers LIMIT 100")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"SO_{r['salesOrder']}"
        add_node(nid, f"SO {r['salesOrder']}", "SalesOrder", {
            "salesOrder": r["salesOrder"], "soldToParty": r["soldToParty"],
            "totalNetAmount": r["totalNetAmount"], "currency": r["transactionCurrency"],
            "deliveryStatus": r["overallDeliveryStatus"],
            "billingStatus": r["overallOrdReltdBillgStatus"],
            "creationDate": r["creationDate"]
        })

    cur.execute("SELECT * FROM sales_order_items")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"SOI_{r['salesOrder']}_{r['salesOrderItem']}"
        add_node(nid, f"Item {r['salesOrderItem']}", "SalesOrderItem", {
            "salesOrder": r["salesOrder"], "item": r["salesOrderItem"],
            "material": r["material"], "quantity": r["requestedQuantity"],
            "netAmount": r["netAmount"]
        })
        add_edge(f"SO_{r['salesOrder']}", nid, "HAS_ITEM")

    cur.execute("SELECT * FROM business_partners")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"CUST_{r['businessPartner']}"
        name = r.get("organizationBpName1") or r.get("businessPartnerFullName") or r["businessPartner"]
        add_node(nid, name[:30], "Customer", {
            "businessPartner": r["businessPartner"], "customer": r["customer"],
            "name": name, "industry": r["industry"]
        })

    cur.execute("SELECT salesOrder, soldToParty FROM sales_order_headers")
    for row in cur.fetchall():
        r = dict(row)
        add_edge(f"CUST_{r['soldToParty']}", f"SO_{r['salesOrder']}", "PLACED_ORDER")

    # Delivery nodes
    cur.execute("SELECT * FROM outbound_delivery_headers LIMIT 100")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"DEL_{r['deliveryDocument']}"
        add_node(nid, f"Del {r['deliveryDocument']}", "Delivery", {
            "deliveryDocument": r["deliveryDocument"],
            "goodsMovementDate": r["actualGoodsMovementDate"],
            "pickingStatus": r["overallPickingStatus"],
            "goodsMovementStatus": r["overallGoodsMovementStatus"]
        })

    # SO -> Delivery via delivery items (referenceSdDocument = salesOrder)
    cur.execute("SELECT DISTINCT deliveryDocument, referenceSdDocument FROM outbound_delivery_items")
    for row in cur.fetchall():
        r = dict(row)
        if r["referenceSdDocument"]:
            add_edge(f"SO_{r['referenceSdDocument']}", f"DEL_{r['deliveryDocument']}", "DELIVERED_VIA")

    # Billing documents
    cur.execute("SELECT * FROM billing_document_headers LIMIT 200")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"BD_{r['billingDocument']}"
        add_node(nid, f"Bill {r['billingDocument']}", "BillingDocument", {
            "billingDocument": r["billingDocument"], "type": r["billingDocumentType"],
            "totalNetAmount": r["totalNetAmount"], "currency": r["transactionCurrency"],
            "isCancelled": r["billingDocumentIsCancelled"], "date": r["billingDocumentDate"]
        })

    # Delivery -> Billing via billing items (referenceSdDocument = deliveryDocument)
    cur.execute("SELECT DISTINCT billingDocument, referenceSdDocument FROM billing_document_items")
    for row in cur.fetchall():
        r = dict(row)
        if r["referenceSdDocument"]:
            add_edge(f"DEL_{r['referenceSdDocument']}", f"BD_{r['billingDocument']}", "BILLED_AS")

    # Journal Entries
    cur.execute("SELECT DISTINCT accountingDocument, referenceDocument, fiscalYear, postingDate FROM journal_entries LIMIT 100")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"JE_{r['accountingDocument']}"
        add_node(nid, f"JE {r['accountingDocument']}", "JournalEntry", {
            "accountingDocument": r["accountingDocument"],
            "referenceDocument": r["referenceDocument"],
            "postingDate": r["postingDate"]
        })
        if r["referenceDocument"]:
            add_edge(f"BD_{r['referenceDocument']}", nid, "POSTED_TO")

    # Payments
    cur.execute("SELECT DISTINCT accountingDocument, invoiceReference, salesDocument, customer FROM payments LIMIT 100")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"PAY_{r['accountingDocument']}"
        add_node(nid, f"Pay {r['accountingDocument']}", "Payment", {
            "accountingDocument": r["accountingDocument"],
            "invoiceReference": r["invoiceReference"],
            "salesDocument": r["salesDocument"]
        })
        if r["invoiceReference"]:
            add_edge(f"BD_{r['invoiceReference']}", nid, "PAID_BY")
        if r["salesDocument"]:
            add_edge(f"SO_{r['salesDocument']}", nid, "PAYMENT_FOR")

    # Products
    cur.execute("""SELECT p.product, pd.productDescription
                   FROM products p
                   LEFT JOIN product_descriptions pd ON p.product=pd.product AND pd.language='EN'
                   LIMIT 69""")
    for row in cur.fetchall():
        r = dict(row)
        nid = f"PROD_{r['product']}"
        add_node(nid, (r["productDescription"] or r["product"])[:20], "Product", {
            "product": r["product"], "description": r["productDescription"] or r["product"]
        })

    # SOI -> Product
    cur.execute("SELECT DISTINCT salesOrder, salesOrderItem, material FROM sales_order_items")
    for row in cur.fetchall():
        r = dict(row)
        if r["material"]:
            add_edge(f"SOI_{r['salesOrder']}_{r['salesOrderItem']}", f"PROD_{r['material']}", "IS_MATERIAL")

    conn.close()
    return {"nodes": list(nodes.values()), "edges": edges}

# ── CORRECT SCHEMA FOR LLM ──
SCHEMA_DESCRIPTION = """
You are an expert SQL analyst for an SAP Order-to-Cash (O2C) system.
You have access to the following SQLite tables:

1. sales_order_headers - salesOrder(PK), salesOrderType, salesOrganization, distributionChannel,
   soldToParty(FK→business_partners.businessPartner), creationDate, totalNetAmount,
   overallDeliveryStatus, overallOrdReltdBillgStatus, transactionCurrency,
   requestedDeliveryDate, headerBillingBlockReason, deliveryBlockReason

2. sales_order_items - salesOrder(FK→sales_order_headers), salesOrderItem, material(FK→products),
   requestedQuantity, netAmount, materialGroup, productionPlant, storageLocation

3. sales_order_schedule_lines - salesOrder, salesOrderItem, scheduleLine,
   confirmedDeliveryDate, confdOrderQtyByMatlAvailCheck

4. outbound_delivery_headers - deliveryDocument(PK), actualGoodsMovementDate,
   overallGoodsMovementStatus, overallPickingStatus, shippingPoint

5. outbound_delivery_items - deliveryDocument(FK→outbound_delivery_headers), deliveryDocumentItem,
   actualDeliveryQuantity, plant(FK→plants), 
   referenceSdDocument(FK→sales_order_headers.salesOrder), referenceSdDocumentItem

6. billing_document_headers - billingDocument(PK), billingDocumentType, billingDocumentDate,
   billingDocumentIsCancelled('X'=cancelled), cancelledBillingDocument,
   totalNetAmount, transactionCurrency, companyCode, fiscalYear,
   accountingDocument(FK→journal_entries), soldToParty

7. billing_document_items - billingDocument(FK→billing_document_headers), billingDocumentItem,
   material(FK→products), billingQuantity, netAmount,
   referenceSdDocument(FK→outbound_delivery_headers.deliveryDocument),
   referenceSdDocumentItem

8. payments - accountingDocument, accountingDocumentItem, clearingDate,
   amountInTransactionCurrency, transactionCurrency, customer,
   invoiceReference(FK→billing_document_headers.billingDocument),
   salesDocument(FK→sales_order_headers.salesOrder), postingDate

9. journal_entries - accountingDocument, glAccount,
   referenceDocument(FK→billing_document_headers.billingDocument),
   amountInTransactionCurrency, transactionCurrency, postingDate,
   accountingDocumentType, customer

10. business_partners - businessPartner(PK), customer, businessPartnerFullName,
    organizationBpName1, industry, creationDate

11. business_partner_addresses - businessPartner, addressId, cityName, country, postalCode, region

12. customer_company_assignments - customer, companyCode, paymentTerms, reconciliationAccount

13. customer_sales_area_assignments - customer, salesOrganization, distributionChannel,
    division, currency, deliveryPriority, shippingCondition, supplyingPlant

14. plants - plant(PK), plantName, valuationArea, salesOrganization

15. products - product(PK), productType, grossWeight, netWeight, productGroup, baseUnit

16. product_descriptions - product, language, productDescription

CRITICAL RELATIONSHIP CHAIN (O2C Flow):
SalesOrder → [via outbound_delivery_items.referenceSdDocument] → DeliveryDocument
DeliveryDocument → [via billing_document_items.referenceSdDocument] → BillingDocument
BillingDocument → [via billing_document_headers.accountingDocument] → JournalEntry
BillingDocument → [via payments.invoiceReference] → Payment

KEY JOIN PATTERNS:
- SO to Delivery: outbound_delivery_items.referenceSdDocument = sales_order_headers.salesOrder
- Delivery to Billing: billing_document_items.referenceSdDocument = outbound_delivery_headers.deliveryDocument
- Billing to Journal: billing_document_headers.accountingDocument = journal_entries.referenceDocument
- Billing to Payment: payments.invoiceReference = billing_document_headers.billingDocument
- Products in Billing: billing_document_items.material = products.product
- Customer to SO: sales_order_headers.soldToParty = business_partners.businessPartner

BUSINESS RULES:
- overallDeliveryStatus: 'A'=Not delivered, 'B'=Partial, 'C'=Fully delivered
- overallOrdReltdBillgStatus: 'A'=Not billed, 'B'=Partial, 'C'=Fully billed
- billingDocumentIsCancelled: 'X' = cancelled
- Delivered but not billed = overallDeliveryStatus='C' AND overallOrdReltdBillgStatus != 'C'
- Billed without delivery = overallOrdReltdBillgStatus='C' AND overallDeliveryStatus='A'

EXAMPLE CORRECT QUERIES:
-- Products with most billing documents:
SELECT bdi.material, pd.productDescription, COUNT(DISTINCT bdi.billingDocument) as billing_count
FROM billing_document_items bdi
LEFT JOIN product_descriptions pd ON bdi.material = pd.product AND pd.language = 'EN'
GROUP BY bdi.material ORDER BY billing_count DESC LIMIT 10;

-- Trace billing document flow:
SELECT bdh.billingDocument, bdh.totalNetAmount, bdh.billingDocumentDate,
       odi.referenceSdDocument as salesOrder,
       bdi.referenceSdDocument as deliveryDocument,
       je.accountingDocument as journalEntry
FROM billing_document_headers bdh
JOIN billing_document_items bdi ON bdh.billingDocument = bdi.billingDocument
JOIN outbound_delivery_items odi ON odi.deliveryDocument = bdi.referenceSdDocument
LEFT JOIN journal_entries je ON je.referenceDocument = bdh.billingDocument
WHERE bdh.billingDocument = '91150187';

-- Delivered but not billed orders:
SELECT salesOrder, totalNetAmount, overallDeliveryStatus, overallOrdReltdBillgStatus
FROM sales_order_headers
WHERE overallDeliveryStatus = 'C' AND overallOrdReltdBillgStatus != 'C';
"""

DOMAIN_KEYWORDS = [
    "order", "billing", "invoice", "delivery", "payment", "customer", "product",
    "material", "plant", "journal", "sales", "revenue", "amount", "quantity",
    "sap", "o2c", "cash", "document", "status", "cancel", "flow", "item",
    "partner", "business", "account", "fiscal", "currency", "date", "track",
    "trace", "find", "show", "list", "count", "which", "what", "how many",
    "total", "sum", "average", "highest", "lowest", "top", "bottom",
    "incomplete", "broken", "missing", "pending", "address", "city", "region"
]

def is_relevant_query(query):
    return any(kw in query.lower() for kw in DOMAIN_KEYWORDS)

def call_llm(prompt):
    if not LLM_AVAILABLE:
        raise RuntimeError("Groq not configured. Add GROQ_API_KEY to backend/.env")
    response = _groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

def query_with_llm(user_message, history=[]):
    if not is_relevant_query(user_message):
        return {
            "answer": "⚠️ This system only answers questions about the SAP Order-to-Cash dataset. Please ask about sales orders, deliveries, billing documents, payments, customers, or products.",
            "sql": None, "data": None, "highlighted_nodes": []
        }

    if not LLM_AVAILABLE:
        return {
            "answer": "❌ LLM not configured. Please add GROQ_API_KEY to backend/.env and restart.",
            "sql": None, "data": None, "highlighted_nodes": []
        }

    sql_prompt = f"""{SCHEMA_DESCRIPTION}

The user asked: "{user_message}"

Generate a SQLite SQL query to answer this question using the CORRECT join patterns above.
Return ONLY a raw JSON object with no markdown:
{{"sql": "SELECT ...", "explanation": "...", "entity_ids": []}}
"""

    try:
        sql_text = call_llm(sql_prompt)
        sql_text = re.sub(r'```(?:json)?\s*', '', sql_text)
        sql_text = re.sub(r'```', '', sql_text).strip()

        sql_data = json.loads(sql_text)
        sql_query = sql_data.get("sql")
        entity_ids = sql_data.get("entity_ids", [])

        query_results = None
        if sql_query:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(sql_query)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                query_results = [dict(zip(cols, row)) for row in rows[:50]]
                conn.close()
            except Exception as ex:
                query_results = {"error": str(ex)}

        result_context = json.dumps(query_results, default=str)[:3000] if query_results else "No data returned"

        answer_prompt = f"""You are an SAP Order-to-Cash data analyst.
User asked: "{user_message}"
SQL executed: {sql_query or "None"}
Results: {result_context}
Give a clear, data-backed answer. Format numbers with commas. Be specific."""

        answer = call_llm(answer_prompt)

        highlighted = []
        for eid in entity_ids:
            eid = str(eid)
            for prefix in ["SO_", "BD_", "DEL_", "JE_", "PAY_", "CUST_", "PROD_"]:
                highlighted.append(f"{prefix}{eid}")

        return {"answer": answer, "sql": sql_query, "data": query_results, "highlighted_nodes": highlighted}

    except Exception as ex:
        try:
            answer = call_llm(f"{SCHEMA_DESCRIPTION}\nUser question: {user_message}\nAnswer based on the schema.")
            return {"answer": answer, "sql": None, "data": None, "highlighted_nodes": []}
        except Exception as ex2:
            return {"answer": f"❌ Error: {str(ex2)}", "sql": None, "data": None, "highlighted_nodes": []}

_graph_cache = None

@app.route("/api/graph", methods=["GET"])
def get_graph():
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = build_graph()
    return jsonify(_graph_cache)

@app.route("/api/graph/node/<node_id>", methods=["GET"])
def get_node_details(node_id):
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = build_graph()
    node = next((n for n in _graph_cache["nodes"] if n["id"] == node_id), None)
    if not node:
        return jsonify({"error": "Node not found"}), 404
    connected_edges = [e for e in _graph_cache["edges"] if e["source"] == node_id or e["target"] == node_id]
    connected_node_ids = set()
    for e in connected_edges:
        connected_node_ids.add(e["source"])
        connected_node_ids.add(e["target"])
    connected_nodes = [n for n in _graph_cache["nodes"] if n["id"] in connected_node_ids]
    return jsonify({"node": node, "edges": connected_edges, "connected_nodes": connected_nodes})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    stats = {}
    tables = ["sales_order_headers","billing_document_headers",
              "outbound_delivery_headers","payments","products","business_partners"]
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            stats[t] = cur.fetchone()[0]
        except Exception:
            stats[t] = 0
    try:
        cur.execute("""SELECT SUM(totalNetAmount), AVG(totalNetAmount), transactionCurrency
                       FROM sales_order_headers GROUP BY transactionCurrency
                       ORDER BY SUM(totalNetAmount) DESC LIMIT 1""")
        row = cur.fetchone()
        if row:
            stats["total_revenue"] = row[0]
            stats["avg_order_value"] = row[1]
            stats["currency"] = row[2]
    except Exception:
        pass
    conn.close()
    return jsonify(stats)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    history = data.get("history", [])
    if not message.strip():
        return jsonify({"error": "Empty message"}), 400
    result = query_with_llm(message, history)
    return jsonify(result)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": os.path.exists(DB_PATH), "llm": LLM_AVAILABLE})

@app.route("/api/sample-queries", methods=["GET"])
def sample_queries():
    return jsonify([
        "Which products are associated with the highest number of billing documents?",
        "Trace the full flow of billing document 90504204",
        "Find sales orders that have been delivered but not billed",
        "What is the total revenue by currency?",
        "List all cancelled billing documents",
        "Which customers have the most sales orders?",
        "Show sales orders with incomplete flows",
        "What is the average order value?"
    ])

if __name__ == "__main__":
    print("Initializing database...")
    populate_db()
    print("Starting server on port 5000...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))