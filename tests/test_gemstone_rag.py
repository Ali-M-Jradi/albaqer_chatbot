# Test the enhanced RAG system with gemstone questions
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_systems.vector_rag_system import semantic_search

print("\n" + "=" * 60)
print("TESTING ENHANCED RAG SYSTEM WITH GEMSTONE KNOWLEDGE")
print("=" * 60)

test_queries = [
    "How can I tell if a ruby is real or synthetic?",
    "What are the 4 C's of diamond grading?",
    "How should I care for my emerald jewelry?",
    "What makes a sapphire valuable?",
    "How to identify a high quality diamond?",
]

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 60)

    results = semantic_search(query, top_k=2)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Category: {result['category']}")
        print(f"   Similarity: {result['similarity_score']:.2%}")
        print(f"   Preview: {result['content'][:150]}...")

    print("\n" + "=" * 60)
