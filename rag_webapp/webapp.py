import streamlit as st
from query_engine import get_answer, get_answer_without_RAG, reset_query_engine
from localisation import t, set_language, get_language, get_language_names

# Configure page
st.set_page_config(
    page_title="Ukrainian Technical Standards Search",
    page_icon="🔍",
    layout="wide"
)

# Language buttons
current_lang = get_language()
language_options = get_language_names()
lang_col1, lang_col2, lang_col3 = st.columns([1, 1, 6])
with lang_col1:
    if st.button(language_options["en"], 
                type="primary" if current_lang == "en" else "secondary",
                use_container_width=True):
        if current_lang != "en":
            set_language("en")
            reset_query_engine()
            st.rerun()
with lang_col2:
    if st.button(language_options["uk"], 
                type="primary" if current_lang == "uk" else "secondary",
                use_container_width=True):
        if current_lang != "uk":
            set_language("uk")
            reset_query_engine()
            st.rerun()

# Main content
st.title(t('app_title'))

# Search form
with st.form("search_form"):
    # Query input
    query = st.text_input(
        label=t('query_input_label'),
        placeholder=t('query_input_placeholder'),
        key="query_input",
        label_visibility="collapsed"
    )
    # Search button
    search_col1, search_col2 = st.columns([1, 3])
    with search_col1:
        search_clicked = st.form_submit_button(t('search_button'), type="primary", use_container_width=True)

# Process query when button is clicked or Enter is pressed
if search_clicked and query.strip():
    answer_col1, answer_col2 = st.columns(2)
    with answer_col1:
        st.subheader(t('rag_response_header'))
        with st.spinner(t('processing_message')):
            rag_answer = get_answer(query)
        st.success(rag_answer)
    with answer_col2:
        st.subheader(t('direct_response_header'))
        with st.spinner(t('processing_message')):
            direct_answer = get_answer_without_RAG(query)
        st.info(direct_answer)

elif search_clicked and not query.strip():
    st.warning(t('no_query_message'))

# Add some helpful information at the bottom
with st.expander(t('tips_header')):
    st.markdown(t('tips_text'))