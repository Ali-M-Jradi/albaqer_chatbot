# AlBaqer Stones - Quick Start Guide

## 📂 Refactored Structure - What Changed?

Your original `albaqer_agents_system.py` (850 lines) has been split into **13 focused files**:

### **Configuration** (`config/settings.py`)
- `get_deepseek()` 
- `get_gemini()`

### **Database** (`database/connection.py`)
- `get_db_connection()`

### **Tools** (5 files in `tools/`)
- `product_tools.py` → search, compare
- `stone_tools.py` → get_stone_info
- `knowledge_tools.py` → RAG search
- `logistics_tools.py` → delivery, currency, payment
- `inventory_tools.py` → stock check

### **Agents** (2 files in `agents/`)
- `specialized_agents.py` → 10 specialized agents
- `supervisor.py` → 1 router agent

### **Middleware** (`middleware/dynamic_routing.py`)
- `dynamic_model_selection()`

### **Entry Point** (`main.py`)
- `run_multi_agent_system()` (main function)

---

## 🚀 How to Use It

### Option 1: Use the same way as before
```python
from main import run_multi_agent_system

result = run_multi_agent_system("Show me Aqeeq rings")
print(result['response'])
```

### Option 2: Use with Streamlit (unchanged)
```bash
streamlit run streamlit_ui_app.py
```

### Option 3: Import individual components
```python
# Get a specific agent
from agents import create_search_agent
search_agent = create_search_agent()

# Use a specific tool
from tools import search_products
products = search_products(category="Rings")

# Get database connection
from database.connection import get_db_connection
conn = get_db_connection()
```

---

## 📊 File Comparison

| Aspect | Before | After |
|--------|--------|-------|
| Main file | 1 file (850 lines) | 13 focused files |
| Database code | Mixed in | Separate module |
| LLM config | Mixed in | Dedicated file |
| Tools | All in one | 5 separate files |
| Agents | All in one | 2 organized files |
| Readability | Hard | Easy ✅ |
| Maintainability | Difficult | Simple ✅ |
| Testing | Hard | Easy ✅ |
| Reusability | Limited | Full ✅ |

---

## ✅ Backward Compatibility

The refactored code is **100% compatible** with your existing code:

✅ Same imports work: `from main import run_multi_agent_system`  
✅ Same function signatures  
✅ Same database queries  
✅ Same agent behaviors  
✅ Same Streamlit UI  

You can keep using your code exactly as before!

---

## 🎯 Key Benefits

1. **Easier to Debug** - Each file does one thing
2. **Easier to Test** - Can test tools/agents separately
3. **Easier to Add Features** - Add agents/tools without touching others
4. **Easier to Collaborate** - Multiple developers can work on different files
5. **Easier to Read** - 200 lines per file instead of 850 lines
6. **Industry Standard** - Professional code organization

---

## 📚 Learning the Structure

Read files in this order:
1. `config/settings.py` - How LLMs are configured
2. `database/connection.py` - Database utilities
3. `tools/__init__.py` - See what tools exist
4. `tools/product_tools.py` - Example tool file
5. `agents/__init__.py` - See all agents
6. `agents/specialized_agents.py` - How agents are built
7. `agents/supervisor.py` - How routing works
8. `main.py` - How everything ties together

---

## 🔧 Common Tasks

### Add a new tool
1. Create `tools/new_tool.py`
2. Add to `tools/__init__.py`
3. Import in agent file
4. Assign to agent

### Add a new agent
1. Create function in `agents/specialized_agents.py`
2. Add to `ALL_AGENTS` dict in `agents/__init__.py`
3. Update supervisor's prompt

### Change LLM settings
1. Edit `config/settings.py`
2. All agents automatically use new settings

### Modify database queries
1. Edit relevant file in `tools/`
2. Only that tool is affected

---

## 🔗 Import Cheat Sheet

```python
# Main entry point
from main import run_multi_agent_system

# All agents
from agents import ALL_AGENTS, create_supervisor_agent
from agents import create_search_agent, create_knowledge_agent

# All tools
from tools import search_products, get_stone_info, calculate_delivery_fee

# Config
from config.settings import get_deepseek, get_gemini

# Database
from database.connection import get_db_connection

# Middleware
from middleware.dynamic_routing import dynamic_model_selection
```

---

**No changes needed to existing code!**  
Your project is now modular and ready to scale. 🚀
