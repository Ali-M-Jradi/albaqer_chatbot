# =====================================================
# AlBaqer Stones - Semantic Vector-Based RAG System
# Using ChromaDB for vector similarity search
# =====================================================

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import json

# ChromaDB
import chromadb
from chromadb.config import Settings

# LangChain integrations
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()


# =====================================================
# DATABASE CONNECTION
# =====================================================
def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_stones_store"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


# =====================================================
# EMBEDDING MODEL
# =====================================================
def get_embeddings_model():
    """
    Get embedding model (using HuggingFace - FREE and LOCAL!)
    No API key needed, runs on your computer
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# =====================================================
# STEP 1: LOAD KNOWLEDGE BASE FROM DATABASE
# =====================================================
def load_knowledge_base_from_db() -> List[Document]:
    """Load all knowledge base articles from database as LangChain Documents"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT id, title, content, category, content_type, target_audience, language
            FROM knowledge_base
            ORDER BY id
        """
        )

        results = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to LangChain Documents
        documents = []
        for row in results:
            doc = Document(
                page_content=f"{row['title']}\n\n{row['content']}",
                metadata={
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "content_type": row["content_type"],
                    "target_audience": row["target_audience"],
                    "language": row["language"],
                },
            )
            documents.append(doc)

        print(f"✅ Loaded {len(documents)} documents from knowledge base")
        return documents

    except Exception as e:
        print(f"❌ Error loading knowledge base: {e}")
        return []


# =====================================================
# STEP 2: CREATE VECTOR STORE
# =====================================================
def create_vector_store(force_recreate=False):
    """
    Create ChromaDB vector store from knowledge base
    Args:
        force_recreate: If True, delete existing and recreate
    """
    print("\n🔧 Creating Vector Store...")

    # ChromaDB settings
    persist_directory = "./chroma_db"
    collection_name = "albaqer_knowledge_base"

    # Get embedding model
    embeddings = get_embeddings_model()

    # Check if vector store already exists
    if os.path.exists(persist_directory) and not force_recreate:
        print(f"✅ Loading existing vector store from {persist_directory}")
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )
        return vectorstore

    # Load documents from database
    documents = load_knowledge_base_from_db()

    if not documents:
        print("❌ No documents to create vector store!")
        return None

    # Create vector store
    print(f"🔄 Creating embeddings for {len(documents)} documents...")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_directory,
    )

    print(f"✅ Vector store created and saved to {persist_directory}")
    return vectorstore


# =====================================================
# STEP 3: SEMANTIC SEARCH FUNCTION
# =====================================================
def semantic_search(query: str, top_k: int = 3, filter_dict: Dict = None) -> List[Dict]:
    """
    Perform semantic search on knowledge base

    Args:
        query: Search query
        top_k: Number of results to return
        filter_dict: Optional metadata filters
            e.g., {"content_type": "islamic"} or {"target_audience": "muslim"}

    Returns:
        List of relevant documents with scores
    """
    try:
        # Load vector store
        persist_directory = "./chroma_db"
        collection_name = "albaqer_knowledge_base"
        embeddings = get_embeddings_model()

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

        # Perform similarity search
        if filter_dict:
            results = vectorstore.similarity_search_with_score(
                query=query, k=top_k, filter=filter_dict
            )
        else:
            results = vectorstore.similarity_search_with_score(query=query, k=top_k)

        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append(
                {
                    "title": doc.metadata.get("title", ""),
                    "content": doc.page_content,
                    "category": doc.metadata.get("category", ""),
                    "content_type": doc.metadata.get("content_type", ""),
                    "target_audience": doc.metadata.get("target_audience", ""),
                    "similarity_score": float(score),
                    "metadata": doc.metadata,
                }
            )

        return formatted_results

    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


# =====================================================
# STEP 4: RAG QUERY FUNCTION
# =====================================================
def rag_query(question: str, context_filter: Dict = None) -> Dict[str, Any]:
    """
    Complete RAG pipeline: Retrieve relevant context + Generate answer

    Args:
        question: User's question
        context_filter: Optional metadata filter

    Returns:
        Dictionary with retrieved context and sources
    """
    # Retrieve relevant documents
    results = semantic_search(question, top_k=3, filter_dict=context_filter)

    if not results:
        return {
            "question": question,
            "context": "No relevant information found in knowledge base.",
            "sources": [],
        }

    # Build context from retrieved documents
    context_parts = []
    sources = []

    for idx, result in enumerate(results, 1):
        context_parts.append(f"[Source {idx}] {result['title']}\n{result['content']}\n")
        sources.append(
            {
                "title": result["title"],
                "category": result["category"],
                "score": result["similarity_score"],
            }
        )

    context = "\n".join(context_parts)

    return {
        "question": question,
        "context": context,
        "sources": sources,
        "num_sources": len(sources),
    }


# =====================================================
# STEP 5: ADD NEW DOCUMENTS
# =====================================================
def add_documents_to_vectorstore(new_documents: List[Dict]):
    """
    Add new documents to existing vector store

    Args:
        new_documents: List of dicts with 'title', 'content', 'category', etc.
    """
    persist_directory = "./chroma_db"
    collection_name = "albaqer_knowledge_base"
    embeddings = get_embeddings_model()

    # Load existing vectorstore
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    # Convert to Document objects
    docs = []
    for doc_dict in new_documents:
        doc = Document(
            page_content=f"{doc_dict['title']}\n\n{doc_dict['content']}",
            metadata={
                "title": doc_dict["title"],
                "category": doc_dict.get("category", ""),
                "content_type": doc_dict.get("content_type", "general"),
                "target_audience": doc_dict.get("target_audience", "all"),
                "language": doc_dict.get("language", "en"),
            },
        )
        docs.append(doc)

    # Add to vectorstore
    vectorstore.add_documents(docs)
    print(f"✅ Added {len(docs)} new documents to vector store")


# =====================================================
# USAGE EXAMPLES
# =====================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🕌 AlBaqer Stones - Semantic RAG System")
    print("=" * 60)

    # Step 1: Create vector store (only needed once)
    print("\n📚 Step 1: Creating Vector Store from Knowledge Base...")
    vectorstore = create_vector_store(force_recreate=False)

    if not vectorstore:
        print("❌ Failed to create vector store. Exiting.")
        exit(1)

    # Step 2: Test semantic search
    print("\n" + "=" * 60)
    print("🔍 Step 2: Testing Semantic Search")
    print("=" * 60)

    test_queries = [
        "What is the Islamic significance of Aqeeq stone?",
        "How to care for turquoise jewelry?",
        "Tell me about Zakat on gold",
        "What are the healing properties of emerald?",
        "Lebanese jewelry traditions",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"❓ Query: {query}")
        print("=" * 60)

        results = semantic_search(query, top_k=2)

        for idx, result in enumerate(results, 1):
            print(f"\n📄 Result {idx}:")
            print(f"   Title: {result['title']}")
            print(f"   Category: {result['category']}")
            print(f"   Score: {result['similarity_score']:.4f}")
            print(f"   Preview: {result['content'][:150]}...")

    # Step 3: Test RAG query
    print("\n" + "=" * 60)
    print("🤖 Step 3: Testing Complete RAG Pipeline")
    print("=" * 60)

    rag_result = rag_query("What is the Islamic meaning of wearing Aqeeq rings?")

    print(f"\n❓ Question: {rag_result['question']}")
    print(f"\n📚 Retrieved {rag_result['num_sources']} sources:")
    for source in rag_result["sources"]:
        print(f"   - {source['title']} (score: {source['score']:.4f})")

    print(f"\n📖 Context for LLM:\n{rag_result['context'][:500]}...")

    # Step 4: Test with filters
    print("\n" + "=" * 60)
    print("🎯 Step 4: Testing Filtered Search (Islamic content only)")
    print("=" * 60)

    islamic_results = semantic_search(
        "gemstone benefits", top_k=3, filter_dict={"content_type": "islamic"}
    )

    print(f"\nFound {len(islamic_results)} Islamic articles:")
    for result in islamic_results:
        print(f"   - {result['title']} ({result['category']})")

    print("\n" + "=" * 60)
    print("✅ RAG System Test Complete!")
    print("=" * 60)

    print("\n💡 Usage in your agents:")
    print("   from vector_rag_system import semantic_search, rag_query")
    print("   results = semantic_search('your query here')")
    print("   rag_data = rag_query('your question here')")


# =====================================================
# HELPER FUNCTIONS FOR AGENTS
# =====================================================
def get_rag_context(query: str, max_sources: int = 3) -> str:
    """
    Simple function for agents to get RAG context as string
    """
    results = semantic_search(query, top_k=max_sources)

    if not results:
        return "No relevant information found."

    context_parts = [f"{r['title']}: {r['content']}" for r in results]
    return "\n\n".join(context_parts)


def search_islamic_knowledge(query: str) -> str:
    """
    Search only Islamic content
    """
    results = semantic_search(query, top_k=3, filter_dict={"content_type": "islamic"})
    return json.dumps(results, default=str)
