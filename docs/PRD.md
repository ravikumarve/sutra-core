**Status**: Draft
**Author**: Product Manager (Alex)
**Last Updated**: 2026-04-25
**Version**: 1.0
**Stakeholders**: Backend Architect, Frontend Developer, AI Engineer, Security Engineer, DevOps Automator

---

## 1. Problem Statement

### The Core Problem
India's ₹50+ lakh crore informal trade economy runs on three things: trust, WhatsApp, and a register. Existing ERPs assume a literate, desktop-operating user, but the reality is busy shop owners who speak in Hinglish, send voice notes at 7am, and want a "kacha bill" on WhatsApp — not a login screen.

### Who Experiences This Problem
- **Primary Persona**: Shop owners in the Indian offline economy (textile merchants, hardware shops, kirana distributors, pharmacies)
- **Secondary Persona**: Customers who prefer WhatsApp communication over app downloads
- **Tertiary Persona**: Business owners managing multiple business entities

### Cost of Not Solving This Problem
- Lost revenue from manual order processing errors
- Inefficient inventory management leading to stockouts
- Poor credit (Udhaar) tracking causing financial losses
- Inability to scale operations without hiring more staff
- GST compliance risks from manual invoicing

### Evidence
- **Market Signal**: India's informal trade economy is ₹50+ lakh crore
- **User Behavior**: Shop owners are on WhatsApp 8 hours/day
- **Competitive Signal**: Existing ERPs require desktop literacy and app adoption
- **Support Signal**: High demand for WhatsApp-first business solutions

---

## 2. Goals & Success Metrics

| Goal | Metric | Current Baseline | Target | Measurement Window |
|------|--------|-----------------|--------|--------------------|
| Order Processing Accuracy | % orders processed correctly | Manual: ~85% | >99.5% | 90 days post-launch |
| Invoice Generation Success | % invoices generated successfully | Manual: ~90% | >99.9% | 90 days post-launch |
| Multi-Tenant Isolation | % tenant data properly isolated | N/A | 100% | 90 days post-launch |
| Financial Ledger Integrity | % financial transactions ACID compliant | Manual: ~95% | 100% | 90 days post-launch |
| WhatsApp Message Latency | Time for voice note transcription | N/A | <30s | 90 days post-launch |
| System Uptime | % system availability | N/A | >99.9% | 90 days post-launch |
| API Response Time | 95th percentile response time | N/A | <200ms | 90 days post-launch |
| Database Query Performance | Average query time | N/A | <100ms | 90 days post-launch |

---

## 3. Non-Goals

Explicitly state what this initiative will NOT address in this iteration:

- We are NOT building a mobile app for customers or owners (WhatsApp-only interaction)
- We are NOT supporting real-time video calls or live chat (async messaging only)
- We are NOT adding advanced analytics or AI-powered insights in v1 (basic analytics only)
- We are NOT supporting multiple languages beyond English, Hindi, and Hinglish in v1
- We are NOT adding payment gateway integration in v1 (UPI links planned for v1.1)
- We are NOT supporting image-based order parsing in v1 (planned for v1.1)
- We are NOT adding Telegram as a secondary inbound channel in v1 (planned for v1.2)

---

## 4. User Personas & Stories

### Primary Persona: Shop Owner (Rajesh)
**Context**: Textile merchant in Surat, runs business 12 hours/day, speaks Hinglish, sends 50+ WhatsApp messages daily, manages inventory manually in register

**Core User Stories**:

#### Epic 1: WhatsApp-First Order Processing

**Story 1.1**: As a shop owner, I want customers to place orders via WhatsApp voice notes, so that I can process orders without requiring them to learn a new app or type out details.

**Acceptance Criteria**:
- [ ] Given a customer sends a WhatsApp voice note, when SUTRA receives it, then the voice note is transcribed within 30 seconds
- [ ] Given a voice note contains order details, when transcription completes, then the intent is extracted with item, quantity, and credit flag
- [ ] Given the extracted intent has confidence >0.7, when processed, then the order is confirmed automatically
- [ ] Given the extracted intent has confidence <0.7, when processed, then the owner receives a WhatsApp message asking for confirmation
- [ ] Given an order is confirmed, when processing completes, then the customer receives a WhatsApp confirmation with order details
- [ ] Performance: Voice note transcription completes in under 30s for 95% of requests
- **Priority**: Must Have
- **Dependencies**: Whisper-Hinglish pipeline, Liaison agent, Strategist agent

**Story 1.2**: As a shop owner, I want customers to place orders via WhatsApp text messages, so that customers who prefer typing can still place orders efficiently.

**Acceptance Criteria**:
- [ ] Given a customer sends a WhatsApp text message, when SUTRA receives it, then the message is parsed for order intent
- [ ] Given the text message contains order details, when parsed, then the intent is extracted with item, quantity, and credit flag
- [ ] Given the extracted intent has confidence >0.7, when processed, then the order is confirmed automatically
- [ ] Given the extracted intent has confidence <0.7, when processed, then the owner receives a WhatsApp message asking for confirmation
- [ ] Given an order is confirmed, when processing completes, then the customer receives a WhatsApp confirmation with order details
- [ ] Performance: Text message processing completes in under 5s for 95% of requests
- **Priority**: Must Have
- **Dependencies**: Liaison agent, Strategist agent

**Story 1.3**: As a shop owner, I want to receive order confirmations on WhatsApp, so that I can track orders without checking a separate dashboard.

**Acceptance Criteria**:
- [ ] Given an order is confirmed, when processing completes, then the owner receives a WhatsApp message with order details
- [ ] Given an order is confirmed, when the owner message is sent, then it includes customer name, item, quantity, price, and total
- [ ] Given an order is placed on credit, when the owner message is sent, then it includes credit balance and limit
- [ ] Given an order is confirmed, when the owner message is sent, then it includes a link to the PDF invoice
- [ ] Performance: Owner confirmation message is sent within 10s of order confirmation
- **Priority**: Must Have
- **Dependencies**: Strategist agent, Auditor agent, WhatsApp integration

**Story 1.4**: As a customer, I want to receive a PDF invoice on WhatsApp after placing an order, so that I have a formal record of the transaction for my records.

**Acceptance Criteria**:
- [ ] Given an order is confirmed, when processing completes, then the customer receives a WhatsApp message with PDF invoice attached
- [ ] Given the PDF invoice is generated, when created, then it includes GST-compliant formatting with HSN codes
- [ ] Given the PDF invoice is generated, when created, then it includes business details, customer details, item details, quantities, prices, and GST breakdown
- [ ] Given the PDF invoice is generated, when created, then it includes a unique invoice number
- [ ] Given the PDF invoice is sent, when delivered, then it is sent in the same WhatsApp thread as the order
- [ ] Performance: PDF invoice is generated and sent within 15s of order confirmation
- **Priority**: Must Have
- **Dependencies**: Auditor agent, WeasyPrint, WhatsApp integration

