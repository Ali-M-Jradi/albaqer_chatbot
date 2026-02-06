# =====================================================
# Setup Script - Run this ONCE to initialize RAG system
# =====================================================

print("=" * 60)
print("🕌 AlBaqer Stones - RAG System Setup")
print("=" * 60)

print("\n📦 Step 1: Checking dependencies...")
try:
    import chromadb

    print("✅ ChromaDB installed")
except ImportError:
    print("❌ ChromaDB not found. Installing...")
    import subprocess

    subprocess.check_call(["pip", "install", "chromadb", "langchain-chroma"])
    print("✅ ChromaDB installed successfully")

print("\n🔧 Step 2: Creating vector store from knowledge base...")
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_systems.vector_rag_system import create_vector_store

vectorstore = create_vector_store(force_recreate=True)

if vectorstore:
    print("\n✅ RAG System Setup Complete!")
    print("=" * 60)
    print("\n📊 Vector Store Statistics:")
    print(f"   Location: ./chroma_db")
    print(f"   Collection: albaqer_knowledge_base")
    print("\n💡 You can now use semantic search in your agents!")
    print("\n🧪 Test it:")
    print("   python vector_rag_system.py")
else:
    print("\n❌ Setup failed. Check your database connection and .env file")

print("\n" + "=" * 60)
