#!/usr/bin/env python3
"""
Document ingestion script for Ukrainian technical standards RAG system.
Loads documents, creates embeddings, and builds searchable index.
Now supports OCR for scanned and corrupted PDFs.
"""

import os
import sys
import io
import json
import tempfile
import fitz  # PyMuPDF
from contextlib import redirect_stderr
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# OCR imports
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR libraries not available. Install pdf2image, pytesseract, and Pillow for OCR support.")

def extract_text_with_ocr(pdf_path, min_text_threshold=100):
    """
    Extract text from PDF using OCR.
    
    Args:
        pdf_path (str): Path to the PDF file
        min_text_threshold (int): Minimum characters to consider as valid text
    
    Returns:
        list: List of Document objects with extracted text
    """
    if not OCR_AVAILABLE:
        print(f"OCR not available for {pdf_path}")
        return []
    
    try:
        print(f"  Running OCR on {os.path.basename(pdf_path)}...")
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path, dpi=300)
        documents = []
        
        for page_num, page_image in enumerate(pages):
            print(f"    Processing page {page_num + 1}/{len(pages)}")
            
            # Extract text using OCR with multiple language support
            # Supports English, Ukrainian, and Russian
            text = pytesseract.image_to_string(page_image, lang='eng+ukr+rus')
            
            # Only include pages with meaningful text content
            if len(text.strip()) > min_text_threshold:
                # Create a Document object
                doc = Document(
                    text=text,
                    metadata={
                        'file_path': pdf_path,
                        'page_number': page_num + 1,
                        'extraction_method': 'OCR',
                        'source': os.path.basename(pdf_path)
                    }
                )
                documents.append(doc)
            else:
                print(f"      Page {page_num + 1} has insufficient text content (OCR)")
        
        return documents
        
    except Exception as e:
        print(f"  OCR failed for {pdf_path}: {str(e)}")
        return []

def extract_text_with_pymupdf(pdf_path, min_text_threshold=100):
    """
    Extract text from PDF using PyMuPDF, with fallback OCR for problematic pages.
    
    Args:
        pdf_path (str): Path to the PDF file
        min_text_threshold (int): Minimum characters to consider as valid text
    
    Returns:
        list: List of Document objects with extracted text
    """
    try:
        doc = fitz.open(pdf_path)
        documents = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Try to extract text normally first
            text = page.get_text()
            
            # If no text or very little text, try OCR on this page
            if len(text.strip()) < min_text_threshold and OCR_AVAILABLE:
                try:
                    # Convert this specific page to image and OCR it
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.pil_tobytes(format="PNG")
                    
                    # Convert to PIL Image and run OCR with multiple language support
                    with Image.open(io.BytesIO(img_data)) as img:
                        ocr_text = pytesseract.image_to_string(img, lang='eng+ukr+rus')
                        if len(ocr_text.strip()) > len(text.strip()):
                            text = ocr_text
                            extraction_method = 'PyMuPDF+OCR'
                        else:
                            extraction_method = 'PyMuPDF'
                except Exception as ocr_e:
                    print(f"    OCR fallback failed for page {page_num + 1}: {str(ocr_e)}")
                    extraction_method = 'PyMuPDF'
            else:
                extraction_method = 'PyMuPDF'
            
            # Only include pages with meaningful content
            if len(text.strip()) > min_text_threshold:
                document = Document(
                    text=text,
                    metadata={
                        'file_path': pdf_path,
                        'page_number': page_num + 1,
                        'extraction_method': extraction_method,
                        'source': os.path.basename(pdf_path)
                    }
                )
                documents.append(document)
        
        doc.close()
        return documents
        
    except Exception as e:
        print(f"  PyMuPDF extraction failed for {pdf_path}: {str(e)}")
        return []

def process_pdf_with_fallbacks(pdf_file, standards_dir):
    """
    Process a PDF file with multiple fallback strategies.
    
    Args:
        pdf_file (str): Path to PDF file
        standards_dir (str): Base directory for relative paths
    
    Returns:
        tuple: (pages, status, error_details)
    """
    print(f"Processing: {os.path.basename(pdf_file)}")
    
    # Strategy 1: Try LlamaIndex SimpleDirectoryReader (original method)
    try:
        stderr_capture = io.StringIO()
        with redirect_stderr(stderr_capture):
            file_reader = SimpleDirectoryReader(input_files=[pdf_file])
            file_pages = file_reader.load_data()
        
        stderr_output = stderr_capture.getvalue()
        if stderr_output.strip():
            print(f"  {stderr_output.strip()}")
        
        # Check for corruption warnings
        has_corruption_warnings = any(warning in stderr_output.lower() for warning in [
            'invalid root object', 'object not defined', 'possible root found',
            'corrupted', 'damaged', 'invalid pdf', 'malformed pdf',
            'xref', 'trailer', 'startxref'
        ])
        
        if has_corruption_warnings:
            print(f"  Corruption detected, trying alternative extraction...")
            raise Exception("PDF corruption detected")
        
        # Check if we got meaningful content
        total_text_length = sum(len(page.text.strip()) for page in file_pages)
        empty_pages_in_file = sum(1 for page in file_pages if len(page.text.strip()) == 0)
        
        if not file_pages or total_text_length < 100:
            print(f"  No meaningful content extracted, trying OCR...")
            raise Exception("Insufficient text content")
        
        if empty_pages_in_file == len(file_pages) and len(file_pages) > 0:
            print(f"  All pages empty, likely scanned document, trying OCR...")
            raise Exception("All pages empty - likely scanned")
        
        # Success with original method
        return file_pages, 'ParsedSuccessfully', None
        
    except Exception as e:
        original_error = str(e)
        
        # Strategy 2: Try PyMuPDF with OCR fallback
        print(f"  Trying PyMuPDF extraction...")
        pymupdf_pages = extract_text_with_pymupdf(pdf_file)
        
        if pymupdf_pages and len(pymupdf_pages) > 0:
            total_text = sum(len(page.text.strip()) for page in pymupdf_pages)
            if total_text > 100:  # Meaningful content threshold
                return pymupdf_pages, 'ParsedWithPyMuPDF', None
        
        # Strategy 3: Full OCR approach
        if OCR_AVAILABLE:
            print(f"  Trying full OCR extraction...")
            ocr_pages = extract_text_with_ocr(pdf_file)
            
            if ocr_pages and len(ocr_pages) > 0:
                return ocr_pages, 'ParsedWithOCR', None
        
        # All strategies failed
        if 'corrupted' in original_error.lower() or 'corruption' in original_error.lower():
            return [], 'CorruptedPDF', original_error
        elif 'scanned' in original_error.lower() or 'empty' in original_error.lower():
            return [], 'ScannedDocument', original_error
        else:
            return [], 'Exception', original_error

