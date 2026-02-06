#!/usr/bin/env python3
# =====================================================
# Process PDF Documents and Add to RAG System
# =====================================================

import PyPDF2
import os
import sys
from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file"""

    print(f"\n📖 Extracting text from: {os.path.basename(pdf_path)}")

    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            all_text = ""
            for i in range(num_pages):
                try:
                    page = pdf_reader.pages[i]
                    text = page.extract_text()
                    all_text += f"\n\n--- Page {i+1} ---\n\n{text}"
                except Exception as e:
                    print(f"   ⚠️ Error reading page {i+1}: {e}")
                    continue

            print(f"   ✅ Extracted {num_pages} pages, {len(all_text)} characters")
            return all_text

    except Exception as e:
        print(f"   ❌ Error extracting PDF: {e}")
        return ""


def chunk_gia_4cs(text: str, filename: str) -> List[Dict]:
    """
    Intelligently chunk the GIA 4Cs PDF
    Single page document - create focused chunks by topic
    """

    chunks = []

    # Since it's a single-page guide, create one comprehensive chunk
    chunks.append(
        {
            "title": "GIA Diamond 4Cs Grading Guide - Complete Reference",
            "content": text,
            "category": "diamond_grading",
            "metadata": {
                "source": filename,
                "authority": "GIA",
                "stone_type": "diamond",
                "technical_level": "standard",
                "topic": "4Cs_grading",
            },
        }
    )

    # Also create a focused chunk on the 4Cs definition
    if "4Cs" in text or "4C" in text:
        chunks.append(
            {
                "title": "Diamond 4Cs Framework - GIA Standard",
                "content": f"""GIA's 4Cs Framework for Diamond Grading:

{text}