#### Epic 2: Hinglish NLP Pipeline

**Story 2.1**: As a shop owner, I want SUTRA to understand Hinglish voice notes with regional dialects, so that customers can speak naturally without worrying about formal language.

**Acceptance Criteria**:
- [ ] Given a voice note contains Hinglish, when transcribed, then the transcription accurately captures mixed English-Hindi text
- [ ] Given a voice note contains regional colloquialisms, when transcribed, then the transcription preserves the meaning of informal terms
- [ ] Given a voice note contains business-specific vocabulary, when transcribed, then the transcription accurately captures terms like "GST", "Udhaar", unit names
- [ ] Given a voice note contains code-switching, when transcribed, then the transcription identifies segment-level language switching
- [ ] Given a voice note is transcribed, when processed, then the transcription accuracy is >85% for common order phrases
- [ ] Performance: Voice note transcription completes in under 30s for 95% of requests on CPU-only deployment
- **Priority**: Must Have
- **Dependencies**: Whisper (CPU-optimized), Hinglish post-processing pipeline

**Story 2.2**: As a shop owner, I want SUTRA to understand informal quantity expressions, so that customers can say "teen sau" or "ek bora" instead of formal numbers.

**Acceptance Criteria**:
- [ ] Given a voice note contains informal quantity like "teen sau", when normalized, then it is converted to "300"
- [ ] Given a voice note contains unit-based quantity like "ek bora", when normalized, then it is converted to the standard unit (e.g., "50kg")
- [ ] Given a voice note contains regional unit names, when normalized, then they are mapped to standard units (e.g., "peti" → "50kg")
- [ ] Given a voice note contains mixed formal and informal quantities, when normalized, then all quantities are converted to canonical form
- [ ] Given normalization is applied, when processed, then the normalized quantities are >95% accurate for common expressions
- [ ] Performance: Quantity normalization completes in under 2s for 95% of requests
- **Priority**: Must Have
- **Dependencies**: Whisper-Hinglish pipeline, dialect mapping system

**Story 2.3**: As a shop owner, I want SUTRA to understand industry-specific vocabulary, so that customers can use terms like "thaan", "nag", "bora" without confusion.

**Acceptance Criteria**:
- [ ] Given a voice note contains industry-specific vocabulary, when transcribed, then the vocabulary is accurately captured
- [ ] Given a voice note contains textile-specific terms like "thaan", when processed, then they are recognized as valid units
- [ ] Given a voice note contains hardware-specific terms like "nag", when processed, then they are recognized as valid units
- [ ] Given a voice note contains kirana-specific terms like "bora", when processed, then they are recognized as valid units
- [ ] Given a voice note contains pharma-specific terms like "strip", when processed, then they are recognized as valid units
- [ ] Given vocabulary recognition is applied, when processed, then the recognition accuracy is >90% for industry-specific terms
- [ ] Performance: Vocabulary recognition completes in under 1s for 95% of requests
- **Priority**: Must Have
- **Dependencies**: Whisper-Hinglish pipeline, dialect mapping system, industry presets

#### Epic 3: Multi-Tenant Business Management

**Story 3.1**: As a business owner, I want to manage multiple business entities with separate WhatsApp numbers, so that I can run different businesses without confusion.

**Acceptance Criteria**:
- [ ] Given a new tenant is provisioned, when created, then it has an isolated PostgreSQL schema named `tenant_{id}`
- [ ] Given a new tenant is provisioned, when created, then it has a dedicated Redis namespace `sutra:{tenant_id}:*`
- [ ] Given a new tenant is provisioned, when created, then it has a dedicated WhatsApp phone number via Meta Business API
- [ ] Given a new tenant is provisioned, when created, then it has optional tenant-specific Whisper vocabulary injection
- [ ] Given multiple tenants exist, when messages are received, then they are routed to the correct tenant based on WhatsApp phone number
- [ ] Given multiple tenants exist, when data is accessed, then tenant isolation is 100% (no data leakage between tenants)
- **Priority**: Must Have
- **Dependencies**: Multi-tenancy architecture, PostgreSQL schema isolation, Redis namespace isolation

**Story 3.2**: As a business owner, I want to configure industry-specific settings for each tenant, so that each business can use its own vocabulary and units.

**Acceptance Criteria**:
- [ ] Given a tenant is configured for textiles, when set up, then it uses textile vocabulary (Thaan, meter, peti, lot)
- [ ] Given a tenant is configured for hardware, when set up, then it uses hardware vocabulary (Nag, patti, pipe, fitting)
- [ ] Given a tenant is configured for kirana, when set up, then it uses kirana vocabulary (Bora, peethi, dozen)
- [ ] Given a tenant is configured for pharma, when set up, then it uses pharma vocabulary (Strip, box, vial)
- [ ] Given a tenant is configured, when processing orders, then the correct industry preset is applied
- [ ] Given industry presets are applied, when used, then the preset accuracy is >95% for industry-specific terms
- **Priority**: Must Have
- **Dependencies**: Industry presets system, tenant configuration management

**Story 3.3**: As a business owner, I want to provision new tenants via command line, so that I can quickly set up new business entities without manual configuration.

**Acceptance Criteria**:
- [ ] Given a provisioning command is run, when executed, then it creates a new tenant with the specified name
- [ ] Given a provisioning command is run, when executed, then it configures the specified WhatsApp phone number
- [ ] Given a provisioning command is run, when executed, then it sets the specified GST state code
- [ ] Given a provisioning command is run, when executed, then it applies the specified industry preset
- [ ] Given provisioning is complete, when finished, then the tenant is ready to receive WhatsApp messages
- [ ] Performance: Tenant provisioning completes in under 60s for 95% of requests
- **Priority**: Should Have
- **Dependencies**: Tenant provisioning system, industry presets

#### Epic 4: Financial Integrity & Ledger

**Story 4.1**: As a shop owner, I want inventory to be deducted automatically when orders are confirmed, so that I never oversell items.

**Acceptance Criteria**:
- [ ] Given an order is confirmed, when processed, then the inventory is deducted atomically with the order creation
- [ ] Given an order is confirmed, when processed, then the inventory deduction is ACID compliant (all or nothing)
- [ ] Given an order is confirmed, when processed, then the inventory is updated in the same transaction as the order
- [ ] Given an order confirmation fails, when rolled back, then the inventory is not deducted
- [ ] Given inventory is deducted, when updated, then the new inventory level is reflected immediately
- [ ] Given inventory deduction is applied, when processed, then the deduction accuracy is 100% (no overselling)
- **Priority**: Must Have
- **Dependencies**: PostgreSQL ACID compliance, inventory management system, Strategist agent

**Story 4.2**: As a shop owner, I want credit (Udhaar) entries to be tracked with ACID compliance, so that I never lose track of who owes me money.