def main():
    '''
    Main function to parse documents, create embeddings, and build a searchable index.
    '''
    print("Starting documents ingestion with OCR support...")
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), override=True)
    standards_dir = os.getenv("STANDARDS_DIR_NAME")
    index_dir = os.getenv("INDEX_DIR_NAME")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    report_file_name = os.getenv("REPORT_FILE_NAME")
    
    # Check OCR availability
    if not OCR_AVAILABLE:
        print("WARNING: OCR libraries not available. Install pdf2image, pytesseract, and Pillow for full PDF support.")
    
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
                'ParsedWithPyMuPDF': {
                    'files_count': 0,
                    'files': []
                },
                'ParsedWithOCR': {
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
    
    all_pages = []
    
    for pdf_file in pdf_files:
        pages, status, error_details = process_pdf_with_fallbacks(pdf_file, standards_dir)
        
        # Record the result
        relative_path = os.path.relpath(pdf_file, standards_dir)
        ingestion_results['parsing']['files'][status]['files'].append(relative_path)
        
        if error_details:
            print(f"  Final status: {status} - {error_details}")
        else:
            print(f"  Final status: {status} - {len(pages)} pages extracted")
        
        all_pages.extend(pages)
    
    # Update counts
    for category in ingestion_results['parsing']['files']:
        ingestion_results['parsing']['files'][category]['files_count'] = len(ingestion_results['parsing']['files'][category]['files'])
    
    # Calculate success metrics
    successful_files = (
        ingestion_results['parsing']['files']['ParsedSuccessfully']['files_count'] +
        ingestion_results['parsing']['files']['ParsedWithPyMuPDF']['files_count'] +
        ingestion_results['parsing']['files']['ParsedWithOCR']['files_count']
    )
    
    total_error_count = (
        ingestion_results['parsing']['files']['CorruptedPDF']['files_count'] +
        ingestion_results['parsing']['files']['EmptyDocument']['files_count'] +
        ingestion_results['parsing']['files']['ScannedDocument']['files_count'] +
        ingestion_results['parsing']['files']['Exception']['files_count']
    )
    
    ingestion_results['parsing']['files_with_parsing_errors_count'] = total_error_count
    ingestion_results['parsing']['successfully_parsed_percentage'] = (successful_files / ingestion_results['parsing']['total_files_count'] * 100) if ingestion_results['parsing']['total_files_count'] > 0 else 0
    ingestion_results['parsing']['total_pages_count'] = len(all_pages)
    
    print(f"Loaded {ingestion_results['parsing']['total_pages_count']} pages from {ingestion_results['parsing']['total_files_count']} files")    
    print(f"Successfully processed {successful_files} files ({ingestion_results['parsing']['successfully_parsed_percentage']:.1f}%)")
    print(f"Encountered {ingestion_results['parsing']['files_with_parsing_errors_count']} files with parsing errors")
    
    # Filter pages for indexing
    pages_for_indexing = [page for page in all_pages if len(page.text.strip()) > 0]
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
- Successfully parsed (original): {ingestion_results['parsing']['files']['ParsedSuccessfully']['files_count']:,}
- Successfully parsed (PyMuPDF): {ingestion_results['parsing']['files']['ParsedWithPyMuPDF']['files_count']:,}
- Successfully parsed (OCR): {ingestion_results['parsing']['files']['ParsedWithOCR']['files_count']:,}
- Total successful files: {successful_files:,} ({ingestion_results['parsing']['successfully_parsed_percentage']:.1f}%)
- Corrupted PDF files: {ingestion_results['parsing']['files']['CorruptedPDF']['files_count']:,}
- Empty files: {ingestion_results['parsing']['files']['EmptyDocument']['files_count']:,}
- Scanned files (failed): {ingestion_results['parsing']['files']['ScannedDocument']['files_count']:,}
- Exception files: {ingestion_results['parsing']['files']['Exception']['files_count']:,}
- Total pages: {ingestion_results['parsing']['total_pages_count']:,}
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