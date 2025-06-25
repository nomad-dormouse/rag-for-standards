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

def analyse_parsing(documents):
    """Analyse document parsing statistics."""
    parsing_stats = {
        'total_files_count': 0,
        'empty_files': [],
        'empty_files_count': 0,
        'empty_files_percentage': 0,
        'total_pages_count': len(documents),
        'empty_pages_count': 0,
        'empty_pages_percentage': 0,
        'pages_by_extension': defaultdict(int),
        'pages_per_file': defaultdict(int),
        'page_lengths': defaultdict(list),
        'processing_errors': []
    }
    
    for doc in documents:
        if 'file_name' in doc.metadata:
            file_name = doc.metadata['file_name']
            file_ext = os.path.splitext(file_name)[1].lower()
            parsing_stats['pages_by_extension'][file_ext] += 1
            parsing_stats['pages_per_file'][file_name] += 1
            text_length = len(doc.text.strip())
            parsing_stats['page_lengths'][file_name].append(text_length)
        text_length = len(doc.text.strip())
        if text_length == 0:
            parsing_stats['empty_pages_count'] += 1
    
    parsing_stats['total_files_count'] = len(parsing_stats['pages_per_file'])
    parsing_stats['empty_files'] = [file for file, pages in parsing_stats['page_lengths'].items() 
                                 if all(length == 0 for length in pages)]
    parsing_stats['empty_files_count'] = len(parsing_stats['empty_files'])
    parsing_stats['empty_files_percentage'] = (parsing_stats['empty_files_count'] / parsing_stats['total_files_count'] * 100) if parsing_stats['total_files_count'] > 0 else 0
    parsing_stats['empty_pages_count'] = len(parsing_stats['empty_files'])
    parsing_stats['empty_pages_percentage'] = (parsing_stats['empty_pages_count'] / parsing_stats['total_pages_count'] * 100) if parsing_stats['total_pages_count'] > 0 else 0
    
    return parsing_stats

def analyse_indexing(index):
    """Analyse vector index statistics."""
    index_stats = {}
    index_stats['indexed_docs'] = len(index.docstore.docs)
    index_stats['vector_count'] = len(index.vector_store._data.embedding_dict)
    index_stats['index_size_mb'] = index.storage_context.get_index_size()
    index_stats['embedding_dimensions'] = Settings.embed_model._model.get_sentence_embedding_dimension()
    return index_stats

def generate_report(documents, index):
    """Generate a concise ingestion report by analysing documents and indexing."""

    parsing_stats = analyse_parsing(documents)
    index_stats = analyse_indexing(index)
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")

    report = f"""# INGESTION REPORT

## Documents Parsing Summary
- **Total pages:** {parsing_stats['total_pages_count']:,} from {parsing_stats['total_files_count']:,} files"""
    for ext, count in sorted(parsing_stats['pages_by_extension'].items()):
        percentage = (count / parsing_stats['total_pages_count'] * 100) if parsing_stats['total_pages_count'] > 0 else 0
        report += f" | {ext.upper()}: {count:,} ({percentage:.1f}%)"
    report += f"""
- **Empty pages:** {parsing_stats['empty_pages_percentage']:.1f}% ({parsing_stats['empty_pages_count']:,} pages)
- **Completely empty files:** {parsing_stats['empty_files_percentage']:.1f}% ({parsing_stats['empty_files_count']:,} files)"""
    report += f"\n\n## Vector Index Summary"
    report += f"\n- **Indexed documents:** {index_stats['indexed_docs']:,}"
    report += f"\n- **Vector embeddings:** {index_stats['vector_count']:,}"
    report += f"\n- **Index size:** {index_stats['index_size_mb']:.1f} MB"
    report += f"\n- **Embedding model:** {embedding_model_name}"
    report += f"\n- **Embedding dimensions:** {index_stats['embedding_dimensions']:,}"
    
    report_path = os.path.join(index_dir, report_file_name)
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Ingestion report saved to: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return report

def main():
    
    load_dotenv(override=True)
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    delimiter_length = int(os.getenv("DELIMITER_LENGTH", "60"))
    
    print(f"Loading Ukrainian technical standards from: {standards_dir}...")
    try:
        documents = SimpleDirectoryReader(
            input_dir=standards_dir,
            recursive=True,
            required_exts=[".pdf", ".docx", ".doc"],
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
    report = generate_report(documents, index)
    print("\n" + "="*delimiter_length)
    print(report)

if __name__ == "__main__":
    main()