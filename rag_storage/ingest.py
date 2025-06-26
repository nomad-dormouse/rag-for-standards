#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Loads documents, creates embeddings, and builds searchable index.
"""

import os
import sys
import io
import json
from contextlib import redirect_stderr
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def main():
    '''
    Main function to parse documents, create embeddings, and build a searchable index.
    '''
    print("Starting documents ingestion...")
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), override=True)
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    ingestion_results = {
        'parsing': {
            'total_files_count': 0,
            'successfully_parsed_percentage': 0,
            'files_with_parsing_errors_count': 0,
            'files': {
                'ParsedSuccessfully': {
                    'files_count': 0,
                    'files': []
                },
                'CorruptedPDF': {
                    'files_count': 0,
                    'files': []
                },
                'EmptyDocument': {
                    'files_count': 0,
                    'files': []
                },
                'ScannedDocument': {
                    'files_count': 0,
                    'files': []
                },
                'Exception': {
                    'files_count': 0,
                    'files': []
                },
            },
            'total_pages_count': 0,
            'empty_pages_count': 0,
            'empty_pages_percentage': 0,
        },
        'embedding': {
            'total_pages_for_indexing_count': 0,
            'total_embeddings_count': 0,
            'embedding_model_name': embedding_model_name,
            'embedding_dimensions': 0,
        },
        'text_summary': ''
    }
    
    print(f"Loading Ukrainian technical standards from: {standards_dir}...")
    pdf_files = []
    for root, dirs, files in os.walk(standards_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    ingestion_results['parsing']['total_files_count'] = len(pdf_files)
    print(f"Found {ingestion_results['parsing']['total_files_count']} PDF files to process...")
    pages = []
    for pdf_file in pdf_files:
        print(f"Processing: {os.path.basename(pdf_file)}")
        try:
            stderr_capture = io.StringIO()
            with redirect_stderr(stderr_capture):
                file_reader = SimpleDirectoryReader(input_files=[pdf_file])
                file_pages = file_reader.load_data()
            stderr_output = stderr_capture.getvalue()
            if stderr_output.strip():
                print(stderr_output.strip())
            has_corruption_warnings = any(warning in stderr_output.lower() for warning in [
                'invalid root object', 'object not defined', 'possible root found',
                'corrupted', 'damaged', 'invalid pdf', 'malformed pdf',
                'xref', 'trailer', 'startxref'
            ])
            if has_corruption_warnings:
                ingestion_results['parsing']['files']['CorruptedPDF']['files'].append(
                    os.path.relpath(pdf_file, standards_dir)
                )
                print(f"WARNING: corrupted PDF detected - {pdf_file}")
            elif not file_pages:
                ingestion_results['parsing']['files']['EmptyDocument']['files'].append(
                    os.path.relpath(pdf_file, standards_dir)
                )
                print(f"WARNING: no pages extracted from {pdf_file}")
            else:
                empty_pages_in_file = sum(1 for page in file_pages if len(page.text.strip()) == 0)
                if empty_pages_in_file == len(file_pages) and len(file_pages) > 0:
                    ingestion_results['parsing']['files']['ScannedDocument']['files'].append(
                        os.path.relpath(pdf_file, standards_dir)
                    )
                    print(f"WARNING: likely scanned document - {pdf_file}")
                else:
                    ingestion_results['parsing']['files']['ParsedSuccessfully']['files'].append(
                        os.path.relpath(pdf_file, standards_dir)
                    )
                        
            pages.extend(file_pages)
        except Exception as e:
            ingestion_results['parsing']['files']['Exception']['files'].append(
                os.path.relpath(pdf_file, standards_dir)
            )
            print(f"Exception caught for {pdf_file}: {type(e).__name__}: {e}")
    ingestion_results['parsing']['files']['ParsedSuccessfully']['files_count'] = len(ingestion_results['parsing']['files']['ParsedSuccessfully']['files'])
    ingestion_results['parsing']['files']['CorruptedPDF']['files_count'] = len(ingestion_results['parsing']['files']['CorruptedPDF']['files'])
    ingestion_results['parsing']['files']['EmptyDocument']['files_count'] = len(ingestion_results['parsing']['files']['EmptyDocument']['files'])
    ingestion_results['parsing']['files']['ScannedDocument']['files_count'] = len(ingestion_results['parsing']['files']['ScannedDocument']['files'])
    ingestion_results['parsing']['files']['Exception']['files_count'] = len(ingestion_results['parsing']['files']['Exception']['files'])
    total_error_count = ingestion_results['parsing']['files']['CorruptedPDF']['files_count'] + ingestion_results['parsing']['files']['EmptyDocument']['files_count'] + ingestion_results['parsing']['files']['ScannedDocument']['files_count'] + ingestion_results['parsing']['files']['Exception']['files_count']
    ingestion_results['parsing']['files_with_parsing_errors_count'] = total_error_count
    ingestion_results['parsing']['successfully_parsed_files_percentage'] = (ingestion_results['parsing']['files']['ParsedSuccessfully']['files_count'] / ingestion_results['parsing']['total_files_count'] * 100) if ingestion_results['parsing']['total_files_count'] > 0 else 0
    ingestion_results['parsing']['total_pages_count'] = len(pages)
    print(f"Loaded {ingestion_results['parsing']['total_pages_count']} pages from {ingestion_results['parsing']['total_files_count']} files")    
    print(f"Encountered {ingestion_results['parsing']['files_with_parsing_errors_count']} files with parsing errors")
    
    pages_for_indexing = [page for page in pages if len(page.text.strip()) > 0]
    ingestion_results['embedding']['total_pages_for_indexing_count'] = len(pages_for_indexing)
    ingestion_results['parsing']['empty_pages_count'] = ingestion_results['parsing']['total_pages_count'] - ingestion_results['embedding']['total_pages_for_indexing_count']
    ingestion_results['parsing']['empty_pages_percentage'] = (ingestion_results['parsing']['empty_pages_count'] / ingestion_results['parsing']['total_pages_count'] * 100) if ingestion_results['parsing']['total_pages_count'] > 0 else 0
    print(f"Filtered out {ingestion_results['parsing']['empty_pages_count']} empty pages, {ingestion_results['embedding']['total_pages_for_indexing_count']} pages will be indexed")
    if not pages_for_indexing:
        print("No pages with content were found!")
        return
    print(f"Setting up embedding model: {embedding_model_name}...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
        print("Embedding model loaded successfully!")
        ingestion_results['embedding']['embedding_dimensions'] = Settings.embed_model._model.get_sentence_embedding_dimension()
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        raise
    print(f"Building index for {ingestion_results['embedding']['total_pages_for_indexing_count']} pages...")
    try:
        index = VectorStoreIndex.from_documents(pages_for_indexing)
        print(f"Index building completed!")
    except Exception as e:
        print(f"Error building index: {e}")
        raise
    ingestion_results['embedding']['total_embeddings_count'] = len(index.vector_store._data.embedding_dict)
    print(f"Saving index to: {index_dir}...")
    try:
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)
        print("Index built and stored successfully!")
    except Exception as e:
        print(f"Error saving index: {e}")
        raise
    
    print("Generating ingestion report...")
    ingestion_results['text_summary'] = f"""INGESTION REPORT

