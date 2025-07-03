#!/usr/bin/env python3
"""
PDF, DOC, DOCX parsing module for Ukrainian technical standards RAG system.
Handles PDF text extraction with OCR fallback support.
Supports Ukrainian, Russian, and English languages.
"""

import os
import io
import fitz
from contextlib import redirect_stderr
from llama_index.core import SimpleDirectoryReader, Document
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def extract_text_with_reader(pdf_path: str, min_text_threshold: int) -> tuple[list[Document], str]:
    try:
        stderr_capture = io.StringIO()
        with redirect_stderr(stderr_capture):
            file_reader = SimpleDirectoryReader(input_files=[pdf_path])
            file_pages = file_reader.load_data()
        stderr_output = stderr_capture.getvalue()
        if stderr_output.strip():
            print(f"  {stderr_output.strip()}")
        
        has_corruption_warnings = any(warning in stderr_output.lower() for warning in [
            'invalid root object', 'object not defined', 'possible root found',
            'corrupted', 'damaged', 'invalid pdf', 'malformed pdf',
            'xref', 'trailer', 'startxref'
        ])
        if has_corruption_warnings:
            print(f"  Corruption detected, trying alternative extraction...")
            raise Exception("PDF corruption detected")
        
        total_text_length = sum(len(page.text.strip()) for page in file_pages)
        empty_pages_in_file = sum(1 for page in file_pages if len(page.text.strip()) == 0)
        if not file_pages or total_text_length < min_text_threshold:
            print(f"  No meaningful content extracted, trying OCR...")
            raise Exception("Insufficient text content")
        if empty_pages_in_file == len(file_pages) and len(file_pages) > 0:
            print(f"  All pages empty, likely scanned document, trying OCR...")
            raise Exception("All pages empty - likely scanned")
        
        return file_pages, None
        
    except Exception as e:
        return [], str(e)

def extract_text_with_pymupdf(pdf_path: str, min_text_threshold: int) -> list[Document]:
    try:
        doc = fitz.open(pdf_path)
        documents = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if len(text.strip()) < min_text_threshold:
                try:
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.pil_tobytes(format="PNG")
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

def extract_text_with_ocr(pdf_path: str, min_text_threshold: int) -> list[Document]:
    try:
        print(f"  Running OCR on {os.path.basename(pdf_path)}...")
        pages = convert_from_path(pdf_path, dpi=300)
        documents = []
        
        for page_num, page_image in enumerate(pages):
            print(f"    Processing page {page_num + 1}/{len(pages)}")
            text = pytesseract.image_to_string(page_image, lang='eng+ukr+rus')
            if len(text.strip()) > min_text_threshold:
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

def process_document_with_fallbacks(document_path: str, min_text_threshold: int) -> tuple[list[Document], str, str]:
    print(f"Processing: {os.path.basename(document_path)}")
    
    # Strategy 1: Try LlamaIndex SimpleDirectoryReader (works for PDF, DOC, DOCX)
    file_pages, error_message = extract_text_with_reader(document_path, min_text_threshold)
    if file_pages:
        return file_pages, 'ParsedWithReader', None
    
    # For PDF files only, try additional fallback strategies
    if document_path.lower().endswith('.pdf'):
        original_error = error_message
        
        # Strategy 2: Try alternative PDF parser (PyMuPDF)
        print(f"  Trying PyMuPDF extraction...")
        pymupdf_pages = extract_text_with_pymupdf(document_path, min_text_threshold)
        if pymupdf_pages and len(pymupdf_pages) > 0:
            total_text = sum(len(page.text.strip()) for page in pymupdf_pages)
            if total_text > min_text_threshold:
                return pymupdf_pages, 'ParsedWithPyMuPDF', None
        
        # Strategy 3: Full OCR processing
        print(f"  Trying full OCR processing...")
        ocr_pages = extract_text_with_ocr(document_path, min_text_threshold)
        if ocr_pages and len(ocr_pages) > 0:
            return ocr_pages, 'ParsedWithOCR', None
        
        # All strategies failed
        if 'corrupted' in original_error.lower() or 'corruption' in original_error.lower():
            return [], 'Corrupted', original_error
        elif 'scanned' in original_error.lower() or 'empty' in original_error.lower():
            return [], 'Scanned', original_error
        else:
            return [], 'Exception', original_error
    else:
        # For non-PDF files, if LlamaIndex failed, mark as exception
        return [], 'Exception', error_message