**Acceptance Criteria**:
- [ ] Given an order is placed on credit, when processed, then the credit entry is created atomically with the order
- [ ] Given an order is placed on credit, when processed, then the credit entry is ACID compliant (all or nothing)
- [ ] Given an order is placed on credit, when processed, then the credit limit is checked before order approval
- [ ] Given an order is placed on credit, when processed, then the credit balance is updated in the same transaction as the order
- [ ] Given a credit payment is received, when processed, then the credit balance is updated atomically
- [ ] Given credit tracking is applied, when processed, then the tracking accuracy is 100% (no lost credits)
- **Priority**: Must Have
- **Dependencies**: PostgreSQL ACID compliance, credit ledger system, Strategist agent

**Story 4.3**: As a shop owner, I want all financial transactions to be recorded in an immutable ledger, so that I have a complete audit trail for compliance and reconciliation.

**Acceptance Criteria**:
- [ ] Given any financial transaction occurs, when processed, then it is recorded in the immutable ledger
- [ ] Given a ledger entry is created, when written, then it cannot be modified or deleted
- [ ] Given a ledger entry is created, when written, then it includes a timestamp, transaction type, and all relevant details
- [ ] Given a ledger entry is created, when written, then it is linked to the tenant and customer
- [ ] Given ledger entries are queried, when accessed, then they are returned in chronological order
- [ ] Given the ledger is used, when audited, then the ledger integrity is 100% (no missing or modified entries)
- **Priority**: Must Have
- **Dependencies**: Immutable ledger system, Auditor agent

**Story 4.4**: As a shop owner, I want GST-compliant invoices to be generated automatically, so that I never make GST calculation errors.

**Acceptance Criteria**:
- [ ] Given an order is confirmed, when processed, then a GST-compliant invoice is generated
- [ ] Given an invoice is generated, when created, then it includes the correct GST calculation based on HSN codes
- [ ] Given an invoice is generated, when created, then it includes the GST state code and customer GSTIN if available
- [ ] Given an invoice is generated, when created, then it includes a breakdown of CGST, SGST, and IGST as applicable
- [ ] Given an invoice is generated, when created, then it includes a unique invoice number
- [ ] Given GST calculation is applied, when processed, then the calculation accuracy is 100% (no GST errors)
- **Priority**: Must Have
- **Dependencies**: GST calculation engine, WeasyPrint, Auditor agent

#### Epic 5: Owner Analytics Dashboard

**Story 5.1**: As a shop owner, I want to view month-end sales analytics, so that I can understand my business performance without manual calculations.

**Acceptance Criteria**:
- [ ] Given the owner accesses the dashboard, when viewed, then they see total sales for the current month
- [ ] Given the owner accesses the dashboard, when viewed, then they see sales breakdown by product category
- [ ] Given the owner accesses the dashboard, when viewed, then they see sales trends over time
- [ ] Given the owner accesses the dashboard, when viewed, then they see top-selling products
- [ ] Given the dashboard is accessed, when loaded, then it loads in under 3s for 95% of requests
- [ ] Given the dashboard is used, when viewed, then the data accuracy is >99% compared to ledger
- **Priority**: Should Have
- **Dependencies**: Next.js 14, shadcn/ui, analytics queries

**Story 5.2**: As a shop owner, I want to view inventory analytics, so that I can identify restocking needs before stockouts occur.

**Acceptance Criteria**:
- [ ] Given the owner accesses the dashboard, when viewed, then they see current inventory levels for all products
- [ ] Given the owner accesses the dashboard, when viewed, then they see products below restock threshold
- [ ] Given the owner accesses the dashboard, when viewed, then they see inventory trends over time
- [ ] Given the owner accesses the dashboard, when viewed, then they see last reorder dates and suppliers
- [ ] Given the dashboard is accessed, when loaded, then it loads in under 3s for 95% of requests
- [ ] Given the dashboard is used, when viewed, then the data accuracy is >99% compared to inventory system
- **Priority**: Should Have
- **Dependencies**: Next.js 14, shadcn/ui, inventory queries

**Story 5.3**: As a shop owner, I want to view credit aging reports, so that I can follow up on overdue payments.

**Acceptance Criteria**:
- [ ] Given the owner accesses the dashboard, when viewed, then they see total outstanding credit by customer
- [ ] Given the owner accesses the dashboard, when viewed, then they see credit aging buckets (0-30 days, 31-60 days, 61-90 days, 90+ days)
- [ ] Given the owner accesses the dashboard, when viewed, then they see customers with credit overdue by configured threshold
- [ ] Given the owner accesses the dashboard, when viewed, then they can click on a customer to see payment history
- [ ] Given the dashboard is accessed, when loaded, then it loads in under 3s for 95% of requests
- [ ] Given the dashboard is used, when viewed, then the data accuracy is >99% compared to credit ledger
- **Priority**: Should Have
- **Dependencies**: Next.js 14, shadcn/ui, credit queries

**Story 5.4**: As a business owner, I want to manage multiple tenants from a single dashboard, so that I can oversee all my businesses in one place.

**Acceptance Criteria**:
- [ ] Given the owner accesses the dashboard, when viewed, then they see a list of all tenants they manage
- [ ] Given the owner selects a tenant, when clicked, then they see analytics for that specific tenant
- [ ] Given the owner accesses the dashboard, when viewed, then they can switch between tenants without reloading
- [ ] Given the owner accesses the dashboard, when viewed, then they see aggregate analytics across all tenants
- [ ] Given the dashboard is accessed, when loaded, then it loads in under 3s for 95% of requests
- [ ] Given the dashboard is used, when viewed, then the data accuracy is >99% compared to individual tenant systems
- **Priority**: Could Have
- **Dependencies**: Next.js 14, shadcn/ui, multi-tenant queries

---

## 5. Solution Overview

SUTRA Core is a headless, multi-agent ERP system that bridges unstructured WhatsApp messaging with strict backend business operations. The system operates as an asynchronous Multi-Modal Agent Mesh on an event-driven loop, where every inbound message triggers a pipeline without waiting for human intervention.

The core architecture consists of three specialized agents:

1. **Liaison Agent**: Decodes intent, sentiment, and structured parameters (Item, Qty, Price, Credit Flag) from raw audio/text using Whisper-Hinglish, SentimentAnalyzer, and LanguageDetector
2. **Strategist Agent**: Validates decoded intent against database state, approves orders, triggers restock alerts, and applies dynamic pricing rules using InventorySync, DynamicPricingEngine, and CreditScorer
3. **Auditor Agent**: Records all state changes to the immutable ledger, generates GST-compliant invoices and credit summaries using PDF-Generator, TrustLedger, and GSTValidator

Agents communicate via structured `AgentMessage` objects passed through Redis pub/sub channels, ensuring each agent can be independently scaled, restarted, or replaced.

