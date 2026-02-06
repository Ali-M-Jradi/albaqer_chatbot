# =====================================================
# Migrate ChromaDB to PostgreSQL pgvector
# =====================================================

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
import json

load_dotenv()


def get_db_connection():
    """Create PostgreSQL connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "albaqer_gemstone_ecommerce_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "po$7Gr@s$"),
    )


def migrate_chromadb_to_postgres():
    """
    Read embeddings from ChromaDB and insert into PostgreSQL
    """
    print("🔄 Starting migration from ChromaDB to PostgreSQL...")

    # Step 1: Check if ChromaDB exists
    if not os.path.exists("./chroma_db"):
        print(
            "❌ ChromaDB folder not found! Please create vectors first using vector_rag_system.py"
        )
        return False

    # Step 2: Load ChromaDB collection
    try:
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_collection(name="albaqer_knowledge_base")
    except Exception as e:
        print(f"❌ Error loading ChromaDB: {e}")
        return False

    # Get all data from ChromaDB
    results = collection.get(include=["embeddings", "metadatas", "documents"])

    if not results["ids"]:
        print("❌ No data found in ChromaDB!")
        return False

    print(f"✅ Found {len(results['ids'])} documents in ChromaDB")

    # Step 3: Connect to PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return False

    # Step 4: Prepare data for insertion
    insert_data = []
    for i in range(len(results["ids"])):
        metadata = results["metadatas"][i]
        embedding = results["embeddings"][i]
        content = results["documents"][i]

        # Get knowledge_base_id from metadata
        kb_id = metadata.get("id")

        # Convert embedding to PostgreSQL vector format
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        insert_data.append((kb_id, content, embedding_str, json.dumps(metadata)))

    # Step 5: Clear existing vectors (optional)
    print("🗑️  Clearing existing vectors...")
    cur.execute("DELETE FROM knowledge_base_vectors")

    # Step 6: Batch insert into PostgreSQL
    print(f"📥 Inserting {len(insert_data)} vectors into PostgreSQL...")

    insert_query = """
        INSERT INTO knowledge_base_vectors 
        (knowledge_base_id, content, embedding_json, metadata)
        VALUES (%s, %s, %s, %s)
    """

    try:
        execute_batch(cur, insert_query, insert_data, page_size=100)
        conn.commit()
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False

    # Step 7: Verify migration
    cur.execute("SELECT COUNT(*) FROM knowledge_base_vectors")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"✅ Migration complete! {count} vectors inserted into PostgreSQL")
    print("🎉 You can now delete the ./chroma_db folder if you want")
    print("💡 Run vector_rag_pgvector.py to test the new system")

    return True


if __name__ == "__main__":
    try:
        success = migrate_chromadb_to_postgres()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
