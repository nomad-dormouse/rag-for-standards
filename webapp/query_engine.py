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

# Global variables to store initialised components
_query_engine = None
_retriever = None
_config = None

def initialise_query_engine():
    global _query_engine, _retriever, _config
    
    print("Initialising query engine...")
    
    load_dotenv()
    config = {
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
    _config = config

    Settings.embed_model = HuggingFaceEmbedding(model_name=config['embedding_model_name'])
    Settings.llm = OpenAI(
        model=config['openai_model_name'],
        api_key=config['openai_api_key'],
        temperature=config['temperature']
    )
    
    print("Loading index...")
    storage_context = StorageContext.from_defaults(persist_dir=config['index_path'])
    index = load_index_from_storage(storage_context=storage_context)

    _retriever = index.as_retriever(similarity_top_k=config['similarity_top_k'])
    
    prompt_template = PromptTemplate(
        f"""{config['system_prompt']}

{config['context_prompt']} {{context_str}}

{config['question_prompt']} {{query_str}}

{config['answer_prompt']}"""
    )
    _query_engine = index.as_query_engine(
        text_qa_template=prompt_template,
        similarity_top_k=config['similarity_top_k']
    )
    
    print("Query engine initialised successfully!")

def reset_query_engine():
    """Reset the query engine components. Call this if you change .env settings"""
    global _query_engine, _retriever, _config
    _query_engine = None
    _retriever = None
    _config = None
    print("Query engine reset. Will reinitialise on next query.")

def get_answer(query: str) -> str:
    """Get RAG answer using pre-initialised components"""
    global _query_engine, _retriever, _config
    
    try:
        if _query_engine is None or _retriever is None or _config is None:
            print("Query engine not initialised. Initialising now...")
            initialise_query_engine()
        
        print(f"Processing RAG query: {query}")
        
        print("Retrieving context...")
        retrieved_nodes = _retriever.retrieve(query)
        context_str = "\n\n".join([node.text for node in retrieved_nodes])

        print("\n" + "=" * _config['delimiter_length'])
        print("FULL RAG QUERY WITH CONTEXT")
        print("=" * _config['delimiter_length'] + "\n")
        print(f"""{_config['system_prompt']}

{_config['context_prompt']} {context_str}

{_config['question_prompt']} {query}

{_config['answer_prompt']}""")
        print("="*_config['delimiter_length'] + "\n")
        
        print("Running query...")
        response = _query_engine.query(query)
        
        print("Got RAG response")
        return str(response)
        
    except Exception as e:
        return f"Error: {str(e)}"

def get_answer_without_RAG(query: str) -> str:
    """Get direct LLM answer using pre-initialised components (no RAG)"""
    global _config
    
    try:
        if _config is None:
            print("Query engine not initialised. Initialising now...")
            initialise_query_engine()
        
        print(f"Processing direct query (without RAG): {query}")
        
        print("\n" + "=" * _config['delimiter_length'])
        print("DIRECT LLM QUERY (NO RAG)")
        print("=" * _config['delimiter_length'] + "\n")
        print(f"""{_config['system_prompt']}

{_config['question_prompt']} {query}

{_config['answer_prompt']}""")
        print("=" * _config['delimiter_length'] + "\n")
        
        prompt_template = PromptTemplate(
            f"""{_config['system_prompt']}

{_config['question_prompt']} {{query_str}}

{_config['answer_prompt']}"""
        )
        formatted_query = prompt_template.format(query_str=query)

        response = Settings.llm.complete(formatted_query)
        
        print("Got direct response")
        return str(response)
        
    except Exception as e:
        return f"Error: {str(e)}"