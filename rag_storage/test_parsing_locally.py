#!/usr/bin/env python3
"""
Local test script for parsing functionality.
"""

import os
import csv
import pickle
from dotenv import load_dotenv
from parsing import parse_all_documents

def save_parsing_results(pages: list, parsing_results: dict, csv_file: str, pages_file: str):
    """Save parsing results to both CSV file and pickle file for reuse."""
    # Save CSV results
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Status', 'Extraction Method'])
        for status, data in parsing_results['files_statistics']['files'].items():
            for file_path in data['files']:
                writer.writerow([file_path, status, data.get('extraction_method', status)])
    print(f"📊 Parsing results saved to: {csv_file}")
    
    # Save parsed pages for embedding
    with open(pages_file, 'wb') as f:
        pickle.dump(pages, f)
    print(f"💾 Parsed pages saved to: {pages_file}")

def main():
    """Test parsing functionality locally."""
    delimiter_length = int(os.getenv("DELIMITER_LENGTH"))
    print("Testing Parsing Functionality Locally")
    print("=" * delimiter_length)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    standards_dir = os.getenv("STANDARDS_DIR_NAME", "standards")
    min_text_threshold = int(os.getenv("MIN_TEXT_THRESHOLD", "100"))
    parsing_results_file = os.getenv("PARSING_RESULTS_FILE_NAME")
    parsed_pages_file = os.getenv("PARSED_PAGES_FILE_NAME")
    
    print(f"Standards directory: {standards_dir}")
    print(f"Minimum text threshold: {min_text_threshold}")
    print()
    
    # Check if standards directory exists
    if not os.path.exists(standards_dir):
        print(f"❌ Standards directory '{standards_dir}' not found")
        return False
    
    # Run parsing
    try:
        pages, results = parse_all_documents(standards_dir, min_text_threshold)
        print("\n" + "=" * delimiter_length)
        print("PARSING COMPLETED SUCCESSFULLY!")
        print("=" * delimiter_length)
        print(results['report_text'])
        print(f"Total pages for indexing: {len(pages)}")
        save_parsing_results(pages, results, parsing_results_file, parsed_pages_file)
        return True
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 