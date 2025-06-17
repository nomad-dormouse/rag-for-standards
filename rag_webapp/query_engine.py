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
_llm_config = None
_rag_components = None

def initialise_llm():
    """Initialize only the LLM and basic configuration for direct queries"""
    global _llm_config
    if _llm_config is not None:
        return _llm_config
    print("Initialising LLM configuration...")
    load_dotenv()
    config = {
        'openai_api_key': os.getenv("OPENAI_API_KEY"),
        'openai_model_name': os.getenv("OPENAI_MODEL_NAME"),
        'temperature': os.getenv("OPENAI_TEMPERATURE"),
        'system_prompt': t('system_prompt'),
        'context_prompt': t('context_prompt'),
        'question_prompt': t('question_prompt'),
        'answer_prompt': t('answer_prompt'),
        'delimiter_length': int(os.getenv("DELIMITER_LENGTH"))
    }
    Settings.llm = OpenAI(
        model=config['openai_model_name'],
        api_key=config['openai_api_key'],
        temperature=config['temperature']
    )
    _llm_config = config
    print("LLM configuration initialised successfully!")
    return config

def initialise_rag():
    """Initialize RAG components (index, embeddings, retriever) only when needed"""
    global _rag_components, _llm_config
    if _rag_components is not None:
        return _rag_components
    print("Initialising RAG components...")
    llm_config = initialise_llm()
    load_dotenv()
    rag_config = {
        'index_path': os.getenv("INDEX_PATH"),
        'embedding_model_name': os.getenv("EMBEDDING_MODEL_NAME"),
        'similarity_top_k': int(os.getenv("SIMILARITY_TOP_K")),
    }    
    Settings.embed_model = HuggingFaceEmbedding(model_name=rag_config['embedding_model_name'])
    print("Loading index...")
    storage_context = StorageContext.from_defaults(persist_dir=rag_config['index_path'])
    index = load_index_from_storage(storage_context=storage_context)
    retriever = index.as_retriever(similarity_top_k=rag_config['similarity_top_k'])
    prompt_template = PromptTemplate(
        f"""{llm_config['system_prompt']}

{llm_config['context_prompt']} {{context_str}}

{llm_config['question_prompt']} {{query_str}}

{llm_config['answer_prompt']}"""
    )
    query_engine = index.as_query_engine(
        text_qa_template=prompt_template,
        similarity_top_k=rag_config['similarity_top_k']
    )
    _rag_components = {
        'query_engine': query_engine,
        'retriever': retriever,
        'config': {**llm_config, **rag_config}
    }
    print("RAG components initialised successfully!")
    return _rag_components

def reset_query_engine():
    """Reset all components. Call this if you change .env settings"""
    global _llm_config, _rag_components
    _llm_config = None
    _rag_components = None
    print("Query engine reset. Will reinitialise on next query.")

def get_answer_without_RAG(query: str) -> str:
    """Get direct LLM answer without loading index or embeddings"""
    try:
        config = initialise_llm()  # Only initialize LLM, not RAG components
        
        print(f"Processing direct query (without RAG): {query}")
        
        print("\n" + "=" * config['delimiter_length'])
        print("DIRECT LLM QUERY (NO RAG)")
        print("=" * config['delimiter_length'] + "\n")
        print(f"""{config['system_prompt']}

{config['question_prompt']} {query}

{config['answer_prompt']}""")
        print("=" * config['delimiter_length'] + "\n")
        
        prompt_template = PromptTemplate(
            f"""{config['system_prompt']}

{config['question_prompt']} {{query_str}}

{config['answer_prompt']}"""
        )
        formatted_query = prompt_template.format(query_str=query)
        response = Settings.llm.complete(formatted_query)
        print("Got direct response")
        return str(response)
    except Exception as e:
        return f"Error: {str(e)}"

def get_answer_with_RAG(query: str) -> dict:
    """Get RAG answer with retrieved source chunks"""
    try:
        rag_components = initialise_rag()
        query_engine = rag_components['query_engine']
        retriever = rag_components['retriever']
        config = rag_components['config']
        print(f"Processing RAG query: {query}")
        print("Retrieving context...")
        retrieved_nodes = retriever.retrieve(query)
        context_str = "\n\n".join([node.text for node in retrieved_nodes])
        print("\n" + "=" * config['delimiter_length'])
        print("FULL RAG QUERY WITH CONTEXT")
        print("=" * config['delimiter_length'] + "\n")
        print(f"""{config['system_prompt']}

{config['context_prompt']} {context_str}

{config['question_prompt']} {query}

{config['answer_prompt']}""")
        print("="*config['delimiter_length'] + "\n")
        print("Running query...")
        response = query_engine.query(query)
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