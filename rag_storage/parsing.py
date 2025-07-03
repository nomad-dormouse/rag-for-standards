#!/usr/bin/env python3
"""
PDF, DOC, DOCX parsing module for Ukrainian technical standards RAG system.
Handles PDF text extraction with 2-step fallback strategy.
Supports Ukrainian, Russian, and English languages.
Saves parsing results statistics to JSON, used parsing methods to CSV, and parsed pages to pickle.
"""

import os
import io
import json
import csv
import pickle
import fitz
from contextlib import redirect_stderr
from llama_index.core import SimpleDirectoryReader, Document
import pytesseract
from PIL import Image

def extract_text_with_default_reader(pdf_path: str, min_text_threshold: int) -> tuple[list[Document], str]:
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
            print(f"  No meaningful content extracted with default reader...")
            raise Exception("Insufficient text content")
        if empty_pages_in_file == len(file_pages) and len(file_pages) > 0:
            print(f"  All pages empty, likely scanned document...")
            raise Exception("All pages empty - likely scanned")
        
        return file_pages, None
        
    except Exception as e:
        return [], str(e)

def extract_text_with_pymupdf_and_ocr(pdf_path: str, min_text_threshold: int, statuses: dict) -> list[Document]:
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
                            extraction_method = statuses['ocr']
                        else:
                            extraction_method = statuses['pymupdf']
                except Exception as ocr_e:
                    print(f"    OCR fallback failed for page {page_num + 1}: {str(ocr_e)}")
                    extraction_method = statuses['pymupdf']
            else:
                extraction_method = statuses['pymupdf']
            if len(text.strip()) > min_text_threshold:
                document = Document(
                    text=text,
                    metadata={
                        'file_path': pdf_path,
                        'page_number': page_num + 1,
                        'extraction_method': extraction_method,
                    }
                )
                documents.append(document)
        
        doc.close()
        return documents
        
    except Exception as e:
        print(f"  PyMuPDF extraction failed for {pdf_path}: {str(e)}")
        return []

def parse_document_with_fallback(document_path: str, min_text_threshold: int) -> tuple[list[Document], str, str]:
    statuses={
        "default": "ParsedWithDefaultReader",
        "pymupdf": "ParsedWithPyMuPDF",
        "ocr": "ParsedWithPyMuPDFAndOCR",
        "failed": "FailedToParse"
    }
    print(f"Processing: {os.path.basename(document_path)}")
    
    # Strategy 1: Try LlamaIndex SimpleDirectoryReader (works for PDF, DOC, DOCX)
    file_pages, error_message = extract_text_with_default_reader(document_path, min_text_threshold)
    if file_pages:
        return file_pages, statuses['default'], None
    
    # For PDF files only, try additional fallback strategy
    if document_path.lower().endswith('.pdf'):
        original_error = error_message
        
        # Strategy 2: Try alternative PDF parser (PyMuPDF) and OCR if needed
        print(f"  Trying alternative parser PyMuPDF + OCR if needed...")
        pymupdf_pages = extract_text_with_pymupdf_and_ocr(document_path, min_text_threshold, statuses)
        if pymupdf_pages and len(pymupdf_pages) > 0:
            total_text = sum(len(page.text.strip()) for page in pymupdf_pages)
            if total_text > min_text_threshold:
                # Check if any page used OCR
                used_ocr = any(page.metadata.get('extraction_method') == 'PyMuPDFAndOCR' for page in pymupdf_pages)
                status = statuses['ocr'] if used_ocr else statuses['pymupdf']
                return pymupdf_pages, status, None
        
        # All strategies failed
        return [], statuses['failed'], original_error
    else:
        # For non-PDF files, if LlamaIndex failed, mark as not parsed
        return [], statuses['failed'], error_message

def load_all_documents(standards_dir: str) -> list[str]:
    """Load and return list of document file paths from standards directory."""
    print(f"Loading Ukrainian technical standards from: {standards_dir}...")
    files = []
    for root, dirs, dir_files in os.walk(standards_dir):
        for file in dir_files:
            if file.lower().endswith(('.pdf', '.doc', '.docx')):
                files.append(os.path.join(root, file))
    print(f"Found {len(files)} files to process.")
    return files

