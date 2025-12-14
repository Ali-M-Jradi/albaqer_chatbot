# =====================================================
# Knowledge Base & RAG Tools
# =====================================================

import json
from langchain.tools import tool
from psycopg2.extras import RealDictCursor
from database.connection import get_db_connection

# Import RAG functions
try:
    from vector_rag_system import semantic_search
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


@tool
def get_knowledge_base(topic: str) -> str:
    """
    RAG Tool: Semantic search on knowledge base using vector embeddings.
    Args:
        topic: Topic to search (e.g., 'diamond', 'zakat', 'aqeeq care')
    Returns: Relevant knowledge base articles with semantic similarity
    """
    try:
        if RAG_AVAILABLE:
            # Use semantic vector search
            results = semantic_search(topic, top_k=3)

            if not results:
                return json.dumps({"error": "No relevant information found"})

            # Format results for agent
            formatted = []
            for result in results:
                formatted.append(
                    {
                        "title": result["title"],
                        "content": result["content"],
                        "category": result["category"],
                        "relevance_score": result["similarity_score"],
                    }
                )

            return json.dumps(formatted, default=str)
        else:
            raise Exception("RAG system not available")

    except Exception as e:
        # Fallback to database keyword search
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT title, content, category, target_audience
            FROM knowledge_base
            WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)
               OR category ILIKE %s
               OR title ILIKE %s
            LIMIT 3
        """,
            (topic, f"%{topic}%", f"%{topic}%"),
        )

        results = cur.fetchall()
        cur.close()
        conn.close()

        return json.dumps([dict(row) for row in results], default=str)