**Key Design Decisions**:
- **Headless (WhatsApp-only)**: We chose WhatsApp-only interaction over mobile app because shop owners are on WhatsApp 8 hours/day. Meeting them there removes the entire adoption problem. Trade-off: Limited to WhatsApp's feature set and API constraints.
- **PostgreSQL over document store**: We chose PostgreSQL for financial ledger data because it requires ACID compliance. Udhaar (credit) entries must be atomic with inventory deductions. Trade-off: More complex schema design vs. flexible document structure.
- **Redis Streams over Kafka**: We chose Redis Streams because the target deployment is a single ₹800/month VPS. Kafka is overkill. Trade-off: Limited scalability vs. resource efficiency.
- **CPU-only Whisper**: We chose CPU-only Whisper because WhatsApp voice notes are async by nature. A 30-second transcription latency is acceptable. Trade-off: Slower transcription vs. GPU requirement elimination.

---

## 6. Agent Responsibility Specifications

### Liaison Agent

**Input Formats and Processing Requirements**:
- **WhatsApp Voice Notes**: Audio files in OGG/AMR format, maximum 5 minutes duration
- **WhatsApp Text Messages**: Plain text messages, maximum 4096 characters
- **WhatsApp Images**: Optional future support for product photo parsing (v1.1)

**Output Structure and Confidence Scoring**:
```python
class LiaisonOutput(BaseModel):
    intent: str                    # "ORDER" | "INQUIRY" | "CANCELLATION" | "PAYMENT" | "UNKNOWN"
    item: Optional[str]            # Product name or SKU
    quantity: Optional[float]      # Normalized quantity in standard units
    unit: Optional[str]            # Standard unit (e.g., "meter", "kg", "pieces")
    price: Optional[float]         # Price per unit
    credit_flag: Optional[bool]    # True if customer requests credit
    customer_id: Optional[str]     # Customer phone number or ID
    confidence: float              # 0.0–1.0 confidence score
    raw_transcript: str            # Original transcription for reference
    normalized_transcript: str    # Normalized transcription with quantities
    sentiment: Optional[str]       # "positive" | "neutral" | "negative"
    requires_confirmation: bool    # True if confidence < 0.7
```

**Integration Points with Whisper-Hinglish Pipeline**:
- **Language Detection**: Receives segment-level language switching detection from Whisper-Hinglish
- **Domain Vocabulary Injection**: Receives force-decoded product names, units, and business terms via Whisper's `logit_bias`
- **Normalization**: Receives converted informal quantities/prices to canonical form

**Error Handling and Fallback Strategies**:
- **Low Confidence (<0.7)**: Sets `requires_confirmation=True` and sends WhatsApp message to owner for manual confirmation
- **Unknown Intent**: Sets `intent="UNKNOWN"` and sends WhatsApp message to owner for clarification
- **Transcription Failure**: Sends WhatsApp message to owner requesting text input instead
- **Network Timeout**: Retries up to 3 times with exponential backoff, then escalates to owner notification

### Strategist Agent

**Business Logic Validation Rules**:
- **Inventory Check**: Validates that requested quantity is available in stock
- **Credit Check**: Validates that customer credit limit is not exceeded
- **Price Validation**: Validates that price is within acceptable range (±20% of base price)
- **Customer Validation**: Validates that customer exists in the system or creates new customer record
- **GST Validation**: Validates that HSN codes are valid for the product category

**Inventory Checking and Credit Scoring**:
- **Inventory Check**: Queries PostgreSQL for current inventory levels, returns available quantity
- **Credit Scoring**: Calculates customer credit score based on payment history, current balance, and credit limit
- **Dynamic Pricing**: Applies dynamic pricing rules based on customer tier, order volume, and market conditions
- **Approval Workflow**: Approves orders automatically if all checks pass, otherwise requires owner confirmation

**Alert Generation Triggers**:
- **Restock Alert**: Triggers when inventory falls below `RESTOCK_THRESHOLD_UNITS` (default: 10 units)
- **Credit Aging Alert**: Triggers when customer credit is unpaid for >`UDHAAR_ALERT_DAYS` (default: 30 days)
- **Low Stock Alert**: Triggers when inventory is below 20% of average monthly sales
- **High Credit Alert**: Triggers when customer credit balance exceeds 80% of credit limit

### Auditor Agent

**Ledger Writing and Immutability Requirements**:
- **Append-Only Ledger**: All financial transactions are written to an append-only ledger that cannot be modified or deleted
- **Transaction Atomicity**: Each ledger entry is written in the same transaction as the financial operation
- **Timestamp Recording**: Each ledger entry includes a precise timestamp for audit trail
- **Tenant Isolation**: Each ledger entry is scoped to a specific tenant for multi-tenancy

**PDF Generation Specifications**:
- **GST-Compliant Templates**: Uses WeasyPrint to generate GST-compliant invoice templates
- **Invoice Numbering**: Generates unique invoice numbers per tenant with sequential numbering
- **Template Customization**: Supports tenant-specific invoice templates with logos and branding
- **PDF Delivery**: Delivers PDF invoices via WhatsApp in the same thread as the order

**GST Validation Rules**:
- **HSN Code Validation**: Validates that HSN codes are valid for the product category
- **GST Calculation**: Calculates CGST, SGST, and IGST based on GST state code and product category
- **Customer GSTIN**: Validates customer GSTIN format if provided
- **Invoice Formatting**: Ensures invoice format complies with GST regulations

**Compliance and Audit Trail Requirements**:
- **Audit Logging**: Logs all financial operations with timestamp, user, and operation details
- **Compliance Reporting**: Generates compliance reports for GST filing and audit purposes
- **Data Retention**: Retains all financial data for minimum 7 years as per regulatory requirements
- **Access Control**: Ensures that only authorized users can access financial data

### Agent Communication Protocol

**Redis Streams Channel Naming Conventions**:
- **Liaison Output Channel**: `sutra:{tenant_id}:liaison:output`
- **Strategist Input Channel**: `sutra:{tenant_id}:strategist:input`
- **Strategist Output Channel**: `sutra:{tenant_id}:strategist:output`
- **Auditor Input Channel**: `sutra:{tenant_id}:auditor:input`
- **Auditor Output Channel**: `sutra:{tenant_id}:auditor:output`

**AgentMessage Schema Validation Rules**:
```python
class AgentMessage(BaseModel):
    message_id: str           # UUID, idempotency key
    tenant_id: str            # Isolated per business entity
    source_agent: str         # "liaison" | "strategist" | "auditor"
    payload: dict             # Agent-specific structured output
    confidence: float         # 0.0–1.0 — Liaison populates; others inherit
    requires_confirmation: bool  # True → send WhatsApp confirmation before executing
    timestamp: datetime

    class Config:
        # Validate that source_agent is one of the allowed values
        @validator('source_agent')
        def validate_source_agent(cls, v):
            if v not in ['liaison', 'strategist', 'auditor']:
                raise ValueError('source_agent must be one of: liaison, strategist, auditor')
            return v

        # Validate that confidence is between 0.0 and 1.0
        @validator('confidence')
        def validate_confidence(cls, v):
            if not 0.0 <= v <= 1.0:
                raise ValueError('confidence must be between 0.0 and 1.0')
            return v
```

