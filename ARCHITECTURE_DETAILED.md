# AlBaqer Stones - Architecture Diagram

## System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY INPUT                              │
│                                                                        │
│  Streamlit UI  OR  main.py  OR  Custom Script                        │
└────────────────────────────┬────────────────────────────────────────┘
                              │
                              ↓
                ┌─────────────────────────────┐
                │  run_multi_agent_system()   │  (main.py)
                │  - Entry point              │
                │  - Orchestration            │
                └────────────┬────────────────┘
                             │
                             ↓
        ┌────────────────────────────────────────┐
        │  create_supervisor_agent()              │  (agents/supervisor.py)
        │  - Routes query to best agent           │
        │  - Analyzes user intent                 │
        └────────────┬─────────────────────────┘
                     │
      ┌──────────────┴──────────────┬──────────────────────┐
      ↓                             ↓                      ↓
 SEARCH_AGENT             KNOWLEDGE_AGENT         RECOMMENDATION_AGENT
 COMPARISON_AGENT         PRICING_AGENT           DELIVERY_AGENT
 PAYMENT_AGENT            CUSTOMER_SERVICE       CULTURAL_AGENT
 INVENTORY_AGENT          
                          (agents/specialized_agents.py)
      │                             │                      │
      └──────────────┬──────────────┴──────────────────────┘
                     ↓
         ┌───────────────────────────┐
         │  Agent Tools (tools/)      │
         │                           │
         │  ┌─ search_products()     │
         │  ├─ get_stone_info()      │
         │  ├─ get_knowledge_base()  │
         │  ├─ calculate_delivery()  │
         │  ├─ convert_currency()    │
         │  ├─ check_stock()         │
         │  ├─ get_payment_methods() │
         │  └─ compare_products()    │
         └───────────┬───────────────┘
                     │
                     ↓
        ┌────────────────────────────┐
        │  PostgreSQL Database        │  (database/connection.py)
        │  - products                 │
        │  - stones                   │
        │  - categories               │
        │  - delivery_zones           │
        │  - currency_rates           │
        │  - payment_methods          │
        │  - knowledge_base           │
        └────────────────────────────┘
         
         
         WITH RAG:
         
         ChromaDB Vector Store (vector_rag_system.py)
         ├─ Semantic search
         └─ Knowledge base embeddings
```

---

## Module Dependencies

```
streamlit_ui_app.py ─┐
                     ├──→ main.py
custom_script.py ────┤    │
                     │    ├──→ agents/
                     │         ├── specialized_agents.py
                     │         └── supervisor.py
                     │              │
                     │              ├──→ tools/
                     │              │    ├── product_tools.py
                     │              │    ├── stone_tools.py
                     │              │    ├── knowledge_tools.py
                     │              │    ├── logistics_tools.py
                     │              │    └── inventory_tools.py
                     │              │         │
                     │              │         ├──→ database/
                     │              │         │    └── connection.py
                     │              │         │         │
                     │              │         │         └──→ PostgreSQL
                     │              │         │
                     │              │         └──→ vector_rag_system.py
                     │              │              │
                     │              │              └──→ ChromaDB
                     │              │
                     │              └──→ config/
                     │                   └── settings.py (LLMs)
                     │
                     └──→ middleware/
                          └── dynamic_routing.py
```

---

## Code Organization

```
albaqer_stones/
│
├── 📁 config/                    Configuration & Models
│   ├── __init__.py
│   └── settings.py               • get_deepseek()
│                                 • get_gemini()
│
├── 📁 database/                  Database Utilities
│   ├── __init__.py
│   └── connection.py             • get_db_connection()
│
├── 📁 tools/                     LangChain Tools (7 tools in 5 files)
│   ├── __init__.py               Centralized imports
│   ├── product_tools.py          • search_products()
│   │                             • compare_products()
│   ├── stone_tools.py            • get_stone_info()
│   ├── knowledge_tools.py        • get_knowledge_base()
│   ├── logistics_tools.py        • calculate_delivery_fee()
│   │                             • convert_currency()
│   │                             • get_payment_methods()
│   └── inventory_tools.py        • check_stock()
│
├── 📁 agents/                    Agent Definitions (11 agents in 2 files)
│   ├── __init__.py               ALL_AGENTS dictionary
│   ├── specialized_agents.py     • create_search_agent()
│   │                             • create_knowledge_agent()
│   │                             • create_recommendation_agent()
│   │                             • create_comparison_agent()
│   │                             • create_pricing_agent()
│   │                             • create_delivery_agent()
│   │                             • create_payment_agent()
│   │                             • create_customer_service_agent()
│   │                             • create_cultural_agent()
│   │                             • create_inventory_agent()
│   └── supervisor.py             • create_supervisor_agent()
│
├── 📁 middleware/                Agent Middleware
│   ├── __init__.py
│   └── dynamic_routing.py        • dynamic_model_selection()
│
├── main.py                       Entry Point
│   │                             • run_multi_agent_system()
│   │                             • Example usage
│   └
│
├── streamlit_ui_app.py           Web UI (unchanged)
├── vector_rag_system.py          RAG/ChromaDB (unchanged)
│
├── requirements.txt              Dependencies
├── .env                          Environment variables
│
├── ARCHITECTURE.md               (This) Detailed architecture guide
└── QUICKSTART.md                 Quick reference guide
```

---

## Data Flow Example

### Query: "Show me Aqeeq rings under $100"

```
1. run_multi_agent_system("Show me Aqeeq rings under $100")
   ↓
