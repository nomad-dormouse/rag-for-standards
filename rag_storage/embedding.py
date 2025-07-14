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
    
    # Basic system information
    print(f"Python version: {__import__('sys').version}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        print("Attempting to load embedding model...")
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
        print("Embedding model loaded successfully!")
        embedding_results_statistics['embedding_dimensions'] = Settings.embed_model._model.get_sentence_embedding_dimension()
    except Exception as e:
        print(f"❌ EMBEDDING MODEL LOADING FAILED ❌")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Print more detailed error information
        import traceback
        print("\n" + "="*50)
        print("FULL ERROR TRACEBACK:")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        
        # Check if it's a network/download issue
        if "ConnectionError" in str(type(e)) or "timeout" in str(e).lower():
            print("\n💡 DIAGNOSIS: Network connectivity issue")
            print("   - The model needs to be downloaded from HuggingFace on first use")
            print("   - Check internet connection on remote server")
        elif "No space left on device" in str(e):
            print("\n💡 DIAGNOSIS: Disk space issue")
            print("   - Free up disk space on the remote server")
        elif "MemoryError" in str(type(e)) or "out of memory" in str(e).lower():
            print("\n💡 DIAGNOSIS: Memory issue")
            print("   - Remote server needs more RAM")
        else:
            print(f"\n💡 DIAGNOSIS: Unknown error type: {type(e).__name__}")
        
        print("\n🔧 SUGGESTED FIXES:")
        print("   1. Check remote server internet connection")
        print("   2. Ensure sufficient disk space (>2GB free)")
        print("   3. Ensure sufficient RAM (>2GB available)")
        print("   4. Try running deployment again (model might download on retry)")
        
        raise
    
    print(f"Building index for {embedding_results_statistics['total_pages']} pages...")
    try:
        index = VectorStoreIndex.from_documents(pages_to_index)
        print(f"Index building completed!")
    except Exception as e:
        print(f"Error building index: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise
    
    save_embedding_results(index, embedding_results_statistics, index_dir, embedding_results_file)