**Message Ordering and Delivery Guarantees**:
- **FIFO Ordering**: Redis Streams guarantee FIFO ordering within each stream
- **Message Acknowledgment**: Agents acknowledge message processing after successful completion
- **Retry Logic**: Failed messages are retried up to 3 times with exponential backoff
- **Dead Letter Queue**: Messages that fail after 3 retries are moved to a dead letter queue for manual inspection

**Error Handling and Retry Logic**:
- **Transient Errors**: Retry with exponential backoff (1s, 2s, 4s)
- **Permanent Errors**: Move to dead letter queue and notify owner
- **Timeout Errors**: Retry up to 3 times, then escalate
- **Validation Errors**: Return error message to calling agent with specific validation failure details

---

## 7. Technical Requirements

### Multi-Tenancy Architecture

**PostgreSQL Schema Isolation Requirements**:
- **Schema Naming**: Each tenant gets a dedicated schema named `tenant_{id}`
- **Table Isolation**: All tenant-specific tables are created within the tenant schema
- **Schema Permissions**: Each tenant schema has restricted permissions accessible only to that tenant
- **Cross-Tenant Queries**: All queries include tenant_id filter to prevent cross-tenant data access

**Redis Namespace Isolation Strategy**:
- **Namespace Naming**: Each tenant gets a dedicated Redis namespace `sutra:{tenant_id}:*`
- **Key Isolation**: All Redis keys are prefixed with the tenant namespace
- **Channel Isolation**: All Redis Streams channels are scoped to the tenant namespace
- **Access Control**: Redis ACLs restrict access to tenant-specific namespaces

**WhatsApp Phone Number Routing Logic**:
- **Phone Number Mapping**: Each tenant is associated with a unique WhatsApp phone number via Meta Business API
- **Message Routing**: Incoming messages are routed to the correct tenant based on the phone number
- **Outbound Messages**: Outbound messages are sent from the tenant's associated phone number
- **Number Management**: Phone numbers can be added, removed, or reassigned to tenants

**Tenant Configuration Management**:
- **Configuration Storage**: Tenant-specific configurations are stored in PostgreSQL within the tenant schema
- **Configuration Schema**: Configuration includes industry preset, GST state code, alert thresholds, and custom vocabulary
- **Configuration Updates**: Configuration can be updated via CLI or API
- **Configuration Validation**: All configuration changes are validated before being applied

### Hinglish NLP Pipeline

**Whisper CPU Optimization Requirements**:
- **Model Selection**: Use Whisper `medium` or `large-v3` model optimized for CPU inference
- **Quantization**: Apply model quantization to reduce memory footprint and improve CPU performance
- **Batch Processing**: Process multiple voice notes in batches when possible to improve throughput
- **Caching**: Cache transcriptions for repeated voice notes to reduce processing time

**Language Detection Accuracy Targets**:
- **Segment-Level Detection**: Detect language switching at the segment level (sentence/phrase)
- **Accuracy Target**: >85% accuracy for common Hinglish phrases
- **Supported Languages**: English, Hindi, and Hinglish code-switching
- **Confidence Scoring**: Provide confidence scores for language detection

**Domain Vocabulary Injection Strategy**:
- **Logit Bias**: Use Whisper's `logit_bias` parameter to force-decode known product names, units, and business terms
- **Vocabulary Lists**: Maintain vocabulary lists per industry preset (textiles, hardware, kirana, pharma)
- **Dynamic Injection**: Inject vocabulary dynamically based on tenant configuration
- **Fallback Handling**: Fall back to standard transcription if vocabulary injection fails

**Quantity Normalization Rules and Examples**:
- **Number Words to Digits**: Convert number words to digits (e.g., "teen sau" → "300", "ek" → "1")
- **Unit-Based Quantities**: Convert unit-based quantities to standard units (e.g., "ek bora" → "50kg", "dus peti" → "500kg")
- **Regional Units**: Map regional units to standard units (e.g., "peti" → "50kg", "thaan" → "meter")
- **Mixed Expressions**: Handle mixed formal and informal expressions (e.g., "5 thaan" → "5 meters")

### Financial Integrity

**ACID Compliance Requirements for All Money Operations**:
- **Atomicity**: All financial operations are atomic — either all changes are committed or none are
- **Consistency**: All financial operations maintain database consistency and integrity constraints
- **Isolation**: All financial operations are isolated from concurrent operations
- **Durability**: All committed financial operations are durable and survive system failures

**Test Coverage Requirements (90% for Financial Modules)**:
- **Ledger Module**: 90%+ test coverage for all ledger operations
- **Inventory Module**: 90%+ test coverage for all inventory operations
- **Credit Module**: 90%+ test coverage for all credit operations
- **GST Module**: 90%+ test coverage for all GST calculations
- **Order Module**: 90%+ test coverage for all order processing

**Ledger Immutability Guarantees**:
- **Append-Only**: Ledger entries can only be appended, never modified or deleted
- **Timestamp Integrity**: Ledger entry timestamps cannot be modified
- **Transaction Linking**: Each ledger entry is linked to the original transaction
- **Audit Trail**: Complete audit trail is maintained for all financial operations

**GST Calculation Accuracy Requirements**:
- **HSN Code Validation**: Validate HSN codes against official GST HSN code database
- **Tax Rate Calculation**: Calculate correct tax rates based on HSN codes and GST state code
- **Invoice Formatting**: Ensure invoice format complies with GST regulations
- **Reporting Accuracy**: Generate accurate GST reports for filing purposes

### Performance Requirements

**API Response Time Targets (<200ms 95th Percentile)**:
- **Webhook Processing**: <200ms for 95th percentile of webhook requests
- **Order Processing**: <200ms for 95th percentile of order processing requests
- **Inventory Queries**: <200ms for 95th percentile of inventory query requests
- **Credit Queries**: <200ms for 95th percentile of credit query requests

**Database Query Performance Targets (<100ms Average)**:
- **Inventory Queries**: <100ms average for inventory queries
- **Order Queries**: <100ms average for order queries
- **Credit Queries**: <100ms average for credit queries
- **Ledger Queries**: <100ms average for ledger queries

**WhatsApp Message Latency Targets (<30s for Voice Notes)**:
- **Voice Note Transcription**: <30s for 95th percentile of voice note transcriptions
- **Text Message Processing**: <5s for 95th percentile of text message processing
- **Order Confirmation**: <10s for 95th percentile of order confirmations
- **PDF Invoice Generation**: <15s for 95th percentile of PDF invoice generation

