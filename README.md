# RAG for Ukrainian Technical Standards

A Retrieval-Augmented Generation (RAG) system for searching and answering questions about Ukrainian technical documentation standards using Docker containerisation.

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
│   ├── ingest.py             # Document processing script
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

# 3. Deploy services
./deploy.sh
```

## 📊 Features

- **Multi-language Support**: Ukrainian, English, Russian document processing
- **Docker Containerisation**: Isolated services with optimised architecture
- **One-time Ingestion**: Storage service runs once to build index, then webapp serves queries
- **Remote Deployment**: One-command deployment to remote servers
- **RAG Pipeline**: Advanced retrieval with similarity search
- **Web Interface**: User-friendly Streamlit application
- **Document Processing**: Automated PDF ingestion and indexing

## 🌐 Access

After deployment:
- **Local**: http://localhost:8501
- **Remote**: http://your-server-ip:8501

## 📚 Document Collection

The system processes 188 Ukrainian technical standards (5,167+ pages) including:
- ДСТУ ISO standards
- Technical documentation standards
- Optical and measurement standards

## 🔍 Usage

1. **Ask Questions**: Enter queries in English or Ukrainian
2. **Get Answers**: Receive two AI-generated responses: one based on retrieved context, and another one just from general LLM knowledge