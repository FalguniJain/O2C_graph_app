# 🔗 O2C Graph — Order to Cash Analytics

A **graph-based data modeling and conversational query system** for SAP Order-to-Cash data.  
Built with React + D3 (frontend), Flask + SQLite (backend), and Claude (LLM query engine).

---

## 📸 What It Looks Like

- **Interactive graph** of all O2C entities: Sales Orders, Deliveries, Billing Documents, Payments, Journal Entries, Customers, Products
- **Chat interface** — ask questions in plain English, get data-backed answers
- **Node inspection** — click any node to see its properties and connections
- **SQL transparency** — see the exact query the AI generated

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- A **GROQ API key** — get one free at https://console.groq.com

### Step 1 — Set your API key

**Windows:**
```
set GROQ_API_KEY=gsk-your-key-here
```

**Mac / Linux:**
```bash
export GROQ_API_KEY=gsk-your-key-here
```

### Step 2 — Place the dataset

Put the `data/` folder (containing `sap-o2c-data/`) inside this project root:
```
o2c-graph-app/
├── data/
│   └── sap-o2c-data/
│       ├── sales_order_headers/
│       ├── billing_document_headers/
│       └── ... (all JSONL folders)
├── backend/
├── frontend/
└── README.md
```

### Step 3 — Run

**One-click on Mac/Linux:**
```bash
./start.sh
```

**One-click on Windows:**
```
start.bat
```

**Manual:**
```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python app.py

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser UI                        │
│  ┌──────────────────────┐  ┌──────────────────────┐ │
│  │   D3 Graph Canvas    │  │   Chat Interface     │ │
│  │  Force-directed viz  │  │  Natural language    │ │
│  │  Node click → modal  │  │  query → answer      │ │
│  └──────────┬───────────┘  └──────────┬───────────┘ │
└─────────────│────────────────────────│──────────────┘
              │  REST API              │ REST API
              ▼                        ▼
┌─────────────────────────────────────────────────────┐
│              Flask Backend (port 5000)               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Graph Builder│  │  SQL Engine  │  │  LLM Proxy│  │
│  │ nodes+edges  │  │  SQLite DB   │  │  Anthropic│  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────┐
│     SQLite Database     │
│  12 tables, ~1500 rows  │
│  Indexed for fast joins │
└─────────────────────────┘
```

### Database Choice — SQLite
- **Why SQLite?** Zero-config, file-based, ships with Python. The dataset is ~1500 core records — SQLite handles this effortlessly and makes the project portable (just copy the folder).  
- The DB is auto-created on first run from the JSONL files.
- For production scale (millions of rows), PostgreSQL or DuckDB would be the upgrade path.

### Graph Model
Entities (nodes):
| Type | Key Field | Color |
|------|-----------|-------|
| Customer | businessPartner | Pink |
| SalesOrder | salesOrder | Blue |
| SalesOrderItem | salesOrder + item | Cyan |
| BillingDocument | billingDocument | Purple |
| Delivery | deliveryDocument | Green |
| Payment | accountingDocument | Amber |
| JournalEntry | accountingDocument | Red |
| Product | product | Lime |

Relationships (edges):
- `Customer → PLACED_ORDER → SalesOrder`
- `SalesOrder → HAS_ITEM → SalesOrderItem`
- `SalesOrderItem → IS_MATERIAL → Product`
- `SalesOrder → DELIVERED_VIA → Delivery`
- `SalesOrder → BILLED_AS → BillingDocument`
- `BillingDocument → POSTED_TO → JournalEntry`
- `BillingDocument → PAID_BY → Payment`

### LLM Prompting Strategy
The system uses a **two-step LLM pipeline**:

1. **SQL Generation step** — Claude receives the full schema description + user question and returns a JSON object with `{ sql, explanation, entity_ids }`.
2. **Answer synthesis step** — Claude receives the actual query results and generates a natural language answer.

The schema prompt includes:
- All table names, column names, and types
- Foreign key relationships
- Business domain rules (status codes, flow definitions)
- SQLite-specific syntax guidance

**Guardrails** — Before hitting the LLM, a keyword filter checks whether the query is domain-relevant. Off-topic queries (general knowledge, creative writing, etc.) are rejected immediately with a polite message.

---

## 💬 Example Queries

```
"Which products are associated with the highest number of billing documents?"
"Trace the full flow of billing document 91150187"
"Find sales orders that have been delivered but not billed"
"What is the total revenue by currency?"
"List all cancelled billing documents"
"Which customers have the most sales orders?"
"Show me the average order value"
"Which orders have incomplete or broken flows?"
```

---

## 📁 Project Structure

```
o2c-graph-app/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python deps
│   └── o2c.db             # Auto-generated SQLite DB
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Root component + layout
│   │   ├── App.css                    # All styles
│   │   └── components/
│   │       ├── GraphVisualization.jsx # D3 force graph
│   │       ├── ChatPanel.jsx          # Chat UI + API calls
│   │       ├── StatsBar.jsx           # Top stats strip
│   │       └── NodeModal.jsx          # Node detail popup
│   ├── index.html
│   └── package.json
├── data/                   # ← Put JSONL dataset here
├── start.sh                # Mac/Linux launcher
├── start.bat               # Windows launcher
└── README.md
```

---

## 🔑 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph` | GET | All nodes + edges |
| `/api/graph/node/:id` | GET | Single node + connections |
| `/api/stats` | GET | Record counts + revenue |
| `/api/chat` | POST | NL query → SQL → answer |
| `/api/health` | GET | Health check |
| `/api/sample-queries` | GET | Example questions |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend framework | React 19 + Vite |
| Graph visualization | D3.js v7 (force-directed) |
| Styling | Pure CSS (custom dark theme) |
| Backend framework | Flask 3 |
| Database | SQLite (via Python stdlib) |
| LLM | Claude claude-sonnet-4-20250514 (Anthropic) |
| Data format | JSONL → SQLite (auto-ingested) |

---

## ⚠️ Troubleshooting

**"Failed to connect to backend"**  
→ Make sure `python app.py` is running in the `backend/` folder  
→ Check that port 5000 is free: `lsof -i :5000`

**"No module named anthropic"**  
→ Run `pip install -r backend/requirements.txt`

**Chat returns guardrail message**  
→ Ask questions about the O2C data (orders, billing, delivery, etc.)

**DB not found / empty graph**  
→ Make sure the `data/sap-o2c-data/` folder is at the correct path  
→ Delete `backend/o2c.db` and restart to rebuild

---

## 📝 License

Built for Dodge AI Forward Deployed Engineer assignment.
# O2C_graph_app
# O2C_graph_app
