#!/usr/bin/env python3
"""
Document embedding and indexing library for Ukrainian technical standards RAG system.
Provides functions for creating embeddings and building searchable index from parsed documents.
"""

import os
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def build_index(pages: list, embedding_model: str, index_dir: str) -> dict:
    embedding_results = {
        'total_pages': len(pages),
        'total_embeddings': 0,
        'embedding_model': embedding_model,
        'embedding_dimensions': 0,
        'report_text': '',
    }
    
    print(f"Setting up embedding model: {embedding_model}...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
        print("Embedding model loaded successfully!")
        embedding_results['embedding_dimensions'] = Settings.embed_model._model.get_sentence_embedding_dimension()
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        raise
    
    print(f"Building index for {embedding_results['total_pages']} pages...")
    try:
        index = VectorStoreIndex.from_documents(pages)
        print(f"Index building completed!")
    except Exception as e:
        print(f"Error building index: {e}")
        raise
    
    embedding_results['total_embeddings'] = len(index.vector_store._data.embedding_dict)
    embedding_results['embeddings_per_page'] = (embedding_results['total_embeddings'] / embedding_results['total_pages']) if embedding_results['total_pages'] > 0 else 0
    
    print(f"Saving index to: {index_dir}...")
    try:
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)
        print("Index built and stored successfully!")
    except Exception as e:
        print(f"Error saving index: {e}")
        raise
    
    embedding_results['report_text'] = f"""
EMBEDDING REPORT

Model: {embedding_results['embedding_model']}
Dimensions: {embedding_results['embedding_dimensions']:,}
Pages for indexing: {embedding_results['total_pages']:,}
Total embeddings: {embedding_results['total_embeddings']:,}
Embeddings per page: {embedding_results['embeddings_per_page']:.1f}
Index directory: {index_dir}
Storage format: LlamaIndex vector store
"""
    
    return embedding_results