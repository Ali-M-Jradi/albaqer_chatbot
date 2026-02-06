"""
Test script to diagnose agate identification issues
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from rag_systems.vector_rag_system import semantic_search, expand_query

# Test queries that should work for agate
test_queries = [
    "agate",
    "yemeni agate",
    "red agate carnelian",
    "banded agate",
    "moss agate",
    "agate properties characteristics grading identification",
]

print("=" * 70)
print("AGATE RAG SYSTEM DIAGNOSTIC TEST")
print("=" * 70)

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    # Show query expansion
    expanded = expand_query(query)
    print(f"\nExpanded query: {expanded}")

    # Perform search
    results = semantic_search(query, top_k=5)

    print(f"\nResults found: {len(results)}")

    if results:
        for i, result in enumerate(results, 1):
            score = result.get("similarity_score", 0)
            content = result.get("content", "")[:200]
            source = result.get("metadata", {}).get("source", "Unknown")

            print(f"\n--- Result {i} (Score: {score:.4f}) ---")
            print(f"Source: {source}")
            print(f"Content preview: {content}...")

            # Check if score is too low
            if score > 0.5:
                print("✅ Good relevance score")
            else:
                print("⚠️ Low relevance score - might be filtered out")
    else:
        print("❌ NO RESULTS FOUND - This is the problem!")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
