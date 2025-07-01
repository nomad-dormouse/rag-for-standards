#!/usr/bin/env python3
"""
Test script to verify OCR functionality for the RAG pipeline.
"""

import os
import sys

def test_imports():
    """Test if all required libraries can be imported."""
    print("Testing imports...")
    
    try:
        import fitz
        print("✓ PyMuPDF (fitz) imported successfully")
    except ImportError as e:
        print(f"✗ PyMuPDF import failed: {e}")
        return False
    
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image imported successfully")
    except ImportError as e:
        print(f"✗ pdf2image import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✓ pytesseract imported successfully")
    except ImportError as e:
        print(f"✗ pytesseract import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow (PIL) imported successfully")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    return True

def test_tesseract():
    """Test if Tesseract is properly installed and accessible."""
    print("\nTesting Tesseract installation...")
    
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Create a simple test image with text
        # This is a minimal test - in practice, we'd use actual PDF pages
        test_text = "Hello OCR Test"
        
        # Try to get Tesseract version
        try:
            version_info = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract version: {version_info}")
        except Exception as e:
            print(f"✗ Could not get Tesseract version: {e}")
            return False
        
        # Test multilingual support
        try:
            # Test if multiple languages can be used
            test_langs = ['eng', 'ukr', 'rus']
            available_langs = []
            
            for lang in test_langs:
                try:
                    # Try to use each language (this will fail if language pack is missing)
                    pytesseract.image_to_string(Image.new('RGB', (100, 50), color='white'), lang=lang)
                    available_langs.append(lang)
                except:
                    pass
            
            if available_langs:
                print(f"✓ Available languages: {', '.join(available_langs)}")
            else:
                print("⚠ No language packs detected")
                
        except Exception as e:
            print(f"⚠ Could not test language support: {e}")
        
        print("✓ Tesseract is accessible")
        return True
        
    except Exception as e:
        print(f"✗ Tesseract test failed: {e}")
        return False

def test_pdf2image():
    """Test if pdf2image can work with poppler."""
    print("\nTesting pdf2image with poppler...")
    
    try:
        from pdf2image import convert_from_path
        
        # Try to access poppler utilities
        import subprocess
        result = subprocess.run(['pdftoppm', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ poppler-utils (pdftoppm) is accessible")
            return True
        else:
            print("✗ poppler-utils not found or not working")
            return False
            
    except Exception as e:
        print(f"✗ pdf2image test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("OCR Functionality Test")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test Tesseract
    if not test_tesseract():
        all_tests_passed = False
    
    # Test pdf2image
    if not test_pdf2image():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All OCR tests passed! Your system is ready for OCR processing.")
    else:
        print("✗ Some tests failed. Please check the installation:")
        print("\nTo install missing dependencies:")
        print("1. Run: ./setup_ocr.sh")
        print("2. Run: pip install -r requirements_storage.txt")
        print("3. Run this test again: python test_ocr.py")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)