2. Supervisor analyzes: "This is a SEARCH query"
   ↓
3. Route to: SEARCH_AGENT
   ↓
4. SEARCH_AGENT calls tools:
   - search_products(stone_name="Aqeeq", max_price=100)
   ↓
5. search_products() (product_tools.py):
   - Builds SQL query
   - Calls get_db_connection() (database/connection.py)
   - Connects to PostgreSQL
   - Executes: SELECT * FROM products WHERE stone='Aqeeq' AND price < 100
   ↓
6. Database returns: [Product1, Product2, Product3, ...]
   ↓
7. SEARCH_AGENT formats response
   ↓
8. Return to user: "Here are 3 Aqeeq rings under $100..."
```

---

## Agent Decision Tree

```
Supervisor analyzes intent:
│
├─ "Show me / Find / Search" → SEARCH_AGENT
├─ "What is / Tell me about / Meaning" → KNOWLEDGE_AGENT
├─ "Recommend / Suggest / Best for" → RECOMMENDATION_AGENT
├─ "Compare / Difference / Which is better" → COMPARISON_AGENT
├─ "Price / Cost / Convert" → PRICING_AGENT
├─ "Delivery / Shipping / Address" → DELIVERY_AGENT
├─ "Pay / Payment / Card" → PAYMENT_AGENT
├─ "Help / Support / Question" → CUSTOMER_SERVICE_AGENT
├─ "Islamic / Halal / Gold prohibition" → CULTURAL_AGENT
└─ "In stock / Available / Stock" → INVENTORY_AGENT
```

---

## LLM Routing

```
Dynamic Model Selection (middleware/dynamic_routing.py):

Simple query (1-2 words, straightforward)
├─ Use Gemini (fast, cheaper)
└─ Examples: "Aqeeq price?", "Is item 5 available?"

Complex query (5+ words, requires analysis)
├─ Use DeepSeek (powerful, accurate)
└─ Examples: "Compare these 3 rings", "Recommend something for Eid"

Supervisor & Comparison Agents
├─ Always use DeepSeek (complex logic)
└─ Need more powerful reasoning
```

---

## Performance Characteristics

```
File               | Lines | Purpose
─────────────────────────────────────────
config/settings.py    | 35   | LLM configuration
database/connection   | 20   | DB utilities
tools/product_tools   | 85   | Product search/compare
tools/stone_tools     | 30   | Stone lookup
tools/knowledge_tools | 50   | RAG + fallback
tools/logistics_tools | 90   | Delivery/Currency
tools/inventory_tools | 45   | Stock check
agents/specialized    | 180  | 10 agents
agents/supervisor     | 25   | Router agent
middleware/routing    | 20   | Dynamic LLM selection
main.py               | 120  | Orchestration
─────────────────────────────────────────
TOTAL                 | 700+ | 13 focused files
```

Original: 850 lines in 1 file  
Refactored: 700+ lines in 13 files  
→ Average: 54 lines per file ✅

---

## Adding New Capabilities

### New Agent
1. Add function to `agents/specialized_agents.py`
2. Register in `agents/__init__.py`
3. Update supervisor prompt

### New Tool
1. Create file in `tools/`
2. Export from `tools/__init__.py`
3. Assign to agent

### New LLM Model
1. Add to `config/settings.py`
2. Use in agents

### New Database Table
1. Update schema
2. Create tool in `tools/`

---

Created: December 2024  
Architecture: Modular Multi-Agent System  
Framework: LangChain + DeepSeek + Gemini
