# =====================================================
# Configuration & LLM Models
# =====================================================

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


# =====================================================
# API KEYS
# =====================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =====================================================
# LLM MODELS
# =====================================================
def get_deepseek():
    """Returns DeepSeek model for complex reasoning"""
    return ChatOpenAI(
        model="deepseek-chat",
        max_tokens=1500,
        timeout=30,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
    )


def get_gemini():
    """Returns Gemini model with fallback to DeepSeek"""
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    except Exception as e:
        print(f"⚠️ Gemini unavailable: {str(e)[:100]}... Falling back to DeepSeek")
        return get_deepseek()
