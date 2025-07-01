#!/bin/bash

# OCR Deployment Verification Script
# Tests if OCR functionality is properly set up in the deployed system

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== OCR Deployment Verification ===${NC}"

# Change to script directory
cd "$(dirname "${BASH_SOURCE[0]}")"

# Load environment variables
if [[ -f ".env" ]]; then
    source ".env"
else
    echo -e "${RED}ERROR: .env file not found${NC}"
    exit 1
fi

# Function to test OCR in storage container
test_ocr_in_container() {
    echo -e "\n${BLUE}Testing OCR functionality in storage container...${NC}"
    
    # Build the storage container if it doesn't exist
    echo -e "${BLUE}Building storage container...${NC}"
    docker-compose build ${STORAGE_SERVICE_NAME} > /dev/null 2>&1
    
    # Test OCR libraries in container
    echo -e "${BLUE}Testing OCR libraries...${NC}"
    
    # Test Tesseract
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} tesseract --version > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Tesseract OCR is available${NC}"
        
        # Get version info
        TESSERACT_VERSION=$(docker-compose run --rm ${STORAGE_SERVICE_NAME} tesseract --version 2>/dev/null | head -1)
        echo -e "  ${TESSERACT_VERSION}"
    else
        echo -e "${RED}✗ Tesseract OCR is not available${NC}"
        return 1
    fi
    
    # Test Poppler
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} pdftoppm -h > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Poppler utilities are available${NC}"
    else
        echo -e "${RED}✗ Poppler utilities are not available${NC}"
        return 1
    fi
    
    # Test Python OCR libraries
    echo -e "${BLUE}Testing Python OCR libraries...${NC}"
    
    OCR_TEST_RESULT=$(docker-compose run --rm ${STORAGE_SERVICE_NAME} python -c "
try:
    import fitz
    print('✓ PyMuPDF (fitz) imported successfully')
except ImportError as e:
    print('✗ PyMuPDF import failed:', e)
    exit(1)

try:
    from pdf2image import convert_from_path
    print('✓ pdf2image imported successfully')
except ImportError as e:
    print('✗ pdf2image import failed:', e)
    exit(1)

try:
    import pytesseract
    print('✓ pytesseract imported successfully')
except ImportError as e:
    print('✗ pytesseract import failed:', e)
    exit(1)

try:
    from PIL import Image
    print('✓ Pillow (PIL) imported successfully')
except ImportError as e:
    print('✗ Pillow import failed:', e)
    exit(1)

print('✓ All OCR libraries imported successfully')
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}${OCR_TEST_RESULT}${NC}"
    else
        echo -e "${RED}✗ Python OCR library test failed${NC}"
        return 1
    fi
    
    # Test Tesseract accessibility from Python
    echo -e "${BLUE}Testing Tesseract accessibility from Python...${NC}"
    
    TESSERACT_PYTHON_TEST=$(docker-compose run --rm ${STORAGE_SERVICE_NAME} python -c "
import pytesseract
try:
    version = pytesseract.get_tesseract_version()
    print(f'✓ Tesseract accessible from Python: {version}')
except Exception as e:
    print(f'✗ Tesseract not accessible from Python: {e}')
    exit(1)
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}${TESSERACT_PYTHON_TEST}${NC}"
    else
        echo -e "${RED}✗ Tesseract not accessible from Python${NC}"
        return 1
    fi
    
    return 0
}

# Function to test language support
test_language_support() {
    echo -e "\n${BLUE}Testing language support...${NC}"
    
    # Test English language pack
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} test -f /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata; then
        echo -e "${GREEN}✓ English language pack available${NC}"
    else
        echo -e "${YELLOW}⚠ English language pack not found${NC}"
    fi
    
    # Test Ukrainian language pack
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} test -f /usr/share/tesseract-ocr/4.00/tessdata/ukr.traineddata; then
        echo -e "${GREEN}✓ Ukrainian language pack available${NC}"
    else
        echo -e "${YELLOW}⚠ Ukrainian language pack not found${NC}"
    fi
    
    # Test Russian language pack
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} test -f /usr/share/tesseract-ocr/4.00/tessdata/rus.traineddata; then
        echo -e "${GREEN}✓ Russian language pack available${NC}"
    else
        echo -e "${YELLOW}⚠ Russian language pack not found${NC}"
    fi
}

# Function to test if ingestion script has OCR support
test_ingestion_ocr_support() {
    echo -e "\n${BLUE}Testing ingestion script OCR support...${NC}"
    
    # Check if the enhanced ingestion script exists and has OCR functions
    if docker-compose run --rm ${STORAGE_SERVICE_NAME} python -c "
import sys
sys.path.append('.')
try:
    from ingest import extract_text_with_ocr, extract_text_with_pymupdf, process_pdf_with_fallbacks
    print('✓ Enhanced ingestion script with OCR support detected')
except ImportError as e:
    print('✗ OCR functions not found in ingestion script')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✓ Enhanced ingestion script with OCR support detected${NC}"
    else
        echo -e "${RED}✗ OCR functions not found in ingestion script${NC}"
        return 1
    fi
}

# Main execution
echo -e "${BLUE}Verifying OCR deployment...${NC}"

# Test OCR in container
if test_ocr_in_container; then
    echo -e "\n${GREEN}✓ OCR container setup verification passed${NC}"
else
    echo -e "\n${RED}✗ OCR container setup verification failed${NC}"
    echo -e "${YELLOW}Please check the Docker setup and try rebuilding containers${NC}"
    exit 1
fi

# Test language support
test_language_support

# Test ingestion script
if test_ingestion_ocr_support; then
    echo -e "\n${GREEN}✓ Ingestion script OCR support verified${NC}"
else
    echo -e "\n${RED}✗ Ingestion script OCR support verification failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== OCR Deployment Verification Complete ===${NC}"
echo -e "${GREEN}✓ Your system is ready to process all PDF types including:${NC}"
echo -e "${GREEN}  - Normal PDFs (fast processing)${NC}"
echo -e "${GREEN}  - Corrupted PDFs (fallback processing)${NC}"
echo -e "${GREEN}  - Scanned PDFs (OCR processing)${NC}"
echo -e "\n${BLUE}To run the enhanced ingestion:${NC}"
echo -e "${BLUE}  docker-compose --profile ingestion run --rm ${STORAGE_SERVICE_NAME}${NC}"
echo -e "\n${BLUE}To monitor processing with detailed logs:${NC}"
echo -e "${BLUE}  docker-compose --profile ingestion run --rm ${STORAGE_SERVICE_NAME} | tee ingestion.log${NC}"
echo -e "\n${BLUE}To test multilingual OCR capabilities:${NC}"
echo -e "${BLUE}  docker-compose run --rm ${STORAGE_SERVICE_NAME} python test_multilingual_ocr.py${NC}"