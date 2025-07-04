#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Orchestrates the complete ingestion pipeline: parsing and embedding stages.
Checks for existing parsed pages and skips parsing if already completed.
"""

import os
from dotenv import load_dotenv
import pickle
from parsing import parse_all_documents
from embedding import build_index

def main():
    """
    Main ingestion pipeline that orchestrates parsing and embedding stages.
    """
    load_dotenv(override=True)
    print("Starting document ingestion pipeline...")
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    min_text_threshold = int(os.getenv("MIN_TEXT_THRESHOLD"))
    delimiter_length = int(os.getenv("DELIMITER_LENGTH"))
    parsing_statistics_file = os.getenv("PARSING_RESULTS_STATISTICS_FILE_NAME")
    parsing_methods_file = os.getenv("PARSING_METHODS_FILE_NAME")
    parsed_pages_file = os.getenv("PARSING_RESULTS_FILE_NAME")
    embedding_statistics_file = os.getenv("EMBEDDING_RESULTS_STATISTICS_FILE_NAME")

    print(f"""{'=' * delimiter_length}
Configuration:
  Standards directory: {standards_dir}
  Index directory: {index_dir}
  Embedding model: {embedding_model_name}
  Min text threshold: {min_text_threshold}
  Parsing statistics file: {parsing_statistics_file}
  Parsing methods file: {parsing_methods_file}
  Parsed pages file: {parsed_pages_file}
  Embedding statistics file: {embedding_statistics_file}""")
    
    # Check if parsed pages already exist
    if parsed_pages_file and os.path.exists(parsed_pages_file):
        print(f"""
STAGE 1: LOADING EXISTING PARSED PAGES
{'-' * delimiter_length}""")
        try:
            with open(parsed_pages_file, 'rb') as f:
                pages_for_indexing = pickle.load(f)
            print(f"✅ Loaded {len(pages_for_indexing)} existing parsed pages from {parsed_pages_file}")
            parsing_results = None  # No parsing results to display
        except Exception as e:
            print(f"❌ Error loading existing parsed pages: {e}")
            print("   Falling back to parsing stage...")
            # Fall back to parsing
            pages_for_indexing = parse_all_documents(standards_dir, min_text_threshold, parsing_statistics_file, parsing_methods_file, parsed_pages_file)
    else:
        print(f"""
STAGE 1: DOCUMENTS PARSING
{'-' * delimiter_length}""")
        pages_for_indexing = parse_all_documents(standards_dir, min_text_threshold, parsing_statistics_file, parsing_methods_file, parsed_pages_file)
        
        if not pages_for_indexing:
            print("❌ No pages with content were found!\nIngestion pipeline failed at parsing stage.")
            return
        
        print(f"✅ Parsing completed successfully!\n   Ready for indexing: {len(pages_for_indexing)} pages")
    
    print(f"""
STAGE 2: VECTOR INDEXING
{'-' * delimiter_length}""")
    build_index(pages_for_indexing, embedding_model_name, index_dir, embedding_statistics_file)
    
    print(f"✅ Indexing completed successfully!")
    
    print(f"""{'=' * delimiter_length}
INGESTION PIPELINE COMPLETED SUCCESSFULLY!
{'=' * delimiter_length}""")

if __name__ == "__main__":
    main() 