def calculate_statistics(files: list[str], all_pages_length: int, successfully_parsed_pages: list) -> dict:
    """Calculate and return complete statistics as JSON object."""
    # Initialise complete statistics structure
    parsing_results_statistics = {
        'files_statistics': {
            'total_loaded': len(files),
            'total_pdf_loaded': len([f for f in files if f.lower().endswith('.pdf')]),
            'total_doc_loaded': len([f for f in files if f.lower().endswith('.doc')]),
            'total_docx_loaded': len([f for f in files if f.lower().endswith('.docx')]),
            'parsed_successfully': 0,
            'parsed_successfully_percentage': 0,
            'failed_to_parse': 0,
            'failed_to_parse_percentage': 0,
            'files': {
                'ParsedWithDefaultReader': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'ParsedWithPyMuPDF': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'ParsedWithPyMuPDFAndOCR': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
                'NotParsed': {
                    'count': 0,
                    'percentage': 0,
                    'files': []
                },
            }
        },
        'pages_statistics': {
            'total_loaded': all_pages_length,
            'not_empty': 0,
            'not_empty_percentage': 0,
            'empty': 0,
            'empty_percentage': 0,
        },
        'report_text': '',
    }
    
    # Calculate file statistics
    parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['count'] = len(parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['files'])
    parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['percentage'] = (parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['count'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['count'] = len(parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['files'])
    parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['percentage'] = (parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['count'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['count'] = len(parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['files'])
    parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['percentage'] = (parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['count'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['files_statistics']['parsed_successfully'] = parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['count'] + parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['count'] + parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['count']
    parsing_results_statistics['files_statistics']['parsed_successfully_percentage'] = (parsing_results_statistics['files_statistics']['parsed_successfully'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['files_statistics']['files']['NotParsed']['count'] = len(parsing_results_statistics['files_statistics']['files']['NotParsed']['files'])
    parsing_results_statistics['files_statistics']['files']['NotParsed']['percentage'] = (parsing_results_statistics['files_statistics']['files']['NotParsed']['count'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['files_statistics']['failed_to_parse'] = parsing_results_statistics['files_statistics']['files']['NotParsed']['count']
    parsing_results_statistics['files_statistics']['failed_to_parse_percentage'] = (parsing_results_statistics['files_statistics']['failed_to_parse'] / parsing_results_statistics['files_statistics']['total_loaded'] * 100) if parsing_results_statistics['files_statistics']['total_loaded'] > 0 else 0
    
    # Calculate page statistics
    parsing_results_statistics['pages_statistics']['not_empty'] = len(successfully_parsed_pages)
    parsing_results_statistics['pages_statistics']['not_empty_percentage'] = (parsing_results_statistics['pages_statistics']['not_empty'] / parsing_results_statistics['pages_statistics']['total_loaded'] * 100) if parsing_results_statistics['pages_statistics']['total_loaded'] > 0 else 0
    parsing_results_statistics['pages_statistics']['empty'] = parsing_results_statistics['pages_statistics']['total_loaded'] - parsing_results_statistics['pages_statistics']['not_empty']
    parsing_results_statistics['pages_statistics']['empty_percentage'] = (parsing_results_statistics['pages_statistics']['empty'] / parsing_results_statistics['pages_statistics']['total_loaded'] * 100) if parsing_results_statistics['pages_statistics']['total_loaded'] > 0 else 0
    
    # Generate report text
    parsing_results_statistics['report_text'] = f"""
PARSING REPORT

Files statistics:
🔢 Total files parsed: {parsing_results_statistics['files_statistics']['total_loaded']:,}
  - PDF files: {parsing_results_statistics['files_statistics']['total_pdf_loaded']:,}
  - DOC files: {parsing_results_statistics['files_statistics']['total_doc_loaded']:,}
  - DOCX files: {parsing_results_statistics['files_statistics']['total_docx_loaded']:,}
✅ Files successfully parsed: {parsing_results_statistics['files_statistics']['parsed_successfully']:,} files ({parsing_results_statistics['files_statistics']['parsed_successfully_percentage']:.1f}%)
   - With Default Reader: {parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['count']:,} files ({parsing_results_statistics['files_statistics']['files']['ParsedWithDefaultReader']['percentage']:.1f}%)
   - With PyMuPDF: {parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['count']:,} files ({parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDF']['percentage']:.1f}%)
   - With PyMuPDF and OCR: {parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['count']:,} files ({parsing_results_statistics['files_statistics']['files']['ParsedWithPyMuPDFAndOCR']['percentage']:.1f}%)
❌ Files failed to parse: {parsing_results_statistics['files_statistics']['files']['NotParsed']['count']:,} files ({parsing_results_statistics['files_statistics']['files']['NotParsed']['percentage']:.1f}%)

Pages statistics:
🔢 Total pages loaded: {parsing_results_statistics['pages_statistics']['total_loaded']:,}
✅ Non-empty pages: {parsing_results_statistics['pages_statistics']['not_empty']:,} ({parsing_results_statistics['pages_statistics']['not_empty_percentage']:.1f}%)
❌ Empty pages: {parsing_results_statistics['pages_statistics']['empty']:,} ({parsing_results_statistics['pages_statistics']['empty_percentage']:.1f}%)
"""
    
    return parsing_results_statistics

def save_parsing_results(files: list[str], all_pages_length: int, successfully_parsed_pages: list, json_file: str, csv_file: str, pickle_file: str):
    """Calculate statistics and save parsing results statistics to JSON file, CSV file, and parsed pages to pickle file."""
    # Calculate parsing results statistics
    parsing_results_statistics = calculate_statistics(files, all_pages_length, successfully_parsed_pages)

    # Save parsing results statistics to JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(parsing_results_statistics, f, indent=2, ensure_ascii=False, default=str)
    print(f"📊 Parsing results statistics saved to: {json_file}")
    
    # Save files processing methods to CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Processing method'])
        for parsing_method, data in parsing_results_statistics['files_statistics']['files'].items():
            for file_path in data['files']:
                writer.writerow([file_path, parsing_method])
    print(f"📁 Files parsing methods saved to: {csv_file}")
    
    # Save parsed pages to pickle file
    with open(pickle_file, 'wb') as f:
        pickle.dump(successfully_parsed_pages, f)
    print(f"💾 Parsed pages saved to: {pickle_file}")

    # Display parsing report
    print(parsing_results_statistics['report_text'])

def parse_all_documents(standards_dir: str, min_text_threshold: int, json_file: str, csv_file: str, pickle_file: str) -> list[Document]:
    """Load and process document files from standards directory, save results, and return parsed pages."""
    files = load_all_documents(standards_dir)
    
    all_pages = []
    for file in files:
        pages, status, error_details = parse_document_with_fallback(file, min_text_threshold)
        if error_details:
            print(f"  Final status: {status} - {error_details}")
        else:
            print(f"  Final status: {status} - {len(pages)} pages extracted")
        all_pages.extend(pages)
    all_pages_length = len(all_pages)
    print(f"Loaded {all_pages_length} pages from {len(files)} files")
    
    successfully_parsed_pages = [page for page in all_pages if len(page.text.strip()) > 0]
    save_parsing_results(files, all_pages_length, successfully_parsed_pages, json_file, csv_file, pickle_file)

    return successfully_parsed_pages
