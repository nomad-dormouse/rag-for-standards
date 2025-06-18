#!/usr/bin/env python3
"""
Query engine for Ukrainian technical standards RAG system.
Provides RAG-based and direct LLM responses for comparison.
"""

import os
from dotenv import load_dotenv
from llama_index.core import load_index_from_storage, Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from localisation import t
import streamlit as st

# Global variables to store initialised components
_query_engine = None
_retriever = None
_config = None

@st.cache_resource
def initialise_query_engine():
    """Initialise LLM and RAG components. Cached with Streamlit decorator to run only once per session."""
    print("Initialising query engine...")
    global _query_engine, _retriever, _config
    
    print("Loading .env file and setting up config...")
    load_dotenv()
    _config = {
        'index_path': os.getenv("INDEX_PATH"),
        'embedding_model_name': os.getenv("EMBEDDING_MODEL_NAME"),
        'openai_api_key': os.getenv("OPENAI_API_KEY"),
        'openai_model_name': os.getenv("OPENAI_MODEL_NAME"),
        'temperature': os.getenv("OPENAI_TEMPERATURE"),
        'similarity_top_k': int(os.getenv("SIMILARITY_TOP_K")),
        'system_prompt': t('system_prompt'),
        'context_prompt': t('context_prompt'),
        'question_prompt': t('question_prompt'),
        'answer_prompt': t('answer_prompt'),
        'delimiter_length': int(os.getenv("DELIMITER_LENGTH"))
    }

    print("Setting up LLM and embeddings...")
    Settings.llm = OpenAI(
        model=_config['openai_model_name'],
        api_key=_config['openai_api_key'],
        temperature=_config['temperature']
    )
    Settings.embed_model = HuggingFaceEmbedding(model_name=_config['embedding_model_name'])
    
    print("Loading index...")
    storage_context = StorageContext.from_defaults(persist_dir=_config['index_path'])
    index = load_index_from_storage(storage_context=storage_context)
    
    print("Initialising retriever and query engine...")
    _retriever = index.as_retriever(similarity_top_k=_config['similarity_top_k'])
    prompt_template = PromptTemplate(
        f"{_config['system_prompt']}\n
        {_config['context_prompt']} {{context_str}}\n
        {_config['question_prompt']} {{query_str}}\n
        {_config['answer_prompt']}"
    )
    _query_engine = index.as_query_engine(
        text_qa_template=prompt_template,
        similarity_top_k=_config['similarity_top_k']
    )
    
    print("Query engine initialised successfully!")

def update_language_prompts():
    """Update query engine prompts for language change without reloading index."""
    global _query_engine, _config
    _config['system_prompt'] = t('system_prompt')
    _config['context_prompt'] = t('context_prompt')
    _config['question_prompt'] = t('question_prompt')
    _config['answer_prompt'] = t('answer_prompt')
    prompt_template = PromptTemplate(
        f"{_config['system_prompt']}\n
        {_config['context_prompt']} {{context_str}}\n
        {_config['question_prompt']} {{query_str}}\n
        {_config['answer_prompt']}"
    )
    index = _retriever._index
    _query_engine = index.as_query_engine(
        text_qa_template=prompt_template,
        similarity_top_k=_config['similarity_top_k']
    )
    print("Query engine updated with new language prompts.")

def get_answer_without_RAG(query: str) -> str:
    """Get direct LLM answer without using RAG components"""
    global _config
    try:
        print(f"Processing direct query (without RAG): {query}")
        print("\n" + "=" * _config['delimiter_length'])
        print("DIRECT LLM QUERY (NO RAG)")
        print("=" * _config['delimiter_length'] + "\n")
        print(f"{_config['system_prompt']}\n
              {_config['question_prompt']} {query}\n
              {_config['answer_prompt']}")
        print("=" * _config['delimiter_length'] + "\n")
        
        prompt_template = PromptTemplate(
            f"{_config['system_prompt']}\n
            n{_config['question_prompt']} {{query_str}}\n
            {_config['answer_prompt']}"
        )
        formatted_query = prompt_template.format(query_str=query)
        response = Settings.llm.complete(formatted_query)
        print("Got direct response")
        return str(response)
    except Exception as e:
        return f"Error: {str(e)}"

def get_answer_with_RAG(query: str) -> dict:
    """Get RAG answer with retrieved context"""
    global _query_engine, _retriever, _config
    
    try:
        print(f"Processing RAG query: {query}")
        
        print("Retrieving context...")
        retrieved_nodes = _retriever.retrieve(query)
        context_str = "\n\n".join([node.text for node in retrieved_nodes])

        print("\n" + "=" * _config['delimiter_length'])
        print("FULL RAG QUERY WITH CONTEXT")
        print("=" * _config['delimiter_length'] + "\n")
        print(f"{_config['system_prompt']}\n
              {_config['context_prompt']} {context_str}\n
              {_config['question_prompt']} {query}\n
              {_config['answer_prompt']}")
        print("="*_config['delimiter_length'] + "\n")
        
        print("Running query...")
        response = _query_engine.query(query)
        print("Got RAG response")
        
        sources = []
        for i, node in enumerate(retrieved_nodes):
            source_info = {
                "chunk_id": i + 1,
                "text": node.text,
                "score": getattr(node, 'score', 0.0),
                "metadata": node.metadata if hasattr(node, 'metadata') else {}
            }
            sources.append(source_info)

        return {
            "answer": str(response),
            "sources": sources,
            "total_sources": len(sources)
        }
        
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "total_sources": 0
        }