# Technical Documentation Standards RAG Assistant

This application uses RAG (Retrieval-Augmented Generation) to search and answer questions about technical documentation standards.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. Place your technical documentation PDFs in the `docs/` directory.

## Usage

1. First, build the document index:
```bash
python ingest.py
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

3. Open your browser at http://localhost:8501 to use the application.

## Project Structure

- `app.py`: Streamlit frontend
- `config.py`: Configuration settings
- `ingest.py`: Document ingestion and indexing
- `query_engine.py`: RAG pipeline logic
- `docs/`: Directory for technical documentation PDFs
- `index_store/`: Storage for the FAISS index

## Features

- Multi-lingual support through MiniLM-L12-v2 embeddings
- Fast similarity search with FAISS
- Interactive web interface with Streamlit
- Support for PDF documents 