**System Uptime Targets (>99.9% Availability)**:
- **Overall System Uptime**: >99.9% availability (maximum 8.76 hours downtime per year)
- **Webhook Availability**: >99.9% availability for WhatsApp webhook endpoint
- **Database Availability**: >99.9% availability for PostgreSQL database
- **Redis Availability**: >99.9% availability for Redis message queue

### Security Requirements

**Tenant Data Isolation Guarantees**:
- **Schema-Level Isolation**: Each tenant has isolated PostgreSQL schemas with no cross-tenant access
- **Redis Namespace Isolation**: Each tenant has isolated Redis namespaces with ACL-based access control
- **WhatsApp Number Isolation**: Each tenant has dedicated WhatsApp phone numbers with no message crossover
- **Data Encryption**: All sensitive data is encrypted at rest and in transit

**WhatsApp Webhook Signature Verification**:
- **Signature Validation**: All incoming webhook requests are verified using Meta's signature verification
- **Timestamp Validation**: Webhook timestamps are validated to prevent replay attacks
- **Token Verification**: Webhook verify token is validated during initial setup
- **IP Whitelisting**: Optional IP whitelisting for webhook endpoints

**GDPR Compliance for Customer Data**:
- **Data Minimization**: Only collect necessary customer data for business operations
- **Right to Access**: Customers can request access to their data
- **Right to Deletion**: Customers can request deletion of their data (with legal retention requirements)
- **Data Portability**: Customers can export their data in machine-readable format
- **Consent Management**: Explicit consent for data processing and marketing communications

**Audit Logging for All Financial Operations**:
- **Transaction Logging**: All financial transactions are logged with timestamp, user, and operation details
- **Access Logging**: All access to financial data is logged with user, timestamp, and operation
- **Change Logging**: All changes to financial data are logged with before/after values
- **Alert Logging**: All financial alerts are logged with trigger conditions and recipients
- **Retention**: Audit logs are retained for minimum 7 years as per regulatory requirements

---

## 8. Industry Presets Specifications

### Textiles Preset

**Vocabulary Requirements (Thaan, meter, peti, lot)**:
- **Thaan**: Traditional textile unit, approximately 1 meter of fabric
- **Meter**: Standard metric unit for fabric measurement
- **Peti**: Large bundle, approximately 50kg of fabric
- **Lot**: Batch of fabric pieces, variable quantity

**Unit Conversion Rules**:
- **Thaan to Meter**: 1 thaan = 1 meter (standard conversion)
- **Peti to Kg**: 1 peti = 50kg (standard conversion)
- **Lot to Pieces**: Variable based on product specification
- **Mixed Units**: Support for mixed unit expressions (e.g., "5 thaan 2 meter")

**HSN Code Categories (50–63)**:
- **HSN 50–55**: Textile fibers and yarns
- **HSN 56–60**: Textile fabrics and woven goods
- **HSN 61–63**: Apparel and clothing accessories

**Sample Inventory Structure**:
```json
{
  "product_id": "TEX001",
  "name": "Red Georgette Fabric",
  "category": "textiles",
  "hsn_code": "5807",
  "default_unit": "thaan",
  "price_per_unit": 1100,
  "stock_quantity": 12,
  "stock_unit": "thaan",
  "aliases": ["georgette", "red fabric", "georgette red"]
}
```

### Hardware Preset

**Vocabulary Requirements (Nag, patti, pipe, fitting)**:
- **Nag**: Snake/serpent shape, used for curved pipes
- **Patti**: Strip/flat piece of metal
- **Pipe**: Cylindrical hollow tube
- **Fitting**: Connector or adapter for pipes

**Unit Conversion Rules**:
- **Nag to Pieces**: 1 nag = 1 piece (standard conversion)
- **Patti to Kg**: 1 patti = variable weight based on dimensions
- **Pipe to Meters**: 1 pipe = variable length based on specification
- **Fitting to Pieces**: 1 fitting = 1 piece (standard conversion)

**HSN Code Categories (73–84)**:
- **HSN 73–76**: Iron and steel products
- **HSN 77–79**: Aluminum and other base metals
- **HSN 80–84**: Tools, hardware, and miscellaneous metal products

**Sample Inventory Structure**:
```json
{
  "product_id": "HRD001",
  "name": "1/2 inch PVC Pipe",
  "category": "hardware",
  "hsn_code": "3917",
  "default_unit": "meter",
  "price_per_unit": 45,
  "stock_quantity": 100,
  "stock_unit": "meter",
  "aliases": ["pvc pipe", "half inch pipe", "water pipe"]
}
```

### Kirana Preset

**Vocabulary Requirements (Bora, peethi, dozen)**:
- **Bora**: Large sack, approximately 50kg
- **Peethi**: Small sack, approximately 25kg
- **Dozen**: 12 pieces
- **Pieces**: Individual items

**Unit Conversion Rules**:
- **Bora to Kg**: 1 bora = 50kg (standard conversion)
- **Peethi to Kg**: 1 peethi = 25kg (standard conversion)
- **Dozen to Pieces**: 1 dozen = 12 pieces (standard conversion)
- **Pieces to Kg**: Variable based on product weight

**HSN Code Categories (07–21)**:
- **HSN 07–10**: Edible vegetables, fruits, nuts
- **HSN 11–15**: Food products, beverages, spirits
- **HSN 16–21**: Miscellaneous food products and preparations

**Sample Inventory Structure**:
```json
{
  "product_id": "KRN001",
  "name": "Basmati Rice",
  "category": "kirana",
  "hsn_code": "1006",
  "default_unit": "kg",
  "price_per_unit": 120,
  "stock_quantity": 500,
  "stock_unit": "kg",
  "aliases": ["rice", "basmati", "chawal"]
}
```

### Pharma Preset

**Vocabulary Requirements (Strip, box, vial)**:
- **Strip**: Blister pack with multiple tablets
- **Box**: Carton containing multiple strips or bottles
- **Vial**: Small glass container for liquid medicine
- **Pieces**: Individual tablets or capsules

**Unit Conversion Rules**:
- **Strip to Pieces**: 1 strip = variable pieces (typically 10-15)
- **Box to Strips**: 1 box = variable strips (typically 5-10)
- **Vial to ml**: 1 vial = variable ml based on product specification
- **Pieces to Strips**: Variable based on strip size

**HSN Code Categories (30)**:
- **HSN 30**: Pharmaceutical products

**Sample Inventory Structure**:
```json
{
  "product_id": "PHM001",
  "name": "Paracetamol 500mg",
  "category": "pharma",
  "hsn_code": "3004",
  "default_unit": "strip",
  "price_per_unit": 25,
  "stock_quantity": 100,
  "stock_unit": "strip",
  "aliases": ["paracetamol", "fever medicine", "pain relief"]
}
```

---

## 9. Non-Functional Requirements

### CPU-Only Deployment Constraints (₹800/month VPS Target)

