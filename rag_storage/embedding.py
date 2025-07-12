#!/usr/bin/env python3
"""
Document embedding and indexing library for Ukrainian technical standards RAG system.
Provides functions for creating embeddings and building searchable index from parsed documents.
"""

import os
import json
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def save_embedding_results(index, embedding_results_statistics: dict, index_dir: str, embedding_results_file: str):
    """Save index and embedding statistics, removing old files first."""
    # Remove old embedding statistics file if it exists
    if os.path.exists(embedding_results_file):
        os.remove(embedding_results_file)
        print(f"Removed old embedding statistics file: {embedding_results_file}")
    
    # Calculate final embedding statistics and create text report
    embedding_results_statistics['total_embeddings'] = len(index.vector_store._data.embedding_dict)
    embedding_results_statistics['embeddings_per_page'] = (embedding_results_statistics['total_embeddings'] / embedding_results_statistics['total_pages']) if embedding_results_statistics['total_pages'] > 0 else 0
    embedding_results_statistics['report_text'] = f"""
EMBEDDING REPORT

Model: {embedding_results_statistics['embedding_model']}
Dimensions: {embedding_results_statistics['embedding_dimensions']:,}
Pages for indexing: {embedding_results_statistics['total_pages']:,}
Total embeddings: {embedding_results_statistics['total_embeddings']:,}
Embeddings per page: {embedding_results_statistics['embeddings_per_page']:.1f}
Index directory: {index_dir}
Storage format: LlamaIndex vector store
"""
    
    # Save index
    print(f"Saving index to: {index_dir}...")
    try:
        # Check if parent directory exists and create if needed
        parent_dir = os.path.dirname(index_dir) if os.path.dirname(index_dir) else '.'
        print(f"Parent directory: {parent_dir}")
        print(f"Target index directory: {index_dir}")
        
        # Debug information
        print(f"Parent directory exists: {os.path.exists(parent_dir)}")
        print(f"Parent directory is writable: {os.access(parent_dir, os.W_OK)}")
        print(f"Index directory exists: {os.path.exists(index_dir)}")
        
        os.makedirs(index_dir, exist_ok=True)
        print(f"Index directory created/verified: {index_dir}")
        print(f"Index directory is writable: {os.access(index_dir, os.W_OK)}")
        
        index.storage_context.persist(persist_dir=index_dir)
        print("Index stored successfully!")
    except Exception as e:
        print(f"Error saving index: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise
    
    # Save embedding results statistics to JSON file
    with open(embedding_results_file, 'w', encoding='utf-8') as f:
        json.dump(embedding_results_statistics, f, indent=2, ensure_ascii=False, default=str)
    print(f"Embedding results statistics saved to: {embedding_results_file}")
    
    # Display embedding report
    print(embedding_results_statistics['report_text'])

def build_index(pages_to_index: list, embedding_model: str, index_dir: str, embedding_results_file: str) -> dict:
    embedding_results_statistics = {
        'total_pages': len(pages_to_index),
        'total_embeddings': 0,
        'embeddings_per_page': 0,
        'embedding_model': embedding_model,
        'embedding_dimensions': 0,
        'report_text': '',
    }
    
    print(f"Setting up embedding model: {embedding_model}...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
        print("Embedding model loaded successfully!")
        embedding_results_statistics['embedding_dimensions'] = Settings.embed_model._model.get_sentence_embedding_dimension()
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        raise
    
    print(f"Building index for {embedding_results_statistics['total_pages']} pages...")
    try:
        index = VectorStoreIndex.from_documents(pages_to_index)
        print(f"Index building completed!")
    except Exception as e:
        print(f"Error building index: {e}")
        raise
    
    save_embedding_results(index, embedding_results_statistics, index_dir, embedding_results_file)