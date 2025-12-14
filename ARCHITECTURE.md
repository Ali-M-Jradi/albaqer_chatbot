# AlBaqer Stones - Modular Architecture

This project has been refactored into a clean, modular structure for easier development and maintenance.

## 📁 Project Structure

```
albaqer_stones/
├── config/                          # Configuration & LLM models
│   ├── __init__.py
│   └── settings.py                  # get_deepseek(), get_gemini()
│
├── database/                        # Database utilities
│   ├── __init__.py
│   └── connection.py                # get_db_connection()
│
├── tools/                           # LangChain tools for agents
│   ├── __init__.py                  # Centralized exports
│   ├── product_tools.py             # search_products, compare_products
│   ├── stone_tools.py               # get_stone_info
│   ├── knowledge_tools.py           # get_knowledge_base (with RAG)
│   ├── logistics_tools.py           # delivery, currency, payment
│   └── inventory_tools.py           # check_stock
│
├── agents/                          # Agent definitions
│   ├── __init__.py                  # ALL_AGENTS dictionary + exports
│   ├── specialized_agents.py        # Agents 1-10 (specific roles)
│   └── supervisor.py                # Agent 11 (router/supervisor)
│
├── middleware/                      # Agent middleware
│   ├── __init__.py
│   └── dynamic_routing.py           # dynamic_model_selection()
│
├── main.py                          # Entry point - run_multi_agent_system()
├── streamlit_ui_app.py              # Streamlit UI (unchanged)
├── vector_rag_system.py             # RAG/ChromaDB (unchanged)
├── requirements.txt                 # Dependencies
└── README.md                        # This file
```

## 🎯 Agent Overview

| Agent | File | Role |
|-------|------|------|
| 1. SEARCH_AGENT | specialized_agents.py | Find products by filters |
| 2. KNOWLEDGE_AGENT | specialized_agents.py | Educate about stones & Islam |
| 3. RECOMMENDATION_AGENT | specialized_agents.py | Personalized suggestions |
| 4. COMPARISON_AGENT | specialized_agents.py | Compare products |
| 5. PRICING_AGENT | specialized_agents.py | Currency conversion |
| 6. DELIVERY_AGENT | specialized_agents.py | Delivery & logistics |
| 7. PAYMENT_AGENT | specialized_agents.py | Payment methods |
| 8. CUSTOMER_SERVICE_AGENT | specialized_agents.py | General support |
| 9. CULTURAL_AGENT | specialized_agents.py | Islamic guidance |
| 10. INVENTORY_AGENT | specialized_agents.py | Stock availability |
| 11. SUPERVISOR_AGENT | supervisor.py | Routes queries to agents |

## 🔧 How to Use

### Run the main system:
```python
from main import run_multi_agent_system

result = run_multi_agent_system("Show me Aqeeq rings under $100")
print(result['response'])
```

### Use specific agents:
```python
from agents import create_search_agent

search_agent = create_search_agent()
result = search_agent.invoke({
    "messages": [{"role": "user", "content": "Find diamond rings"}]
})
```

### Use specific tools:
```python
from tools import search_products, get_stone_info

# Search products
products = search_products(category="Rings", max_price=500)

# Get stone info
info = get_stone_info("Aqeeq")
```

### Run Streamlit UI:
```bash
streamlit run streamlit_ui_app.py
```

## 📦 Dependencies

All dependencies remain the same - see `requirements.txt`:
- `langchain` - Agent framework
- `langchain-openai` - DeepSeek integration
- `langchain-google-genai` - Gemini integration
- `psycopg2-binary` - PostgreSQL
- `python-dotenv` - Environment variables
- `chromadb` - Vector store (for RAG)
- `streamlit` - Web UI

## 🚀 Benefits of This Structure

✅ **Modular** - Each component has one responsibility
✅ **Scalable** - Easy to add new agents or tools
✅ **Maintainable** - Clear file organization
✅ **Testable** - Can test each module independently
✅ **Reusable** - Tools and agents can be imported anywhere
✅ **Readable** - Smaller files are easier to understand

## 🔄 Workflow

1. **User Query** → `run_multi_agent_system(query)`
2. **Supervisor Routes** → Analyzes query intent
3. **Specialized Agent** → Executes with relevant tools
4. **Tools Query Database** → Fetch/process data
5. **Response Returned** → To user/Streamlit UI

## 📝 Adding a New Agent

1. Create function in `agents/specialized_agents.py`:
```python
def create_my_agent():
    return create_agent(
        model=get_deepseek(),
        middleware=[],
        tools=[tool1, tool2],
        system_prompt="Your role...",
    )
```

2. Add to `agents/__init__.py`:
```python
# In ALL_AGENTS dictionary
"MY_AGENT": create_my_agent,
```

3. Update supervisor's prompt to mention it

## 📝 Adding a New Tool

1. Create file in `tools/`:
```python
# tools/my_tools.py
from langchain.tools import tool

@tool
def my_tool(param: str) -> str:
    """Description of tool"""
    # Implementation
    return result
```

2. Export in `tools/__init__.py`:
```python
from .my_tools import my_tool
__all__ = [..., "my_tool"]
```

3. Import and assign to agents

## 🔗 Import Examples

```python
# Import entire agent system
from main import run_multi_agent_system

# Import specific agent
from agents import create_search_agent

# Import multiple agents
from agents import create_search_agent, create_knowledge_agent

# Import all agents
from agents import ALL_AGENTS

# Import tools
from tools import search_products, get_stone_info

# Import database
from database.connection import get_db_connection

# Import config
from config.settings import get_deepseek, get_gemini

# Import middleware
from middleware.dynamic_routing import dynamic_model_selection
```

## 🐛 Troubleshooting

**Import errors?** Make sure you're in the project root and have set PYTHONPATH:
```bash
set PYTHONPATH=%cd%
```

**Database connection fails?** Check `.env` file has:
- DB_HOST
- DB_NAME
- DB_USER
- DB_PASSWORD

**LLM API errors?** Verify `.env` has:
- DEEPSEEK_API_KEY
- DEEPSEEK_API_BASE
- GEMINI_API_KEY

---

**Created**: December 2024  
**Project**: AlBaqer Islamic Gemstone Store  
**Architecture**: Modular Multi-Agent System