Files parsing
- Total files: {ingestion_results['parsing']['total_files_count']:,}
- Successfully parsed: {ingestion_results['parsing']['files']['ParsedSuccessfully']['files_count']:,} ({ingestion_results['parsing']['successfully_parsed_percentage']:.1f}%)
- Corrupted PDFs: {ingestion_results['parsing']['files']['CorruptedPDF']['files_count']:,}
- Empty files: {ingestion_results['parsing']['files']['EmptyDocument']['files_count']:,}
- Scanned documents: {ingestion_results['parsing']['files']['ScannedDocument']['files_count']:,}
- Exceptions: {ingestion_results['parsing']['files']['Exception']['files_count']:,}
- Total pages: {ingestion_results['parsing']['total_pages_count']:,} from {ingestion_results['parsing']['total_files_count']:,} files
- Empty pages: {ingestion_results['parsing']['empty_pages_count']:,} ({ingestion_results['parsing']['empty_pages_percentage']:.1f}%)

Vector embeddings
- Total pages for indexing: {ingestion_results['embedding']['total_pages_for_indexing_count']:,}
- Total embeddings: {ingestion_results['embedding']['total_embeddings_count']:,}
- Embedding model: {ingestion_results['embedding']['embedding_model_name']}
- Embedding dimensions: {ingestion_results['embedding']['embedding_dimensions']:,}"""
    if report_file_name:
        try:
            with open(report_file_name, 'w', encoding='utf-8') as f:
                json.dump(ingestion_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"Ingestion report saved to: {report_file_name}")
        except Exception as e:
            print(f"Error saving report: {e}")
    else:
        print("Warning: REPORT_FILE_NAME not set, skipping report file creation")
    print(ingestion_results['text_summary'])

if __name__ == "__main__":
    main()