# =====================================================
# AlBaqer Stones - Simple RAG System (NO pgvector needed)
# Uses PostgreSQL JSON storage + Python similarity
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
# COSINE SIMILARITY CALCULATION
# =====================================================
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# =====================================================
# SEMANTIC SEARCH (Python-side similarity)
# =====================================================
def semantic_search(query: str, top_k: int = 3, filter_dict: Dict = None) -> List[Dict]:
    """
    Perform semantic search using Python-side similarity calculation
    
    Args:
        query: Search query
        top_k: Number of results to return
        filter_dict: Optional metadata filters
    
    Returns:
        List of relevant documents with similarity scores
    """
    try:
        # Generate embedding for query
        embeddings_model = get_embeddings_model()
        query_embedding = embeddings_model.embed_query(query)
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query with optional filtering
        base_query = """
            SELECT 
                id,
                knowledge_base_id,
                content,
                embedding_json,
                metadata
            FROM knowledge_base_vectors
        """
        
        params = []
        where_clauses = []
        
        # Add metadata filtering
        if filter_dict:
            for key, value in filter_dict.items():
                where_clauses.append(f"metadata->>'{key}' = %s")
                params.append(value)
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        # Execute query to get all vectors
        cur.execute(base_query, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if not results:
            return []
        
        # Calculate similarities in Python
        similarities = []
        for row in results:
            # Parse embedding from JSON
            doc_embedding = json.loads(row['embedding_json'])
            
            # Calculate similarity
            similarity = cosine_similarity(query_embedding, doc_embedding)
            
            metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
            
            similarities.append({
                "id": row['id'],
                "knowledge_base_id": row['knowledge_base_id'],
                "title": metadata.get("title", ""),
                "content": row['content'],
                "category": metadata.get("category", ""),
                "content_type": metadata.get("content_type", ""),
                "target_audience": metadata.get("target_audience", ""),
                "similarity_score": float(similarity),
                "metadata": metadata,
            })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:top_k]
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
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
        sources.append({
            "title": result["title"],
            "category": result["category"],
            "score": result["similarity_score"],
        })
    
    context = "\n".join(context_parts)
    
    return {
        "question": question,
        "context": context,
        "sources": sources,
        "num_sources": len(sources),
    }


# =====================================================
# CREATE VECTORS FOR KNOWLEDGE BASE
# =====================================================
def create_vectors_for_knowledge_base():
    """
    Generate and store vectors for all knowledge base articles
    """
    print("🔄 Creating vectors for knowledge base...")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all knowledge base articles
        cur.execute("""
            SELECT id, title, content, category, content_type, target_audience, language
            FROM knowledge_base
            ORDER BY id
        """)
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
            embedding_json = json.dumps(embedding.tolist())
            
            # Prepare metadata
            metadata = {
                "id": article['id'],
                "title": article['title'],
                "category": article['category'],
                "content_type": article['content_type'],
                "target_audience": article['target_audience'],
                "language": article['language']
            }
            
            # Insert vector
            cur.execute("""
                INSERT INTO knowledge_base_vectors 
                (knowledge_base_id, content, embedding_json, metadata)
                VALUES (%s, %s, %s, %s)
            """, (article['id'], doc_text, embedding_json, json.dumps(metadata)))
        
        conn.commit()
        
        # Verify
        cur.execute("SELECT COUNT(*) as count FROM knowledge_base_vectors")
        count = cur.fetchone()['count']
        
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
    print("AlBaqer Stones - Simple RAG System Test")
    print("=" * 60)
    
    # Test search
    test_queries = [
        "What are the benefits of Aqeeq stone?",
        "Tell me about Islamic gemstones",
        "How do I care for my silver jewelry?"
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
