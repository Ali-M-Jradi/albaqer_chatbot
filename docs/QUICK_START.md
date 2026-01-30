# 🤖 AlBaqer Chatbot - Quick Start Guide

## ✅ Setup Complete!

Your virtual environment is ready with all dependencies installed.

---

## 🚀 How to Run the Chatbot

### Option 1: Streamlit Web UI (Recommended)
```powershell
.\run_chatbot.ps1
```
**Opens at:** `http://localhost:8501`

### Option 2: Command Line Interface
```powershell
.\run_cli.ps1
```

### Option 3: Manual Commands
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run Streamlit UI
streamlit run streamlit_ui_app.py

# OR run CLI
python main.py
```

---

## 📦 What's Installed

- ✅ **Virtual Environment** (`venv/`) - Isolated Python environment
- ✅ **All Dependencies** - LangChain, Streamlit, OpenAI, Google GenAI, etc.
- ✅ **Database Connection** - Connected to `albaqer_gemstone_ecommerce_db`

---

## 🔧 Configuration

### Database Settings (`.env`)
```
DB_HOST=localhost
DB_NAME=albaqer_gemstone_ecommerce_db
DB_USER=postgres
DB_PASSWORD=po$7Gr@s$
```

### API Keys (`.env`)
```
DEEPSEEK_API_KEY=sk-da97c4dbc0f84832bbffd1d5057e53c1
GEMINI_API_KEY=AIzaSyA4wEFwLUEJ5WqWn21vYHJ9yZrPg8Ta4Xo
```

---

## 🎯 Features

### 11 Specialized AI Agents:
1. **SEARCH_AGENT** - Product search & filtering
2. **KNOWLEDGE_AGENT** - Gemstone education
3. **RECOMMENDATION_AGENT** - Personalized suggestions
4. **COMPARISON_AGENT** - Compare products
5. **PRICING_AGENT** - Currency conversion
6. **DELIVERY_AGENT** - Shipping info
7. **PAYMENT_AGENT** - Payment methods
8. **CUSTOMER_SERVICE_AGENT** - General support
9. **CULTURAL_AGENT** - Islamic guidance
10. **INVENTORY_AGENT** - Stock availability
11. **SUPERVISOR_AGENT** - Query routing

---

## 🛠️ Maintenance

### Update Dependencies
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
```

### Reinstall from Scratch
```powershell
# Delete virtual environment
Remove-Item -Recurse -Force venv

# Create new one
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📝 Notes

- The virtual environment is **isolated** - changes won't affect other Python projects
- Dependencies are **frozen** - no need to reinstall every time
- Just run the scripts to start the chatbot anytime!

---

## 🎉 You're Ready!

Run `.\run_chatbot.ps1` to start chatting! 🚀
