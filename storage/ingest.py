#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Loads documents, creates embeddings, and builds searchable index.
"""

import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def main():
    load_dotenv()
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    
    print(f"Loading documents from: {standards_dir}...")
    try:
        documents = SimpleDirectoryReader(
            input_dir=standards_dir,
            recursive=True,
            required_exts=[".pdf"],
            errors='ignore'
        ).load_data()
        print(f"Loaded {len(documents)} document pages")
    except Exception as e:
        print(f"Error loading documents: {e}")
        return
    if not documents:
        print("No documents were loaded successfully!")
        return
    
    print(f"Setting up embedding model: {embedding_model_name}...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
        print("Embedding model loaded successfully!")
    except Exception as e:
        print(f"DETAILED ERROR loading embedding model: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        raise
    
    print("Building index...")
    index = VectorStoreIndex.from_documents(documents)
    
    print(f"Saving index to: {index_dir}...")
    index.storage_context.persist(persist_dir=index_dir)
    
    print("Index built and stored successfully!")

if __name__ == "__main__":
    main()