**Hardware Requirements**:
- **Minimum CPU**: 2 vCPU
- **Minimum RAM**: 2GB RAM
- **Minimum Storage**: 20GB SSD
- **Operating System**: Linux (Ubuntu 20.04+ or equivalent)

**Whisper CPU Optimization**:
- **Model Selection**: Use Whisper `medium` model (balance of accuracy and performance)
- **Quantization**: Apply 8-bit quantization to reduce memory footprint
- **Batch Processing**: Process up to 5 voice notes in parallel
- **Caching**: Cache transcriptions for 24 hours to reduce processing time

**Resource Management**:
- **Memory Limits**: Whisper process limited to 1GB RAM
- **CPU Limits**: Whisper process limited to 1 vCPU
- **Timeout Limits**: Voice note transcription timeout of 60 seconds
- **Queue Management**: Maximum 10 concurrent voice note transcriptions

### Scalability Requirements for Multi-Tenant Growth

**Horizontal Scaling**:
- **Agent Scaling**: Each agent can be scaled independently based on load
- **Database Scaling**: PostgreSQL read replicas for query scaling
- **Redis Scaling**: Redis Cluster for multi-tenant message queue scaling
- **Webhook Scaling**: Multiple webhook instances behind load balancer

**Vertical Scaling**:
- **CPU Scaling**: Support for 2-8 vCPU configurations
- **RAM Scaling**: Support for 2-16GB RAM configurations
- **Storage Scaling**: Support for 20-200GB SSD configurations
- **Network Scaling**: Support for increased bandwidth with tenant growth

**Tenant Capacity**:
- **Minimum Tenants**: Support for 1-10 tenants on base configuration
- **Maximum Tenants**: Support for 100+ tenants on scaled configuration
- **Tenant Isolation**: Maintain 100% tenant isolation at all scales
- **Performance**: Maintain performance targets at maximum tenant capacity

### Monitoring and Alerting Requirements

**System Monitoring**:
- **CPU Usage**: Monitor CPU usage per agent and overall system
- **Memory Usage**: Monitor memory usage per agent and overall system
- **Disk Usage**: Monitor disk usage and alert at 80% capacity
- **Network Usage**: Monitor network bandwidth and alert at 90% capacity

**Application Monitoring**:
- **Webhook Latency**: Monitor webhook processing latency
- **Agent Performance**: Monitor agent processing time and throughput
- **Queue Depth**: Monitor Redis queue depth and alert on backlog
- **Error Rates**: Monitor error rates and alert on threshold breaches

**Business Monitoring**:
- **Order Volume**: Monitor order volume by tenant and time period
- **Inventory Levels**: Monitor inventory levels and alert on low stock
- **Credit Aging**: Monitor credit aging and alert on overdue payments
- **System Uptime**: Monitor system uptime and alert on downtime

**Alerting**:
- **Alert Channels**: WhatsApp, email, and optional Slack integration
- **Alert Severity**: Critical, Warning, and Informational levels
- **Alert Escalation**: Escalate unacknowledged alerts after 30 minutes
- **Alert Suppression**: Suppress alerts during maintenance windows

### Backup and Disaster Recovery Requirements

**Database Backups**:
- **Backup Frequency**: Daily full backups, hourly incremental backups
- **Backup Retention**: Retain daily backups for 30 days, monthly backups for 12 months
- **Backup Storage**: Store backups in separate geographic region
- **Backup Testing**: Test backup restoration monthly

**Redis Backups**:
- **Backup Frequency**: Hourly snapshots of Redis data
- **Backup Retention**: Retain hourly snapshots for 7 days
- **Backup Storage**: Store snapshots in separate geographic region
- **Backup Testing**: Test snapshot restoration weekly

**Disaster Recovery**:
- **RTO (Recovery Time Objective)**: 4 hours for system recovery
- **RPO (Recovery Point Objective)**: 1 hour for data recovery
- **Failover Process**: Automated failover to backup system
- **Recovery Testing**: Test disaster recovery process quarterly

### Deployment and Rollback Procedures

**Deployment Process**:
- **Staging Deployment**: Deploy to staging environment first
- **Testing**: Run automated tests in staging environment
- **Production Deployment**: Deploy to production during low-traffic hours
- **Health Checks**: Run health checks after deployment

**Rollback Process**:
- **Rollback Trigger**: Automatic rollback on critical errors
- **Rollback Time**: Rollback within 5 minutes of trigger
- **Rollback Verification**: Verify system health after rollback
- **Incident Response**: Initiate incident response on rollback

**Maintenance Windows**:
- **Scheduled Maintenance**: Monthly maintenance windows (2 hours)
- **Emergency Maintenance**: As needed for critical issues
- **Notification**: Notify tenants 24 hours before scheduled maintenance
- **Downtime**: Minimize downtime during maintenance windows

---

## 10. Testing Requirements

### Test Coverage Targets (75% Agent Pipeline, 90% Financial Modules)

**Agent Pipeline Test Coverage (75%+)**:
- **Liaison Agent**: 75%+ test coverage for intent extraction and confidence scoring
- **Strategist Agent**: 75%+ test coverage for business logic validation
- **Auditor Agent**: 75%+ test coverage for ledger writing and PDF generation
- **Agent Communication**: 75%+ test coverage for Redis Streams communication
- **Error Handling**: 75%+ test coverage for error scenarios and fallbacks

**Financial Module Test Coverage (90%+)**:
- **Ledger Module**: 90%+ test coverage for all ledger operations
- **Inventory Module**: 90%+ test coverage for all inventory operations
- **Credit Module**: 90%+ test coverage for all credit operations
- **GST Module**: 90%+ test coverage for all GST calculations
- **Order Module**: 90%+ test coverage for all order processing

### Integration Test Scenarios

**End-to-End Order Processing**:
- **Voice Note Order**: Test complete flow from voice note to PDF invoice
- **Text Message Order**: Test complete flow from text message to PDF invoice
- **Credit Order**: Test complete flow for credit orders with limit checking
- **Low Confidence Order**: Test complete flow for orders requiring owner confirmation
- **Multi-Tenant Order**: Test complete flow across multiple tenants

**Agent Communication**:
- **Liaison to Strategist**: Test message passing from Liaison to Strategist
- **Strategist to Auditor**: Test message passing from Strategist to Auditor
- **Error Propagation**: Test error handling and propagation across agents
- **Retry Logic**: Test retry logic for failed messages
- **Dead Letter Queue**: Test dead letter queue for permanently failed messages

**Multi-Tenancy Isolation**:
- **Schema Isolation**: Test PostgreSQL schema isolation between tenants
- **Redis Isolation**: Test Redis namespace isolation between tenants
- **WhatsApp Routing**: Test WhatsApp phone number routing between tenants
- **Data Leakage**: Test for data leakage between tenants under concurrent load

### Performance Benchmark Requirements

