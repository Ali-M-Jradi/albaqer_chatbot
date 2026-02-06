#!/usr/bin/env python3
"""
Process all PDFs in knowledge_base folder and add to RAG system
"""

import os
import sys
from pathlib import Path
import PyPDF2
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file"""
    print(f"\n📖 Processing: {os.path.basename(pdf_path)}")

    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"   Pages: {num_pages}")

            text = ""
            for i in range(num_pages):
                try:
                    page = pdf_reader.pages[i]
                    page_text = page.extract_text()
                    text += page_text + "\n\n"
                except Exception as e:
                    print(f"   ⚠️ Error on page {i+1}: {e}")

            print(f"   ✅ Extracted {len(text)} characters")
            return text

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return ""


def process_knowledge_base():
    """Process all PDFs and text files in knowledge_base folder"""

    knowledge_base_path = Path("./knowledge_base")

    if not knowledge_base_path.exists():
        print("❌ knowledge_base folder not found!")
        return

    print("🚀 Processing Knowledge Base Documents")
    print("=" * 50)

    # Find all PDFs
    pdf_files = list(knowledge_base_path.glob("*.pdf"))
    txt_files = list(knowledge_base_path.glob("*.txt"))

    print(f"\nFound {len(pdf_files)} PDF files and {len(txt_files)} text files")

    all_documents = []
    all_metadatas = []

    # Process PDFs
    for pdf_file in pdf_files:
        text = extract_pdf_text(str(pdf_file))
        if text.strip():
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            chunks = text_splitter.split_text(text)

            # Add metadata
            for i, chunk in enumerate(chunks):
                all_documents.append(chunk)
                all_metadatas.append(
                    {"source": pdf_file.name, "type": "pdf", "chunk_id": i}
                )

            print(f"   ✅ Created {len(chunks)} chunks")

    # Process text files
    for txt_file in txt_files:
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()

            print(f"\n📄 Processing: {txt_file.name}")
            print(f"   Characters: {len(text)}")

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            chunks = text_splitter.split_text(text)

            # Add metadata
            for i, chunk in enumerate(chunks):
                all_documents.append(chunk)
                all_metadatas.append(
                    {"source": txt_file.name, "type": "text", "chunk_id": i}
                )

            print(f"   ✅ Created {len(chunks)} chunks")

        except Exception as e:
            print(f"   ❌ Error processing {txt_file.name}: {e}")

    print(f"\n📊 Total chunks created: {len(all_documents)}")

    # Add to vector store
    if all_documents:
        add_to_vector_store(all_documents, all_metadatas)
    else:
        print("❌ No documents to add!")


def add_to_vector_store(documents, metadatas):
    """Add documents to ChromaDB vector store"""

    print("\n🔧 Adding documents to vector store...")

    persist_directory = "./chroma_db"
    collection_name = "albaqer_knowledge_base"

    # Get embedding model
    print("Loading embedding model (all-mpnet-base-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Check if vector store exists
    if os.path.exists(persist_directory):
        print(f"✅ Loading existing vector store from {persist_directory}")

        # Load existing vectorstore
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name,
        )

        # Add new documents
        print(f"Adding {len(documents)} new chunks...")
        vectorstore.add_texts(texts=documents, metadatas=metadatas)

        # Get collection stats
        collection = vectorstore._collection
        total_docs = collection.count()

        print(f"\n✅ Successfully added documents!")
        print(f"📊 Total documents in vector store: {total_docs}")

    else:
        print(f"Creating new vector store at {persist_directory}")

        # Create new vectorstore
        vectorstore = Chroma.from_texts(
            texts=documents,
            embedding=embeddings,
            metadatas=metadatas,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )

        print(f"\n✅ Successfully created vector store!")
        print(f"📊 Total documents: {len(documents)}")


if __name__ == "__main__":
    # Set offline mode for HuggingFace
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    process_knowledge_base()

    print("\n" + "=" * 50)
    print("✅ RAG System Updated Successfully!")
    print("=" * 50)