This is the official GIA (Gemological Institute of America) standard for diamond quality assessment, 
covering Cut, Color, Clarity, and Carat Weight - the universal method for assessing diamond quality.""",
                "category": "grading_standards",
                "metadata": {
                    "source": filename,
                    "authority": "GIA",
                    "stone_type": "diamond",
                    "technical_level": "beginner",
                    "topic": "grading_framework",
                },
            }
        )

    return chunks


def chunk_gemological_manual(text: str, filename: str) -> List[Dict]:
    """
    Intelligently chunk the Complete Gemological Reference Manual
    18-page document - create logical chunks by major sections
    """

    chunks = []

    # Define sections based on common gemological manual structure
    section_markers = [
        ("PART 1", "PART 2", "Gemstone Classification and Fundamental Science"),
        ("PART 2", "PART 3", "Precious Stones - Diamond, Ruby, Sapphire, Emerald"),
        ("PART 3", "PART 4", "Semi-Precious Stones - Quartz, Garnet, Tourmaline, etc."),
        ("PART 4", "PART 5", "Enhancements, Synthetics, and Treatments"),
        ("PART 5", None, "Practical Identification and Reference Tables"),
    ]

    # Try to split by parts
    for i, (start_marker, end_marker, section_name) in enumerate(section_markers):
        start_idx = text.find(start_marker)

        if start_idx != -1:
            if end_marker:
                end_idx = text.find(end_marker)
                if end_idx == -1:
                    section_text = text[start_idx:]
                else:
                    section_text = text[start_idx:end_idx]
            else:
                section_text = text[start_idx:]

            if len(section_text) > 100:  # Only add if substantial content
                chunks.append(
                    {
                        "title": f"Gemological Manual - {section_name}",
                        "content": section_text,
                        "category": "gemological_reference",
                        "metadata": {
                            "source": filename,
                            "technical_level": "expert",
                            "section": f"part_{i+1}",
                            "topic": section_name.lower().replace(" ", "_"),
                        },
                    }
                )

    # If no parts found, chunk by page count (every 3-4 pages)
    if not chunks:
        words = text.split()
        chunk_size = 1500  # words per chunk

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunks.append(
                {
                    "title": f"Gemological Manual - Section {i//chunk_size + 1}",
                    "content": chunk_text,
                    "category": "gemological_reference",
                    "metadata": {
                        "source": filename,
                        "technical_level": "expert",
                        "chunk_index": i // chunk_size,
                        "topic": "general_gemology",
                    },
                }
            )

    return chunks


def process_pdfs() -> List[Dict]:
    """Process both PDFs and prepare chunks"""

    docs_path = "../docs"
    all_chunks = []

    # PDF 1: GIA 4Cs Guide
    gia_pdf = os.path.join(docs_path, "GIA_4Cs_Download.pdf")
    if os.path.exists(gia_pdf):
        text = extract_pdf_text(gia_pdf)
        if text:
            chunks = chunk_gia_4cs(text, "GIA_4Cs_Download.pdf")
            all_chunks.extend(chunks)
            print(f"   ✅ Created {len(chunks)} chunks from GIA 4Cs PDF")
    else:
        print(f"   ⚠️ GIA PDF not found: {gia_pdf}")

    # PDF 2: Complete Gemological Manual
    manual_pdf = os.path.join(docs_path, "Complete_Gemological_Reference_Manual.pdf")
    if os.path.exists(manual_pdf):
        text = extract_pdf_text(manual_pdf)
        if text:
            chunks = chunk_gemological_manual(
                text, "Complete_Gemological_Reference_Manual.pdf"
            )
            all_chunks.extend(chunks)
            print(f"   ✅ Created {len(chunks)} chunks from Gemological Manual PDF")
    else:
        print(f"   ⚠️ Manual PDF not found: {manual_pdf}")

    return all_chunks


def add_to_vector_store(chunks: List[Dict]):
    """Add PDF chunks to existing ChromaDB vector store"""

    print(f"\n🔧 Adding {len(chunks)} chunks to vector store...")

    # ChromaDB settings
    persist_directory = "./chroma_db"
    collection_name = "albaqer_knowledge_base"

    # Get embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Check if vector store exists
    if not os.path.exists(persist_directory):
        print("❌ ChromaDB vector store not found. Please run setup_rag.py first!")
        return None

    # Load existing vector store
    print(f"✅ Loading existing vector store from {persist_directory}")
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )

    # Convert chunks to LangChain Documents
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=f"{chunk['title']}\n\n{chunk['content']}",
            metadata={
                "title": chunk["title"],
                "category": chunk["category"],
                **chunk["metadata"],
            },
        )
        documents.append(doc)

    print(f"📝 Adding {len(documents)} documents to vector store...")

    # Add documents to existing vector store
    vectorstore.add_documents(documents)

    print(f"✅ Successfully added {len(documents)} PDF chunks!")
    print(f"📊 Total documents in vector store: {vectorstore._collection.count()}")

    return vectorstore


def test_enhanced_rag(vectorstore):
    """Test the enhanced RAG system with PDF-specific queries"""

    print("\n" + "=" * 70)
    print("TESTING ENHANCED RAG SYSTEM WITH PDF CONTENT")
    print("=" * 70)

    test_queries = [
        "What are the 4Cs according to GIA?",
        "How does GIA grade diamond color?",
        "What is the difference between cut and clarity?",
        "Tell me about carat weight in diamonds",
        "What are the GIA grading standards?",
    ]

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)

        results = vectorstore.similarity_search(query, k=2)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.metadata.get('title', 'Unknown')}")
            print(f"   Category: {result.metadata.get('category', 'N/A')}")
            print(f"   Source: {result.metadata.get('source', 'N/A')}")
            print(f"   Authority: {result.metadata.get('authority', 'N/A')}")
            preview = result.page_content[:200].replace("\n", " ")
            print(f"   Preview: {preview}...")

        print("\n" + "=" * 70)


def main():
    """Main processing function"""

    print("=" * 70)
    print("PDF PROCESSING - ADD TO RAG SYSTEM")
    print("=" * 70)

    # Step 1: Extract and chunk PDFs
    print("\n📖 Step 1: Processing PDF documents...")
    chunks = process_pdfs()

    if not chunks:
        print("\n❌ No chunks created. Please check PDF files.")
        return

    print(f"\n✅ Created {len(chunks)} total chunks from PDFs")

    # Step 2: Add to vector store
    print("\n💾 Step 2: Adding to vector store...")
    vectorstore = add_to_vector_store(chunks)

    if vectorstore:
        # Step 3: Test the enhanced system
        print("\n🧪 Step 3: Testing enhanced RAG system...")
        test_enhanced_rag(vectorstore)

        print("\n" + "=" * 70)
        print("✅ PDF DOCUMENTS SUCCESSFULLY ADDED TO RAG SYSTEM!")
        print("=" * 70)
        print(f"\nAdded Content:")
        print(f"  • GIA 4Cs Diamond Grading Guide (Official)")
        print(f"  • Complete Gemological Reference Manual (18 pages)")
        print(f"  • Total: {len(chunks)} expert-level chunks")
        print(f"\n🎯 Your RAG system now includes authoritative GIA standards!")
    else:
        print("\n❌ Failed to add documents to vector store")


if __name__ == "__main__":
    main()
