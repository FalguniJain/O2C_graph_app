# O2C Graph — Order to Cash Analytics

A **graph-based data modeling and conversational query system** for SAP Order-to-Cash data.  
Built with React + D3 (frontend), Flask + SQLite (backend), and Groq LLaMA 3.3 70B (LLM).

---

## What It Does

- **Interactive graph** of all O2C entities: Sales Orders, Deliveries, Billing Documents, Payments, Journal Entries, Customers, Products
- **Click any node to expand** — its neighbors appear on the canvas dynamically
- **Entity type filter bar** — show/hide node types with one click
- **Chat interface** — ask questions in plain English, get data-backed answers with the SQL shown
- **Node highlighting** — chat responses highlight relevant nodes in the graph
- **Guardrails** — two-layer system (keyword + LLM intent classification) rejects off-topic queries

---

## Quick Start

### Prerequisites
- Python 3.9+, Node.js 18+
- A free Groq API key from https://console.groq.com

### Step 1 — Set API key in `backend/.env`
```
GROQ_API_KEY=your_key_here
```

### Step 2 — Place the dataset
```
o2c-graph-app/
├── data/
│   ├── sales_order_headers/
│   ├── billing_document_headers/
│   └── ... (all JSONL folders from the dataset zip)
```

### Step 3 — Run

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
```
start.bat
```

**Manual:**
```bash
# Terminal 1
cd backend && pip install -r requirements.txt && python app.py

# Terminal 2
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**

---

## Architecture

```
Browser
  ├── D3 Force Graph (GraphVisualization.jsx)
  │     ├── Filter bar — toggle entity types
  │     ├── Click-to-expand — fetches neighbors via /api/graph/node/:id/expand
  │     └── Node highlight — gold ring on LLM-referenced entities
  └── Chat Panel (ChatPanel.jsx)
        └── Sends NL query → /api/chat → answer + SQL + highlighted node IDs

Flask Backend (port 5000)
  ├── /api/graph           → full node+edge list (built from SQLite on startup)
  ├── /api/graph/node/:id/expand → neighbors for click-to-expand
  ├── /api/chat            → guardrail → LLM SQL gen → SQLite exec → LLM answer
  └── /api/stats           → record counts

SQLite Database (auto-created from JSONL on first run)
  └── 16 tables: sales_order_headers, billing_document_headers,
      outbound_delivery_headers, payments, journal_entries,
      business_partners, products, and more
```

---

## Database Choice — SQLite

**Why SQLite instead of Neo4j or PostgreSQL?**

The dataset has ~1,500–2,000 core business documents. SQLite handles this with zero configuration, zero infrastructure cost, and ships with Python's standard library. The graph is constructed in-memory at startup from relational joins, not stored natively as a graph.

**Why not Neo4j?** Neo4j would be the right choice at millions of entities where traversal queries (multi-hop paths) become slow in SQL. At this scale, the JOIN-based approach is faster to query and easier to inspect. The tradeoff is that adding new relationship types requires schema changes rather than just adding edges — acceptable here since the O2C schema is well-defined.

**Upgrade path:** PostgreSQL + pgvector for semantic search, or Neo4j if the entity count grows 100x and path queries dominate.

---

## LLM Prompting Strategy

The system uses a **two-step pipeline** per query:

### Step 1 — SQL generation
The LLM receives:
- Full schema (16 tables, all columns, all FKs)
- Explicit join patterns for the O2C flow (SO → Delivery → Billing → Journal → Payment)
- Business rule codes (status A/B/C, cancelled = 'X')
- Three worked example queries

It returns `{ sql, explanation, entity_ids }` as JSON. The `entity_ids` field is used to highlight nodes in the graph.

### Step 2 — Answer synthesis
The actual query results (up to 50 rows) are passed back with the user's question. The LLM writes a natural-language answer grounded only in those results.

**Why two steps?** A single "answer the question" prompt tends to hallucinate data. Separating SQL generation from answer synthesis forces the LLM to ground its answer in real query results rather than its training knowledge.

---

## Guardrail System

Two-layer approach (explicitly called out as an evaluation criterion):

**Layer 1 — Keyword hard-block (no LLM cost)**  
A list of obviously off-topic patterns (`write a poem`, `weather`, `sports`, etc.) is checked first. If matched, the query is rejected immediately with no LLM call.

**Layer 2 — LLM intent classification**  
For queries that pass Layer 1 but lack clear domain keywords, a lightweight LLM call classifies intent as `ALLOWED` or `BLOCKED`. This catches adversarial prompts like "write a poem about billing status codes" that keyword lists miss.

Example rejection message:
> "This system is designed to answer questions related to the SAP Order-to-Cash dataset only — such as sales orders, deliveries, billing documents, payments, customers, and products."

---

## Example Queries

```
Which products are associated with the highest number of billing documents?
Trace the full flow of billing document 91150187
Find sales orders that have been delivered but not billed
What is the total revenue by currency?
List all cancelled billing documents
Which customers have the most sales orders?
Show orders with broken or incomplete flows
What is the average order value?
```

---

## Graph Model

| Node type | Key field | Color |
|-----------|-----------|-------|
| Customer | businessPartner | Pink |
| SalesOrder | salesOrder | Blue |
| SalesOrderItem | salesOrder + item | Cyan |
| BillingDocument | billingDocument | Purple |
| Delivery | deliveryDocument | Green |
| Payment | accountingDocument | Amber |
| JournalEntry | accountingDocument | Red |
| Product | product | Lime |

Relationships:
- `Customer → PLACED_ORDER → SalesOrder`
- `SalesOrder → HAS_ITEM → SalesOrderItem`
- `SalesOrderItem → IS_MATERIAL → Product`
- `SalesOrder → DELIVERED_VIA → Delivery`
- `Delivery → BILLED_AS → BillingDocument`
- `BillingDocument → POSTED_TO → JournalEntry`
- `BillingDocument → PAID_BY → Payment`

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph` | GET | All nodes + edges |
| `/api/graph/node/:id` | GET | Node details + connections |
| `/api/graph/node/:id/expand` | GET | Node + all neighbors (for expand feature) |
| `/api/stats` | GET | Record counts + revenue |
| `/api/chat` | POST | NL query → guardrail → SQL → answer |
| `/api/health` | GET | Health check |
| `/api/sample-queries` | GET | Suggested example questions |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 19 + Vite | Fast dev, great D3 integration |
| Graph | D3.js v7 force-directed | Industry standard, fully customizable |
| Styling | Pure CSS dark theme | No framework bloat |
| Backend | Flask 3 | Minimal, Python-native |
| Database | SQLite | Zero-config, portable, sufficient at this scale |
| LLM | Groq LLaMA 3.3 70B | Free tier, fast inference, strong SQL generation |
| Data format | JSONL → SQLite | Auto-ingested on first run |

---

## Project Structure

```
o2c-graph-app/
├── backend/
│   ├── app.py              # Flask API + graph builder + LLM pipeline
│   ├── requirements.txt
│   └── o2c.db             # Auto-generated SQLite DB (gitignored)
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── components/
│           ├── GraphVisualization.jsx  # D3 graph + filter + expand
│           ├── ChatPanel.jsx           # Chat UI + API
│           ├── StatsBar.jsx            # Top stats strip
│           └── NodeModal.jsx           # Node detail popup
├── data/                   # JSONL dataset (gitignored)
├── start.sh
└── start.bat
```
