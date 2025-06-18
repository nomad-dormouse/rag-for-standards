import streamlit as st
import os
from query_engine import get_answer_with_RAG, get_answer_without_RAG, update_language_prompts, initialise_query_engine
from localisation import t, set_language, get_language, get_language_names

# Configure page
st.set_page_config(
    page_title="Ukrainian Technical Standards Search",
    page_icon="🔍",
    layout="wide"
)

# Initialise query engine on page load
if 'initialized' not in st.session_state:
    with st.spinner(t('loading_system_message')):
        initialise_query_engine()
        st.session_state.initialized = True

# Language buttons
current_lang = get_language()
language_options = get_language_names()
lang_col1, lang_col2, _ = st.columns([1, 1, 6])
with lang_col1:
    if st.button(language_options["en"], 
                type="primary" if current_lang == "en" else "secondary",
                use_container_width=True):
        if current_lang != "en":
            set_language("en")
            update_language_prompts()
            st.rerun()
with lang_col2:
    if st.button(language_options["uk"], 
                type="primary" if current_lang == "uk" else "secondary",
                use_container_width=True):
        if current_lang != "uk":
            set_language("uk")
            update_language_prompts()
            st.rerun()

# Page title and tips
st.title(f"🔍 {t('app_title')}")
with st.expander(f"❓ {t('tips_header')}"):
    st.markdown(t('tips_text'))

# Search form
with st.form("search_form"):
    query = st.text_input(
        label=t('query_input_label'),
        placeholder=t('query_input_placeholder'),
        key="query_input",
        label_visibility="collapsed"
    )
    search_col1, _ = st.columns([1, 7])
    with search_col1:
        search_clicked = st.form_submit_button(f"🔍 {t('search_button')}", type="primary", use_container_width=True)

# Create empty containers for results
direct_container = st.empty()
rag_container = st.empty()
sources_container = st.empty()

# Process query when button is clicked or Enter is pressed
if search_clicked and query.strip():
    # Clear previous results
    direct_container.empty()
    rag_container.empty()
    sources_container.empty()
    
    # Get direct response without RAG
    with direct_container.container():
        st.subheader(f"💭 {t('direct_response_header')}")
        with st.spinner(t('processing_message')):
            result_without_rag = get_answer_without_RAG(query)
        st.info(result_without_rag)
    
    # Get RAG response and sources
    with rag_container.container():
        st.subheader(f"📚 {t('rag_response_header')}")
        with st.spinner(t('processing_message')):
            result_with_rag = get_answer_with_RAG(query)
        st.success(result_with_rag["answer"])
    with sources_container.container():
        if result_with_rag["total_sources"] > 0:
            st.subheader(f"📑 {t('retrieved_sources_header')}")
            delimiter_length = int(os.getenv("DELIMITER_LENGTH"))
            combined_sources = ""
            for source in result_with_rag["sources"]:
                combined_sources += "=" * delimiter_length + "\n\n"
                combined_sources += f"📄 {t('source_label')} {source['chunk_id']} ({t('similarity_label')}: {source['score']:.3f})\n"
                if source["metadata"]:
                    metadata = source["metadata"]
                    if "file_name" in metadata:
                        combined_sources += f"📁 {t('file_label')}: {metadata['file_name']}\n"
                    if "page_label" in metadata:
                        combined_sources += f"📄 {t('page_label')}: {metadata['page_label']}\n"
                if source["text"].strip():
                    combined_sources += f"\n📝 {t('content_label')}:\n{source['text']}\n\n"
                else:
                    combined_sources += f"⚠️ {t('no_text_content_warning')}\n\n"
            st.text_area(
                label=t('all_sources_label'),
                value=combined_sources,
                height=400,
                disabled=True,
                label_visibility="collapsed",
                key="all_sources"
            )
        else:
            st.warning(t('no_sources_warning'))

elif search_clicked and not query.strip():
    # Clear previous results and show warning
    direct_container.empty()
    rag_container.empty() 
    sources_container.empty()
    st.warning(t('no_query_message'))