#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Orchestrates the complete ingestion pipeline: parsing and embedding stages.
"""

import os
import json
from dotenv import load_dotenv
from parsing import parse_all_documents
from embedding import build_index

def save_ingestion_report(ingestion_results: dict, report_file_name: str) -> str:
    parsing_report_text = ingestion_results['parsing']['report_text']
    embedding_report_text = ingestion_results['embedding']['report_text']
    full_report_text = parsing_report_text + embedding_report_text
    
    try:
        with open(report_file_name, 'w', encoding='utf-8') as f:
            json.dump(ingestion_results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Ingestion report saved to: {report_file_name}")
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return full_report_text

def main():
    """
    Main ingestion pipeline that orchestrates parsing and embedding stages.
    """
    load_dotenv()
    print("Starting document ingestion pipeline...")
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    min_text_threshold = int(os.getenv("MIN_TEXT_THRESHOLD"))
    delimiter_length = int(os.getenv("DELIMITER_LENGTH"))

    print(f"""{'=' * delimiter_length}
Configuration:
  Standards directory: {standards_dir}
  Index directory: {index_dir}
  Embedding model: {embedding_model_name}
  Report file: {report_file_name}
  Min text threshold: {min_text_threshold}""")
    
    # Stage 1: Parse all PDFs
    print(f"""
STAGE 1: PDF PARSING
{'-' * delimiter_length}""")
    pages_for_indexing, parsing_results = parse_all_documents(standards_dir, min_text_threshold)
    
    if not pages_for_indexing:
        print("❌ No pages with content were found!\nIngestion pipeline failed at parsing stage.")
        return
    
    print(f"✅ Parsing completed successfully!\n   Ready for indexing: {len(pages_for_indexing)} pages")
    
    # Stage 2: Build vector index
    print(f"""
STAGE 2: VECTOR INDEXING
{'-' * delimiter_length}""")
    embedding_results = build_index(pages_for_indexing, embedding_model_name, index_dir)
    
    print(f"✅ Indexing completed successfully!\n   Total embeddings created: {embedding_results['total_embeddings']:,}")
    
    # Save report
    ingestion_results = {
        'parsing': parsing_results,
        'embedding': embedding_results,
        'report_text': '',
    }
    print(f"""
SAVING FINAL REPORT
{'-' * delimiter_length}""")
    ingestion_results['report_text'] = save_ingestion_report(ingestion_results, report_file_name)
    print(f"""{'=' * delimiter_length}
INGESTION PIPELINE COMPLETED SUCCESSFULLY!
{'=' * delimiter_length}""")
    print(ingestion_results['report_text'])

if __name__ == "__main__":
    main() 