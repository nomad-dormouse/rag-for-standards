#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Loads documents, creates embeddings, and builds searchable index.
"""

import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def generate_report(documents, index):
    """Generate a concise ingestion report by analysing documents and indexing."""
    report = {
        'parsing': {
            'total_files_count': 0,
            'empty_files': [],
            'empty_files_count': 0,
            'empty_files_percentage': 0,
            'total_pages_count': len(documents),
            'empty_pages_count': 0,
            'empty_pages_percentage': 0,
            'pages_per_file': defaultdict(int),
            'page_lengths': defaultdict(list),
        },
        'indexing': {
            'vector_count': len(index.vector_store._data.embedding_dict),
            'embedding_model_name': os.getenv("EMBEDDING_MODEL_NAME"),
            'embedding_dimensions': Settings.embed_model._model.get_sentence_embedding_dimension(),
        },
        'text_summary': ''
    }
    
    for doc in documents:
        if 'file_name' in doc.metadata:
            file_name = doc.metadata['file_name']
            file_ext = os.path.splitext(file_name)[1].lower()
            report['parsing']['pages_per_file'][file_name] += 1
            text_length = len(doc.text.strip())
            report['parsing']['page_lengths'][file_name].append(text_length)
        text_length = len(doc.text.strip())
        if text_length == 0:
            report['parsing']['empty_pages_count'] += 1
    
    report['parsing']['total_files_count'] = len(report['parsing']['pages_per_file'])
    report['parsing']['empty_files'] = [file for file, pages in report['parsing']['page_lengths'].items() 
                                 if all(length == 0 for length in pages)]
    report['parsing']['empty_files_count'] = len(report['parsing']['empty_files'])
    report['parsing']['empty_files_percentage'] = (report['parsing']['empty_files_count'] / report['parsing']['total_files_count'] * 100) if report['parsing']['total_files_count'] > 0 else 0
    report['parsing']['empty_pages_percentage'] = (report['parsing']['empty_pages_count'] / report['parsing']['total_pages_count'] * 100) if report['parsing']['total_pages_count'] > 0 else 0

    report['text_summary'] = f"""INGESTION REPORT
- Total pages: {report['parsing']['total_pages_count']:,} from {report['parsing']['total_files_count']:,} files
- Empty pages: {report['parsing']['empty_pages_percentage']:.1f}% ({report['parsing']['empty_pages_count']:,} pages)
- Completely empty files: {report['parsing']['empty_files_percentage']:.1f}% ({report['parsing']['empty_files_count']:,} files)
- Vector embeddings: {report['indexing']['vector_count']:,}
- Embedding model: {report['indexing']['embedding_model_name']}
- Embedding dimensions: {report['indexing']['embedding_dimensions']:,}"""
    
    storage_dir = os.getenv("STORAGE_DIR_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    report_path = os.path.join(storage_dir, report_file_name)
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print(f"Ingestion report saved as JSON to: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return report['text_summary']

def main():
    
    load_dotenv(override=True)
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    delimiter_length = int(os.getenv("DELIMITER_LENGTH", "60"))
    
    print(f"Loading Ukrainian technical standards from: {standards_dir}...")
    try:
        all_documents = SimpleDirectoryReader(
            input_dir=standards_dir,
            recursive=True,
            required_exts=[".pdf"],
            errors='ignore'
        ).load_data()
        print(f"Loaded {len(all_documents)} document pages")
        documents = [doc for doc in all_documents if len(doc.text.strip()) > 0]
        empty_pages_filtered = len(all_documents) - len(documents)
        print(f"Filtered out {empty_pages_filtered} empty pages, {len(documents)} pages will be indexed")
    except Exception as e:
        print(f"Error loading documents: {e}")
        return
    if not documents:
        print("No documents with content were found!")
        return
    
    print(f"Setting up embedding model: {embedding_model_name}...")
    try:
        Settings.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
        print("Embedding model loaded successfully!")
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        raise
    
    print(f"Building index for {len(documents)} documents...")
    try:
        index = VectorStoreIndex.from_documents(documents)
        print(f"Index building completed!")
    except Exception as e:
        print(f"Error building index: {e}")
        raise
    
    print(f"Saving index to: {index_dir}...")
    try:
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)
        print("Index built and stored successfully!")
    except Exception as e:
        print(f"Error saving index: {e}")
        raise
    
    print("Generating ingestion report...")
    text_summary = generate_report(all_documents, index)
    print(text_summary)

if __name__ == "__main__":
    main()