def parse_all_documents(standards_dir: str, min_text_threshold: int) -> tuple[list[Document], dict]:
    parsing_results = {
        'files_statistics': {
            'total_loaded': 0,
            'total_pdf_loaded': 0,
            'total_doc_loaded': 0,
            'total_docx_loaded': 0,
            'parsed_successfully': 0,
            'parsed_successfully_percentage': 0,
            'failed_to_parse': 0,
            'failed_to_parse_percentage': 0,
            'files': {
                'ParsedWithReader': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'ParsedWithPyMuPDF': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'ParsedWithOCR': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'Corrupted': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'Scanned': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'Empty': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'Exception': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
            }
        },
        'pages_statistics': {
            'total_loaded': 0,
            'not_empty': 0,
            'not_empty_percentage': 0,
            'empty': 0,
            'empty_percentage': 0,
        },
        'report_text': '',
    }
    
    print(f"Loading Ukrainian technical standards from: {standards_dir}...")
    files = []
    for root, dirs, dir_files in os.walk(standards_dir):
        for file in dir_files:
            if file.lower().endswith(('.pdf', '.doc', '.docx')):
                files.append(os.path.join(root, file))
    parsing_results['files_statistics']['total_loaded'] = len(files)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    doc_files = [f for f in files if f.lower().endswith('.doc')]
    docx_files = [f for f in files if f.lower().endswith('.docx')]
    parsing_results['files_statistics']['total_pdf_loaded'] = len(pdf_files)
    parsing_results['files_statistics']['total_doc_loaded'] = len(doc_files)
    parsing_results['files_statistics']['total_docx_loaded'] = len(docx_files)
    print(f"Found {parsing_results['files_statistics']['total_loaded']} files to process: {len(pdf_files)} PDF, {len(doc_files)} DOC, {len(docx_files)} DOCX")
    
    all_pages = []
    for file in files:
        pages, status, error_details = process_document_with_fallbacks(file, min_text_threshold)
        relative_path = os.path.relpath(file, standards_dir)
        parsing_results['files_statistics']['files'][status]['files'].append(relative_path)
        if error_details:
            print(f"  Final status: {status} - {error_details}")
        else:
            print(f"  Final status: {status} - {len(pages)} pages extracted")
        all_pages.extend(pages)
    parsing_results['pages_statistics']['total_loaded'] = len(all_pages)
    print(f"Loaded {parsing_results['pages_statistics']['total_loaded']} pages from {parsing_results['files_statistics']['total_loaded']} files")
    
    parsing_results['files_statistics']['files']['ParsedWithReader']['count'] = len(parsing_results['files_statistics']['files']['ParsedWithReader']['files'])
    parsing_results['files_statistics']['files']['ParsedWithReader']['percentage'] = (parsing_results['files_statistics']['files']['ParsedWithReader']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['count'] = len(parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['files'])
    parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['percentage'] = (parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['ParsedWithOCR']['count'] = len(parsing_results['files_statistics']['files']['ParsedWithOCR']['files'])
    parsing_results['files_statistics']['files']['ParsedWithOCR']['percentage'] = (parsing_results['files_statistics']['files']['ParsedWithOCR']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['parsed_successfully'] = parsing_results['files_statistics']['files']['ParsedWithReader']['count'] + parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['count'] + parsing_results['files_statistics']['files']['ParsedWithOCR']['count']
    parsing_results['files_statistics']['parsed_successfully_percentage'] = (parsing_results['files_statistics']['parsed_successfully'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['Corrupted']['count'] = len(parsing_results['files_statistics']['files']['Corrupted']['files'])
    parsing_results['files_statistics']['files']['Corrupted']['percentage'] = (parsing_results['files_statistics']['files']['Corrupted']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['Scanned']['count'] = len(parsing_results['files_statistics']['files']['Scanned']['files'])
    parsing_results['files_statistics']['files']['Scanned']['percentage'] = (parsing_results['files_statistics']['files']['Scanned']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['Empty']['count'] = len(parsing_results['files_statistics']['files']['Empty']['files'])
    parsing_results['files_statistics']['files']['Empty']['percentage'] = (parsing_results['files_statistics']['files']['Empty']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['files']['Exception']['count'] = len(parsing_results['files_statistics']['files']['Exception']['files'])
    parsing_results['files_statistics']['files']['Exception']['percentage'] = (parsing_results['files_statistics']['files']['Exception']['count'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    parsing_results['files_statistics']['failed_to_parse'] = parsing_results['files_statistics']['files']['Corrupted']['count'] + parsing_results['files_statistics']['files']['Scanned']['count'] + parsing_results['files_statistics']['files']['Empty']['count'] + parsing_results['files_statistics']['files']['Exception']['count']
    parsing_results['files_statistics']['failed_to_parse_percentage'] = (parsing_results['files_statistics']['failed_to_parse'] / parsing_results['files_statistics']['total_loaded'] * 100) if parsing_results['files_statistics']['total_loaded'] > 0 else 0
    print(f"Successfully extracted text from {parsing_results['files_statistics']['parsed_successfully']} files")
    
    pages_for_indexing = [page for page in all_pages if len(page.text.strip()) > 0]
    parsing_results['pages_statistics']['not_empty'] = len(pages_for_indexing)
    parsing_results['pages_statistics']['not_empty_percentage'] = (parsing_results['pages_statistics']['not_empty'] / parsing_results['pages_statistics']['total_loaded'] * 100) if parsing_results['pages_statistics']['total_loaded'] > 0 else 0
    parsing_results['pages_statistics']['empty'] = parsing_results['pages_statistics']['total_loaded'] - parsing_results['pages_statistics']['not_empty']
    parsing_results['pages_statistics']['empty_percentage'] = (parsing_results['pages_statistics']['empty'] / parsing_results['pages_statistics']['total_loaded'] * 100) if parsing_results['pages_statistics']['total_loaded'] > 0 else 0
    print(f"Filtered {parsing_results['pages_statistics']['not_empty']} non-empty pages for indexing")
    
    parsing_results['report_text'] = f"""
PARSING REPORT

🔢 Total files parsed: {parsing_results['files_statistics']['total_loaded']:,}
  - PDF files: {parsing_results['files_statistics']['total_pdf_loaded']:,}
  - DOC files: {parsing_results['files_statistics']['total_doc_loaded']:,}
  - DOCX files: {parsing_results['files_statistics']['total_docx_loaded']:,}
✅ Files successfully parsed: {parsing_results['files_statistics']['parsed_successfully']:,} files ({parsing_results['files_statistics']['parsed_successfully_percentage']:.1f}%)
   - With Reader: {parsing_results['files_statistics']['files']['ParsedWithReader']['count']:,} files ({parsing_results['files_statistics']['files']['ParsedWithReader']['percentage']:.1f}%)
   - With PyMuPDF: {parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['count']:,} files ({parsing_results['files_statistics']['files']['ParsedWithPyMuPDF']['percentage']:.1f}%)
   - With OCR: {parsing_results['files_statistics']['files']['ParsedWithOCR']['count']:,} files ({parsing_results['files_statistics']['files']['ParsedWithOCR']['percentage']:.1f}%)
❌ Files failed to parse: {parsing_results['files_statistics']['failed_to_parse']:,} files ({parsing_results['files_statistics']['failed_to_parse_percentage']:.1f}%)
   - Corrupted: {parsing_results['files_statistics']['files']['Corrupted']['count']:,} files ({parsing_results['files_statistics']['files']['Corrupted']['percentage']:.1f}%)
   - Scanned: {parsing_results['files_statistics']['files']['Scanned']['count']:,} files ({parsing_results['files_statistics']['files']['Scanned']['percentage']:.1f}%)
   - Empty: {parsing_results['files_statistics']['files']['Empty']['count']:,} files ({parsing_results['files_statistics']['files']['Empty']['percentage']:.1f}%)
   - Exception: {parsing_results['files_statistics']['files']['Exception']['count']:,} files ({parsing_results['files_statistics']['files']['Exception']['percentage']:.1f}%)

Total pages loaded: {parsing_results['pages_statistics']['total_loaded']:,}
✅ Non-empty: {parsing_results['pages_statistics']['not_empty']:,} ({parsing_results['pages_statistics']['not_empty_percentage']:.1f}%)
❌ Empty: {parsing_results['pages_statistics']['empty']:,} ({parsing_results['pages_statistics']['empty_percentage']:.1f}%)
"""
    
    return pages_for_indexing, parsing_results