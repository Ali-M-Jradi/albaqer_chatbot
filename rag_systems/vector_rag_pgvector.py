# =====================================================
# AlBaqer Stones - Vector RAG with PostgreSQL pgvector
# Replaces ChromaDB with PostgreSQL native vectors
# =====================================================

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import json
import numpy as np

from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()


# =====================================================
# DATABASE CONNECTION
# =====================================================
def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_gemstone_ecommerce_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "po$7Gr@s$"),
    )


# =====================================================
# EMBEDDING MODEL
# =====================================================
def get_embeddings_model():
    """Get embedding model (HuggingFace - FREE and LOCAL!)"""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# =====================================================
# SEMANTIC SEARCH WITH PGVECTOR
# =====================================================
def semantic_search(query: str, top_k: int = 3, filter_dict: Dict = None) -> List[Dict]:
    """
    Perform semantic search using PostgreSQL pgvector

    Args:
        query: Search query
        top_k: Number of results to return
        filter_dict: Optional metadata filters (e.g., {"content_type": "islamic"})

    Returns:
        List of relevant documents with similarity scores
    """
    try:
        # Generate embedding for query
        embeddings_model = get_embeddings_model()
        query_embedding = embeddings_model.embed_query(query)

        # Convert to PostgreSQL vector format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with optional filtering
        base_query = """
            SELECT 
                kbv.id,
                kbv.knowledge_base_id,
                kbv.content,
                kbv.metadata,
                1 - (kbv.embedding <=> %s::vector) as similarity
            FROM knowledge_base_vectors kbv
        """

        params = [embedding_str]
        where_clauses = []

        # Add metadata filtering
        if filter_dict:
            for key, value in filter_dict.items():
                where_clauses.append(f"kbv.metadata->>'{key}' = %s")
                params.append(value)

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += """
            ORDER BY kbv.embedding <=> %s::vector
            LIMIT %s
        """
        params.append(embedding_str)
        params.append(top_k)

        # Execute query
        cur.execute(base_query, params)
        results = cur.fetchall()

        cur.close()
        conn.close()

        # Format results
        formatted_results = []
        for row in results:
            metadata = (
                row["metadata"]
                if isinstance(row["metadata"], dict)
                else json.loads(row["metadata"])
            )
            formatted_results.append(
                {
                    "id": row["id"],
                    "knowledge_base_id": row["knowledge_base_id"],
                    "title": metadata.get("title", ""),
                    "content": row["content"],
                    "category": metadata.get("category", ""),
                    "content_type": metadata.get("content_type", ""),
                    "target_audience": metadata.get("target_audience", ""),
                    "similarity_score": float(row["similarity"]),
                    "metadata": metadata,
                }
            )

        return formatted_results

    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


# =====================================================
# RAG QUERY FUNCTION
# =====================================================
def rag_query(question: str, context_filter: Dict = None) -> Dict[str, Any]:
    """
    Complete RAG pipeline: Retrieve relevant context

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
# INITIAL SETUP: Create vectors for knowledge base
# =====================================================
def create_vectors_for_knowledge_base():
    """
    Generate and store vectors for all knowledge base articles
    Should be run once or when knowledge base is updated
    """
    print("🔄 Creating vectors for knowledge base...")

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get all knowledge base articles
        cur.execute(
            """
            SELECT id, title, content, category, content_type, target_audience, language
            FROM knowledge_base
            ORDER BY id
        """
        )
        articles = cur.fetchall()

        if not articles:
            print("❌ No articles found in knowledge_base table")
            cur.close()
            conn.close()
            return

        print(f"✅ Found {len(articles)} articles")

        # Get embedding model
        embeddings_model = get_embeddings_model()

        # Clear existing vectors
        cur.execute("DELETE FROM knowledge_base_vectors")
        conn.commit()

        # Process each article
        for idx, article in enumerate(articles, 1):
            print(f"Processing article {idx}/{len(articles)}: {article['title']}")

            # Create document text
            doc_text = f"{article['title']}\n\n{article['content']}"

            # Generate embedding
            embedding = embeddings_model.embed_query(doc_text)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            # Prepare metadata
            metadata = {
                "id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "content_type": article["content_type"],
                "target_audience": article["target_audience"],
                "language": article["language"],
            }

            # Insert vector
            cur.execute(
                """
                INSERT INTO knowledge_base_vectors 
                (knowledge_base_id, content, embedding, metadata)
                VALUES (%s, %s, %s::vector, %s)
            """,
                (article["id"], doc_text, embedding_str, json.dumps(metadata)),
            )

        conn.commit()

        # Verify
        cur.execute("SELECT COUNT(*) as count FROM knowledge_base_vectors")
        count = cur.fetchone()["count"]

        cur.close()
        conn.close()

        print(f"✅ Created {count} vectors successfully!")

    except Exception as e:
        print(f"❌ Error creating vectors: {e}")
        import traceback

        traceback.print_exc()


# =====================================================
# EXAMPLE USAGE
# =====================================================
if __name__ == "__main__":
    print("=" * 60)
    print("AlBaqer Stones - pgvector RAG System Test")
    print("=" * 60)

    # Test search
    test_queries = [
        "What are the benefits of Aqeeq stone?",
        "Tell me about Islamic gemstones",
        "How do I care for my silver jewelry?",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 60)

        results = semantic_search(query, top_k=3)

        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title']}")
                print(f"   Score: {result['similarity_score']:.4f}")
                print(f"   Category: {result['category']}")
                print(f"   Content: {result['content'][:150]}...")
        else:
            print("No results found")

        print()
