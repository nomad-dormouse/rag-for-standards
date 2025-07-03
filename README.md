# RAG for Ukrainian Technical Standards

A multilingual Retrieval-Augmented Generation (RAG) system for searching and answering questions about Ukrainian technical documentation standards. Supports PDF, DOC, and DOCX files with enhanced OCR processing.

## 🚀 Quick Start

```bash
# Clone and deploy
git clone https://github.com/nomad-dormouse/rag-for-standards.git
cd rag-for-standards
./deploy.sh
```

## 📁 Project Structure

```
rag-for-standards/
├── rag_storage/               # Document processing service
│   ├── standards/             # Technical standards (PDF, DOC, DOCX)
│   ├── dockerfile_storage     # Docker image for document ingestion
│   ├── parsing.py            # Document parsing with OCR fallback
│   ├── embedding.py          # Vector embedding and indexing
│   ├── ingestion.py          # Pipeline orchestrator
│   ├── test_parsing.py       # Parsing functionality tester
│   └── requirements_storage.txt
├── rag_webapp/                # Web application service
│   ├── dockerfile_webapp     # Docker image for web interface
│   ├── webapp.py            # Streamlit application
│   ├── query_engine.py      # RAG query processing
│   ├── localisation.py     # Multi-language support
│   └── requirements_webapp.txt
├── docker-compose.yml        # Container orchestration
├── deploy.sh                # Local deployment script
├── deploy_remotely.sh       # Remote deployment script
└── .env                     # Environment configuration
```

## 🛠️ Configuration

```bash
cp .env.template .env
# Edit .env with your OpenAI API key
```

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `WEBAPP_PORT`: Port for web interface (default: 8501)

## 📊 Features

- **Multi-format Support**: PDF, DOC, DOCX files
- **Enhanced OCR**: Handles corrupted and scanned documents
- **Multilingual**: English, Ukrainian, Russian text recognition
- **Bilingual Interface**: English 🇬🇧 and Ukrainian 🇺🇦
- **Dual Response Mode**: Compare with/without standards access
- **Docker Containerisation**: Isolated services
- **Modular Architecture**: Clean separation of parsing, embedding, and web interface

## 🔍 Document Processing

### Processing Strategy

1. **Standard Extraction** (LlamaIndex)
   - Fast processing for well-formed documents
   - Works with PDF, DOC, DOCX files

2. **Alternative PDF Parser** (PyMuPDF)
   - Robust parsing for partially corrupted PDFs
   - Selective OCR for problematic pages

3. **Full OCR Processing** (Tesseract)
   - Converts PDF pages to images
   - Handles completely scanned documents

### Language Support

- ✅ **English** - International standards
- ✅ **Ukrainian** - ДСТУ standards  
- ✅ **Russian** - Legacy GOST standards

## 🌐 Access

After deployment:
- **Local**: http://localhost:8501
- **Remote**: http://your-server-ip:8501

## 🔍 Usage

1. **Choose Language**: Click 🇬🇧 English or 🇺🇦 Українська
2. **Ask Questions**: Enter queries about technical standards
3. **Compare Responses**: See answers with/without standards access
4. **Review Sources**: View retrieved document chunks

## 🔧 Testing

```bash
# Test parsing locally
cd rag_storage
python test_parsing_local.py
```