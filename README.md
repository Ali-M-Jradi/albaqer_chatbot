# AlBaqer Chatbot - RAG System

AI-powered chatbot with multi-agent system for AlBaqer Islamic Gemstone Store.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start API Server
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 3. Access API
- Health: http://localhost:8000/api/health
- Chat: POST http://localhost:8000/api/chat

## 🤖 Multi-Agent System

- **Supervisor Agent** - Routes queries to specialized agents
- **Search Agent** - Product search
- **Knowledge Agent** - Stone education (RAG-powered)
- **Recommendation Agent** - Personalized suggestions
- **Customer Service** - General support
- And 6 more specialized agents!

## 🧠 RAG System

- **Vector Database**: PostgreSQL with JSON embeddings
- **Embeddings**: HuggingFace sentence-transformers
- **Knowledge Base**: 20+ articles about Islamic gemstones

## 📱 Mobile Integration

Use the Flutter service (`lib/services/chatbot_service.dart`) to connect your mobile app.

## 📖 Full Documentation

See the [docs](./docs) folder for:
- Architecture details
- Setup guides
- Integration instructions
- API documentation