**Webhook Performance**:
- **Throughput**: 100 requests/second sustained
- **Latency**: <200ms for 95th percentile
- **Error Rate**: <0.1% error rate under normal load
- **Scalability**: Linear scaling with increased load

**Database Performance**:
- **Query Performance**: <100ms average for all queries
- **Transaction Performance**: <200ms for financial transactions
- **Connection Pool**: Support for 100 concurrent connections
- **Index Performance**: All queries use appropriate indexes

**Whisper Performance**:
- **Transcription Speed**: <30s for 95th percentile of voice notes
- **Accuracy**: >85% accuracy for common Hinglish phrases
- **Resource Usage**: <1GB RAM and <1 vCPU per transcription
- **Batch Processing**: Support for 5 concurrent transcriptions

### Security Audit Requirements

**Penetration Testing**:
- **External Testing**: Quarterly external penetration testing
- **Internal Testing**: Monthly internal security audits
- **Vulnerability Scanning**: Weekly vulnerability scanning
- **Compliance Testing**: Monthly compliance testing

**Access Control Testing**:
- **Tenant Isolation**: Test tenant isolation under all scenarios
- **Role-Based Access**: Test role-based access control
- **API Security**: Test API security and authentication
- **Data Encryption**: Test data encryption at rest and in transit

**Audit Trail Testing**:
- **Transaction Logging**: Verify all financial transactions are logged
- **Access Logging**: Verify all access to financial data is logged
- **Change Logging**: Verify all changes to financial data are logged
- **Log Integrity**: Verify log integrity and tamper resistance

### User Acceptance Testing Criteria

**Functional Testing**:
- **Order Processing**: Test all order processing scenarios
- **Inventory Management**: Test all inventory management scenarios
- **Credit Tracking**: Test all credit tracking scenarios
- **Invoice Generation**: Test all invoice generation scenarios

**Usability Testing**:
- **WhatsApp Interaction**: Test WhatsApp interaction flows
- **Dashboard Usability**: Test dashboard usability and accessibility
- **Error Messages**: Test error message clarity and helpfulness
- **Documentation**: Test documentation completeness and accuracy

**Performance Testing**:
- **Load Testing**: Test system under expected load
- **Stress Testing**: Test system beyond expected load
- **Endurance Testing**: Test system over extended periods
- **Recovery Testing**: Test system recovery from failures

---

## 11. Success Metrics

### Measurable Success Criteria

**Order Processing Accuracy (>99.5%)**:
- **Metric**: Percentage of orders processed correctly without errors
- **Measurement**: Automated monitoring of order processing errors
- **Target**: >99.5% accuracy within 90 days post-launch
- **Baseline**: Manual processing ~85% accuracy

**Invoice Generation Success (>99.9%)**:
- **Metric**: Percentage of invoices generated successfully
- **Measurement**: Automated monitoring of invoice generation failures
- **Target**: >99.9% success within 90 days post-launch
- **Baseline**: Manual processing ~90% success

**Multi-Tenant Isolation (100%)**:
- **Metric**: Percentage of tenant data properly isolated
- **Measurement**: Automated testing for cross-tenant data leakage
- **Target**: 100% isolation maintained at all times
- **Baseline**: N/A (new system)

**Financial Ledger Integrity (100%)**:
- **Metric**: Percentage of financial transactions ACID compliant
- **Measurement**: Automated monitoring of transaction integrity
- **Target**: 100% integrity maintained at all times
- **Baseline**: Manual processing ~95% integrity

**User Satisfaction Targets**:
- **Customer Satisfaction**: >4.5/5.0 customer satisfaction score
- **Owner Satisfaction**: >4.5/5.0 owner satisfaction score
- **Support Ticket Reduction**: >50% reduction in support tickets
- **Time Savings**: >60% reduction in order processing time

### Business Impact Metrics

**Revenue Impact**:
- **Order Volume**: >20% increase in order volume
- **Order Value**: >15% increase in average order value
- **Customer Retention**: >10% improvement in customer retention
- **New Customer Acquisition**: >15% increase in new customer acquisition

**Cost Impact**:
- **Operational Costs**: >30% reduction in operational costs
- **Error Costs**: >50% reduction in error-related costs
- **Staff Efficiency**: >40% improvement in staff efficiency
- **Inventory Costs**: >20% reduction in inventory holding costs

**Strategic Impact**:
- **Market Position**: Establish leadership in WhatsApp-first ERP
- **Competitive Advantage**: Differentiate through Hinglish NLP capabilities
- **Scalability**: Enable rapid scaling to new tenants
- **Innovation**: Pioneer AI-powered business automation

### Technical Success Metrics

**System Performance**:
- **API Response Time**: <200ms for 95th percentile
- **Database Query Performance**: <100ms average
- **WhatsApp Message Latency**: <30s for voice notes
- **System Uptime**: >99.9% availability

**Quality Metrics**:
- **Test Coverage**: 75% agent pipeline, 90% financial modules
- **Bug Density**: <1 bug per 1000 lines of code
- **Code Quality**: Maintain code quality score >8/10
- **Documentation**: 100% API documentation coverage

**Adoption Metrics**:
- **Tenant Adoption**: >50% target tenant adoption within 6 months
- **Feature Adoption**: >80% feature adoption among active tenants
- **User Engagement**: >70% weekly active user rate
- **Retention Rate**: >90% monthly retention rate

---

## 12. Launch Plan

| Phase | Date | Audience | Success Gate |
|-------|------|----------|-------------|
| Internal Alpha | Week 1-2 | Team + 5 design partners | No P0 bugs, core flow complete |
| Closed Beta | Week 3-4 | 20 opted-in customers | <5% error rate, CSAT ≥ 4/5 |
| GA Rollout | Week 5-6 | 100% rollout | Metrics on target at 20% |

**Rollback Criteria**: If order processing accuracy drops below 95% or error rate exceeds 1%, revert flag and page on-call.

---

## 13. Appendix

### User Research Session Recordings
- [Session recordings to be added during discovery phase]
- [Interview notes to be added during discovery phase]

### Competitive Analysis Doc
- [Competitive analysis to be added during discovery phase]
- [Market positioning analysis to be added during discovery phase]

### Design Mocks
- [Figma link to be added during design phase]
- [UI/UX mockups to be added during design phase]

### Analytics Dashboard Link
- [Analytics dashboard link to be added during development phase]
- [Monitoring dashboard link to be added during development phase]

### Relevant Support Tickets
- [Support ticket analysis to be added during discovery phase]
- [Common pain points analysis to be added during discovery phase]

---

**PRD Status**: Draft - Ready for Backend Architect and Frontend Developer review
**Next Steps**: Backend Architect and Frontend Developer to review PRD for technical feasibility
**Timeline**: 2-3 hours for PRD review and feedback
**Confidence**: HIGH - Comprehensive requirements with clear acceptance criteria

---

