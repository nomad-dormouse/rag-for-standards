# Enhanced RAG Pipeline with OCR Support

This enhanced version of your RAG pipeline now supports processing **all PDF documents**, including corrupted PDFs and scanned documents that require Optical Character Recognition (OCR).

## What's New

### 🔧 Enhanced PDF Processing
- **Multi-strategy approach**: Falls back through different extraction methods automatically
- **OCR support**: Handles scanned PDFs and images using Tesseract OCR
- **Corruption handling**: Attempts alternative extraction methods for corrupted PDFs
- **Improved reporting**: Detailed breakdown of extraction methods used

### 📊 Processing Strategies

The pipeline now uses a three-tier fallback approach:

1. **LlamaIndex SimpleDirectoryReader** (Original method)
   - Fast and efficient for well-formed PDFs
   - Detects corruption warnings automatically

2. **PyMuPDF with OCR fallback**
   - More robust PDF parsing
   - Automatically applies OCR to pages with little/no text
   - Handles partially corrupted documents

3. **Full OCR processing**
   - Converts entire PDF to images
   - Runs OCR on all pages
   - Last resort for completely corrupted or scanned documents

## Installation

### 1. Install System Dependencies

Run the setup script to install required system packages:

```bash
cd rag_storage
./setup_ocr.sh
```

This will install:
- **Tesseract OCR**: For text recognition
- **Poppler**: For PDF to image conversion

### 2. Install Python Dependencies

```bash
pip install -r requirements_storage.txt
```

### 3. Verify Installation

```bash
python test_ocr.py
```

This will test all OCR components and report any issues.

## Usage

The enhanced pipeline works exactly like the original - just run:

```bash
python ingest.py
```

### What Happens Automatically

1. **Normal PDFs**: Processed with the original fast method
2. **Corrupted PDFs**: Automatically tries PyMuPDF extraction
3. **Scanned PDFs**: Automatically applies OCR when needed
4. **Mixed documents**: Uses the best method for each page

### Enhanced Reporting

The new pipeline provides detailed reports:

```
Files parsing
- Total files: 150
- Successfully parsed (original): 120
- Successfully parsed (PyMuPDF): 15
- Successfully parsed (OCR): 10
- Total successful: 145 (96.7%)
- Corrupted PDFs: 3
- Scanned documents (failed): 2
```

## Configuration

### OCR Language Support

By default, the system uses English OCR. To add support for other languages:

1. **Ukrainian**: `sudo apt-get install tesseract-ocr-ukr`
2. **Russian**: `sudo apt-get install tesseract-ocr-rus`
3. **French**: `sudo apt-get install tesseract-ocr-fra`
4. **German**: `sudo apt-get install tesseract-ocr-deu`

Then modify the OCR calls in `ingest.py`:
```python
text = pytesseract.image_to_string(page_image, lang='eng+ukr')
```

### Performance Tuning

#### OCR Quality vs Speed
- **Higher DPI** (300-600): Better OCR accuracy, slower processing
- **Lower DPI** (150-200): Faster processing, potentially lower accuracy

Modify in `ingest.py`:
```python
pages = convert_from_path(pdf_path, dpi=300)  # Adjust DPI here
```

#### Text Threshold
Minimum characters to consider a page as having meaningful content:

```python
min_text_threshold = 100  # Adjust this value
```

## Troubleshooting

### Common Issues

#### 1. "OCR libraries not available"
**Solution**: Run `./setup_ocr.sh` and `pip install -r requirements_storage.txt`

#### 2. "poppler-utils not found"
**Solution**: 
- **Linux**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`

#### 3. "Tesseract not found"
**Solution**:
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

#### 4. Slow OCR processing
**Solutions**:
- Reduce DPI in `convert_from_path(pdf_path, dpi=200)`
- Increase `min_text_threshold` to skip near-empty pages
- Consider processing in batches

#### 5. Poor OCR accuracy
**Solutions**:
- Increase DPI: `convert_from_path(pdf_path, dpi=600)`
- Install language-specific models
- Pre-process images (deskewing, noise removal)

### Testing Individual Components

```bash
# Test Tesseract
tesseract --version

# Test poppler
pdftoppm -h

# Test Python libraries
python -c "import fitz, pytesseract; from pdf2image import convert_from_path; print('All imports successful')"
```

## Performance Considerations

### Memory Usage
- OCR processing is memory-intensive
- Large PDFs are processed page-by-page to manage memory
- Consider processing large batches overnight

### Processing Time
- **Normal PDFs**: ~1-2 seconds per file
- **OCR PDFs**: ~10-30 seconds per page (depending on complexity)
- **Mixed documents**: Varies based on content

### Disk Space
- Temporary images are created during OCR processing
- Images are cleaned up automatically
- Ensure sufficient disk space for large document sets

## Advanced Configuration

### Custom OCR Settings

You can modify OCR parameters in the `extract_text_with_ocr` function:

```python
# Custom OCR configuration
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(page_image, config=custom_config)
```

OCR parameters:
- `--oem 3`: Use default OCR Engine Mode
- `--psm 6`: Assume uniform block of text
- `--psm 1`: Automatic page segmentation with OSD

### Batch Processing

For large document collections, consider processing in batches:

```python
# Process files in smaller batches
batch_size = 50
for i in range(0, len(pdf_files), batch_size):
    batch = pdf_files[i:i+batch_size]
    # Process batch...
```

## Migration from Original Pipeline

The enhanced pipeline is **fully backward compatible**:

1. **No changes needed** to existing configuration
2. **Same output format** for embeddings and index
3. **Enhanced reporting** with additional extraction method details
4. **Graceful degradation** - works without OCR libraries (with warnings)

## Monitoring and Logging

The pipeline now provides detailed logging for each processing strategy:

```
Processing: document.pdf
  Corruption detected, trying alternative extraction...
  Trying PyMuPDF extraction...
  Trying full OCR extraction...
    Processing page 1/10
    Processing page 2/10
    ...
  Final status: ParsedWithOCR - 8 pages extracted
```

This helps identify which documents require OCR and monitor processing efficiency.

## Support

If you encounter issues:

1. Run `python test_ocr.py` to verify installation
2. Check the processing logs for specific error messages
3. Consider the troubleshooting section above
4. For Ukrainian text, install `tesseract-ocr-ukr` language pack

The enhanced pipeline maintains the same simplicity while dramatically expanding the range of documents it can process successfully.