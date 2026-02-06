#!/usr/bin/env python3
"""
Pre-Flight System Health Check
Verifies all components are ready before running the chatbot
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 ALBAQER CHATBOT - SYSTEM HEALTH CHECK")
print("=" * 70)

errors = []
warnings = []

# 1. Check Python version
print("\n[1/7] Python Environment...")
if sys.version_info >= (3, 8):
    print(f"   ✅ Python {sys.version.split()[0]}")
else:
    errors.append("Python 3.8+ required")
    print(f"   ❌ Python {sys.version.split()[0]} (need 3.8+)")

# 2. Check critical dependencies
print("\n[2/7] Critical Dependencies...")
try:
    import psycopg2
    import chromadb
    import langchain_community
    from sentence_transformers import SentenceTransformer
    import google.generativeai as genai

    print("   ✅ All critical packages installed")
except ImportError as e:
    errors.append(f"Missing package: {e.name}")
    print(f"   ❌ Missing: {e.name}")

# 3. Check database connection
print("\n[3/7] Database Connection...")
try:
    import psycopg2

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    conn.close()
    print("   ✅ PostgreSQL connected")
except Exception as e:
    errors.append(f"Database error: {str(e)}")
    print(f"   ❌ Database connection failed: {str(e)[:50]}")

# 4. Check vector store
print("\n[4/7] Vector Store (ChromaDB)...")
if os.path.exists("./chroma_db"):
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
        )

        vectorstore = Chroma(
            persist_directory="./chroma_db",
            collection_name="albaqer_knowledge_base",
            embedding_function=embeddings,
        )

        count = vectorstore._collection.count()
        print(f"   ✅ ChromaDB working ({count} documents)")

        if count < 40:
            warnings.append(f"Only {count} documents in RAG (expected 48+)")

    except Exception as e:
        errors.append(f"ChromaDB error: {str(e)}")
        print(f"   ❌ ChromaDB failed: {str(e)[:50]}")
else:
    errors.append("ChromaDB not found - run setup_rag.py first")
    print("   ❌ Vector store not found")

# 5. Check API keys
print("\n[5/7] API Keys...")
gemini_key = os.getenv("GEMINI_API_KEY")
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

if gemini_key and len(gemini_key) > 20:
    print("   ✅ Gemini API key configured")
else:
    errors.append("Missing GEMINI_API_KEY in .env")
    print("   ❌ Gemini API key missing")

if deepseek_key and len(deepseek_key) > 20:
    print("   ✅ DeepSeek API key configured")
else:
    warnings.append("DeepSeek API key missing (optional)")
    print("   ⚠️  DeepSeek API key missing (optional)")

# 6. Check agent tools
print("\n[6/7] Agent Tools...")
try:
    from tools import cart_tools, inventory_tools, order_tools
    from tools import product_tools, review_tools, stone_tools

    print("   ✅ All 6 agent tools loaded")
except ImportError as e:
    warnings.append(f"Tool import warning: {e.name}")
    print(f"   ⚠️  Warning: {e.name}")

# 7. Test embedding model
print("\n[7/7] Embedding Model...")
try:
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device="cpu")
    test_embedding = model.encode(["test"], normalize_embeddings=True)
    dims = len(test_embedding[0])

    if dims == 768:
        print(f"   ✅ Upgraded model working (768 dimensions)")
    else:
        warnings.append(f"Wrong embedding dimensions: {dims} (expected 768)")
        print(f"   ⚠️  Embedding dimensions: {dims} (expected 768)")

except Exception as e:
    errors.append(f"Embedding model error: {str(e)}")
    print(f"   ❌ Model failed: {str(e)[:50]}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if errors:
    print(f"\n❌ CRITICAL ERRORS ({len(errors)}):")
    for error in errors:
        print(f"   • {error}")
    print("\n⚠️  Fix these errors before running the chatbot!")
    sys.exit(1)

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for warning in warnings:
        print(f"   • {warning}")
    print("\n✅ System will work but consider addressing warnings")

if not errors and not warnings:
    print("\n✅ ALL SYSTEMS OPERATIONAL!")
    print("\n🚀 Ready to launch:")
    print("   • API Server: scripts\\start_api_server.ps1")
    print("   • Web UI: scripts\\run_web_ui.ps1")
    print("   • CLI: scripts\\run_cli.ps1")

print("\n" + "=" * 70)
