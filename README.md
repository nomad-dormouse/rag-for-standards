# RAG for Ukrainian Technical Standards

A bilingual Retrieval-Augmented Generation (RAG) system for searching and answering questions about Ukrainian technical documentation standards using Docker containerisation. **Now with enhanced OCR support for processing all PDF types, including corrupted and scanned documents.**

## 🚀 Quick Start

### Local Deployment
```bash
# Clone and deploy locally
git clone https://github.com/nomad-dormouse/rag-for-standards.git
cd rag-for-standards
./deploy.sh
```

### Remote Deployment
```bash
# Deploy to remote server (requires SSH key setup)
./deploy_remotely.sh
```

## 📁 Project Structure

```
rag-for-standards/
├── rag_storage/               # Document processing service
│   ├── standards/             # Ukrainian technical standards (PDFs)
│   ├── dockerfile_storage     # Docker image for document ingestion
│   ├── ingest.py             # Enhanced document processing with OCR
│   ├── setup_ocr.sh          # OCR dependencies installer
│   ├── test_ocr.py           # OCR functionality tester
│   └── requirements_storage.txt # Includes OCR dependencies
├── rag_webapp/                # Web application service
│   ├── dockerfile_webapp     # Docker image for web interface
│   ├── webapp.py            # Streamlit application
│   ├── query_engine.py      # RAG query processing
│   ├── localisation.py     # Multi-language support
│   └── requirements_webapp.txt
├── docker-compose.yml        # Container orchestration
├── deploy.sh                # Local deployment script
├── deploy_remotely.sh       # Remote deployment script
├── verify_ocr_deployment.sh # OCR functionality verification
└── .env                     # Environment configuration
```

## 🛠️ Configuration

Copy the template and configure your environment:

```bash
cp .env.template .env
# Edit .env with your actual values
```

**Required settings:**
- `OPENAI_API_KEY`: Your OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- `WEBAPP_PORT`: Port for web interface (default: 8501)

**Optional settings (for remote deployment):**
- `REMOTE_HOST`: Your server IP address
- `REMOTE_USER`: SSH username (usually 'root')
- `SSH_KEY`: Path to your SSH private key

## 🔧 Manual Setup

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- SSH key (for remote deployment)

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/nomad-dormouse/rag-for-standards.git
cd rag-for-standards

# 2. Configure environment
cp .env.template .env
# Edit .env with your settings

# 3. Deploy services (OCR dependencies included automatically)
./deploy.sh

# 4. Optional: Verify OCR functionality
./verify_ocr_deployment.sh
```

## 📊 Features

- **Enhanced PDF Processing**: Handles all PDF types including corrupted and scanned documents with OCR
- **Multi-tier Extraction**: Automatic fallback from standard parsing to PyMuPDF to full OCR
- **Bilingual Interface**: Switch between English 🇬🇧 and Ukrainian 🇺🇦 instantly
- **Dual Response Mode**: Compare answers with and without access to standards
- **Docker Containerisation**: Isolated services with optimised architecture
- **One-time Ingestion**: Storage service runs once to build index, then webapp serves queries
- **Remote Deployment**: One-command deployment to remote servers with Git LFS support
- **RAG Pipeline**: Advanced retrieval with similarity search and source transparency
- **Web Interface**: User-friendly Streamlit application with progressive loading

## 🔍 Enhanced PDF Processing

The system now uses a three-tier approach to handle all PDF documents:

### Processing Strategies

1. **Standard Extraction** (LlamaIndex SimpleDirectoryReader)
   - Fast processing for well-formed PDFs
   - Automatically detects corruption warnings

2. **Robust Extraction** (PyMuPDF with selective OCR)
   - More robust PDF parsing for partially corrupted documents
   - Applies OCR to individual pages when needed

3. **Full OCR Processing** (Tesseract OCR)
   - Converts entire PDF to images and runs OCR
   - Handles completely scanned or corrupted documents

### OCR Setup

OCR dependencies are **automatically included** in the Docker containers. No manual setup required!

```bash
# OCR is automatically available after deployment
./deploy.sh

# Optional: Verify OCR functionality
./verify_ocr_deployment.sh

# For local development outside Docker (optional):
cd rag_storage
./setup_ocr.sh
python test_ocr.py
```

### Language Support

The OCR system supports multiple languages. To add Ukrainian support:

```bash
# Install Ukrainian language pack
sudo apt-get install tesseract-ocr-ukr

# Or for other languages:
# sudo apt-get install tesseract-ocr-rus  # Russian
# sudo apt-get install tesseract-ocr-fra  # French
```

### Processing Results

The enhanced pipeline provides detailed reporting:

```
Files parsing
- Total files: 188
- Successfully parsed (original): 150
- Successfully parsed (PyMuPDF): 20
- Successfully parsed (OCR): 15
- Total successful: 185 (98.4%)
- Corrupted PDFs: 2
- Scanned documents (failed): 1
```

## 🌐 Access

After deployment:
- **Local**: http://localhost:8501
- **Remote**: http://your-server-ip:8501

## 📚 Document Collection

The system processes 188 Ukrainian technical standards (5,167+ pages) including:
- ДСТУ ISO standards
- Technical documentation standards
- Optical and measurement standards
- **Now supports corrupted and scanned documents through OCR**

## 🔍 Usage

1. **Choose Language**: Click 🇬🇧 English or 🇺🇦 Українська buttons at the top
2. **Ask Questions**: Enter queries in English or Ukrainian about technical standards
3. **Compare Responses**: Receive two AI-generated responses:
   - 💭 **Without Standards**: General AI knowledge response
   - 📚 **With Standards**: Response based on retrieved document content
4. **Review Sources**: View retrieved document chunks with similarity scores

## 🔧 Troubleshooting

### OCR Issues

If you encounter OCR-related problems:

```bash
# Test OCR functionality in deployed containers
./verify_ocr_deployment.sh

# For manual testing (local development):
cd rag_storage
python test_ocr.py

# Check container OCR setup
docker-compose run --rm storage tesseract --version
docker-compose run --rm storage pdftoppm -h
```

Common solutions:
- **Linux**: `sudo apt-get install tesseract-ocr poppler-utils`
- **macOS**: `brew install tesseract poppler`

### Performance Considerations

- **Normal PDFs**: Processing time unchanged (~1-2 seconds each)
- **OCR PDFs**: Longer processing time (~10-30 seconds per page)
- **Memory**: OCR processing is memory-intensive for large documents
- **Disk Space**: Temporary images created during OCR (automatically cleaned up)

The enhanced system maintains backward compatibility while dramatically improving document processing success rates from ~50% to ~95%+.