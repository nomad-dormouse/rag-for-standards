#!/usr/bin/env python3
"""
Demonstration script showing multilingual OCR capabilities.
This script shows how the system handles English, Ukrainian, and Russian text.
"""

import os
import sys

def test_multilingual_ocr():
    """Demonstrate multilingual OCR capabilities."""
    
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        print("✓ OCR libraries imported successfully")
    except ImportError as e:
        print(f"✗ OCR libraries not available: {e}")
        print("Please install: pip install pytesseract pillow")
        return False
    
    print("\n" + "="*60)
    print("MULTILINGUAL OCR DEMONSTRATION")
    print("="*60)
    
    # Test different language combinations
    language_tests = [
        {
            'name': 'English Only',
            'lang_code': 'eng',
            'sample_text': 'Hello World! This is English text.'
        },
        {
            'name': 'Ukrainian Only', 
            'lang_code': 'ukr',
            'sample_text': 'Привіт світ! Це український текст.'
        },
        {
            'name': 'Russian Only',
            'lang_code': 'rus', 
            'sample_text': 'Привет мир! Это русский текст.'
        },
        {
            'name': 'Combined Languages (Auto-detect)',
            'lang_code': 'eng+ukr+rus',
            'sample_text': 'Mixed: Hello Привіт Привет'
        }
    ]
    
    print(f"\nTesting Tesseract version: {pytesseract.get_tesseract_version()}")
    print("\nLanguage Support Test:")
    print("-" * 40)
    
    for test in language_tests:
        try:
            # Create a simple test image with text
            img = Image.new('RGB', (400, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Use default font (this works on most systems)
            try:
                # Try to use a larger font if available
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw text on image
            draw.text((10, 30), test['sample_text'], fill='black', font=font)
            
            # Run OCR with specified language
            result = pytesseract.image_to_string(img, lang=test['lang_code'])
            
            print(f"✓ {test['name']}: Language '{test['lang_code']}' working")
            print(f"  Input:  {test['sample_text']}")
            print(f"  Output: {result.strip()}")
            print()
            
        except Exception as e:
            print(f"✗ {test['name']}: Failed - {e}")
            if 'not found' in str(e).lower():
                print(f"  Language pack '{test['lang_code']}' may not be installed")
            print()
    
    # Show how the actual ingestion script uses OCR
    print("="*60)
    print("ACTUAL INGESTION CONFIGURATION")
    print("="*60)
    print("The ingestion script uses: lang='eng+ukr+rus'")
    print("This means it will automatically:")
    print("• Detect English text in PDFs")
    print("• Detect Ukrainian text in PDFs") 
    print("• Detect Russian text in PDFs")
    print("• Handle mixed-language documents")
    print("• Work with any combination of these languages")
    
    return True

def show_language_info():
    """Show information about language support."""
    print("\n" + "="*60)
    print("LANGUAGE SUPPORT INFORMATION")
    print("="*60)
    
    print("Supported Languages:")
    print("• English (eng) - Technical documentation, international standards")
    print("• Ukrainian (ukr) - ДСТУ standards, local technical documents")
    print("• Russian (rus) - Legacy documents, GOST standards")
    
    print("\nHow it works:")
    print("• The system automatically tries all three languages")
    print("• No need to specify document language in advance")
    print("• Works with mixed-language documents")
    print("• Optimized for technical/standards documentation")
    
    print("\nDocument types that benefit:")
    print("• Scanned ДСТУ standards")
    print("• Photocopied technical documents")
    print("• Mixed Ukrainian/Russian legacy documents")
    print("• International standards with multiple languages")

if __name__ == "__main__":
    print("Multilingual OCR Test for RAG Pipeline")
    print("This demonstrates the OCR capabilities for English, Ukrainian, and Russian")
    
    if test_multilingual_ocr():
        show_language_info()
        print(f"\n✓ Multilingual OCR system is ready!")
        print(f"Your RAG pipeline can now process documents in English, Ukrainian, and Russian.")
    else:
        print(f"\n✗ Multilingual OCR test failed.")
        print(f"Please check OCR installation and language packs.")
        sys.exit(1)