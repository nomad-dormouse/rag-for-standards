#!/usr/bin/env python3
"""
Script to run only the embedding stage using pre-parsed pages.
"""

import os
import pickle
from dotenv import load_dotenv
from embedding import build_index

def load_parsed_pages(input_file: str):
    """Load parsed pages from pickle file."""
    with open(input_file, 'rb') as f:
        pages = pickle.load(f)
    print(f"📂 Loaded {len(pages)} parsed pages from: {input_file}")
    return pages

def main():
    """Run embedding on pre-parsed pages."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    index_dir = os.getenv("INDEX_DIR_NAME", "index")
    delimiter_length = int(os.getenv("DELIMITER_LENGTH", "100"))
    parsed_pages_file = "parsed_pages.pkl"
    
    print("Running Embedding Stage Only")
    print("=" * delimiter_length)
    print(f"Embedding model: {embedding_model_name}")
    print(f"Index directory: {index_dir}")
    print(f"Parsed pages file: {parsed_pages_file}")
    print()
    
    # Check if parsed pages file exists
    if not os.path.exists(parsed_pages_file):
        print(f"❌ Parsed pages file '{parsed_pages_file}' not found")
        print("Please run parsing first using test_parsing_locally.py")
        return False
    
    # Load parsed pages
    try:
        pages = load_parsed_pages(parsed_pages_file)
        
        if not pages:
            print("❌ No pages found in parsed pages file")
            return False
        
        print(f"✅ Ready to embed {len(pages)} pages")
        print()
        
        # Run embedding
        print("STAGE: VECTOR INDEXING")
        print("-" * delimiter_length)
        
        embedding_results = build_index(pages, embedding_model_name, index_dir)
        
        print(f"✅ Indexing completed successfully!")
        print(f"   Total embeddings created: {embedding_results['total_embeddings']:,}")
        print()
        print("=" * delimiter_length)
        print("EMBEDDING COMPLETED SUCCESSFULLY!")
        print("=" * delimiter_length)
        print(embedding_results['report_text'])
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 