#!/usr/bin/env python3
"""
Simple localisation module for Ukrainian technical standards RAG system.
Supports Ukrainian (uk) and English (en) languages.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Translation dictionary for UI and prompts
TRANSLATIONS = {
    'en': {
        # Webapp interface
        'app_title': '🔍 Search through Ukrainian technical standards using AI',
        'query_input_label': 'Enter your question',
        'query_input_placeholder': 'Enter your question here. For example: "What are the ergonomic requirements for workplace design?"',
        'search_button': '🔍 Search',
        'rag_response_header': '📑 Response WITH access to standards',
        'direct_response_header': '💭 Response WITHOUT access to standards',
        'no_query_message': 'Please enter a question to search',
        'processing_message': 'Processing your query...',
        'tips_header': '❓ How to use',
        'tips_text': '- Choose language using buttons above: 🇬🇧 English or 🇺🇦 Ukrainian\n- Ask a questions in chosen language about Ukrainian technical standards and press Enter or click 🔎 Search button\n- Get two different answers: on the left — 📑 with access to those standards, and on the right — 💭 without access to them',
        # Prompt templates
        'system_prompt': 'You are a helpful assistant who answers questions about Ukrainian standards for technical documentation. You should respond in English.',
        'translation_prompt': 'Translate the question from English to Ukrainian, formulate the answer in Ukrainian using context provided below, and then translate your answer to English. Provide only the answer in English.',
        'context_prompt': 'Given the following information:',
        'question_prompt': 'Question:',
        'answer_prompt': 'Answer:',
    },
    
    'uk': {
        # Webapp interface
        'app_title': '🔍 Пошук по українських технічних стандартах за допомогою ШІ',
        'query_input_label': 'Введіть ваше запитання',
        'query_input_placeholder': 'Введіть ваше запитання тут. Наприклад: "Які ергономічні вимоги до організації робочого місця?"',
        'search_button': '🔍 Пошук',
        'rag_response_header': '📑 Відповідь З доступом до стандартів',
        'direct_response_header': '💭 Відповідь БЕЗ доступу до стандартів',
        'no_query_message': 'Будь ласка, введіть запитання для пошуку',
        'processing_message': 'Обробка вашого запиту...',
        'tips_header': '❓ Як користуватися',
        'tips_text': '- Виберіть мову за допомогою кнопок вище: 🇬🇧 Англійську або 🇺🇦 Українську\n- Поставте запитання на вибраній мові про українські технічні стандарти і натисніть Enter або кнопку 🔎 Пошук\n- Отримайте дві різні відповіді: ліворуч — 📑 з доступом до цих стандартів, а праворуч — 💭 без доступу до них',
        # Prompt templates
        'system_prompt': 'Ти — корисний асистент, який відповідає на запитання про українські стандарти технічної документації.',
        'translation_prompt': 'Якщо запитання поставлене НЕ українською мовою, переклади його на українську, сформуй відповідь українською мовою, а потім переклади свою відповідь на мову, якою було поставлене запитання. Відповідь повинна бути ВИКЛЮЧНО тією мовою, якою було поставлене запитання.',
        'context_prompt': 'Враховуючи наступну інформацію:',
        'question_prompt': 'Запитання:',
        'answer_prompt': 'Відповідь:',
    }
}

def get_language():
    """Get the current language from environment variable or default from DEFAULT_INTERFACE_LANGUAGE."""
    default_lang = os.getenv('DEFAULT_INTERFACE_LANGUAGE').lower()
    return os.getenv('INTERFACE_LANGUAGE', default_lang).lower()

def set_language(lang_code):
    """Set the interface language."""
    if lang_code in TRANSLATIONS:
        os.environ['INTERFACE_LANGUAGE'] = lang_code
        return True
    return False

def t(key):
    """Translate a key to the current language."""
    lang = get_language()
    
    # Fallback to default language if language not found
    if lang not in TRANSLATIONS:
        lang = os.getenv('DEFAULT_INTERFACE_LANGUAGE', 'en').lower()
        # Final fallback to English if default is also invalid
        if lang not in TRANSLATIONS:
            lang = 'en'
    
    # Get translation or fallback to key if not found
    translation = TRANSLATIONS[lang].get(key, key)
    
    return translation

def get_language_names():
    """Get dictionary of language codes to display names."""
    return {
        'en': '🇬🇧 English',
        'uk': '🇺🇦 Українська'
    }