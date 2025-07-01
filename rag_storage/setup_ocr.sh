#!/bin/bash

# Setup script for OCR dependencies
# This script installs the system dependencies needed for PDF OCR processing

echo "Setting up OCR dependencies for RAG pipeline..."

# Detect the operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"
    
    # Update package list
    sudo apt-get update
    
    # Install Tesseract OCR
    echo "Installing Tesseract OCR..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    
    # Install poppler-utils for pdf2image
    echo "Installing poppler-utils..."
    sudo apt-get install -y poppler-utils
    
    # Install additional language packs for multilingual support
    echo "Installing language packs for Ukrainian and Russian..."
    sudo apt-get install -y tesseract-ocr-ukr tesseract-ocr-rus
    
    # Install other language packs if needed (uncomment as needed)
    # sudo apt-get install -y tesseract-ocr-fra  # French
    # sudo apt-get install -y tesseract-ocr-deu  # German
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi
    
    # Install Tesseract OCR with language support
    echo "Installing Tesseract OCR with language packs..."
    brew install tesseract tesseract-lang
    
    # Install poppler for pdf2image
    echo "Installing poppler..."
    brew install poppler
    
else
    echo "Unsupported operating system: $OSTYPE"
    echo "Please install the following manually:"
    echo "- Tesseract OCR"
    echo "- Poppler (for pdf2image)"
    exit 1
fi

echo "System dependencies installed successfully!"
echo ""
echo "Now install Python dependencies with:"
echo "pip install -r requirements_storage.txt"
echo ""
echo "To verify installation, run:"
echo "python test_multilingual_ocr.py"
echo ""
echo "Note: If using Docker deployment, OCR dependencies are automatically included."
echo "This script is only needed for local development outside Docker."