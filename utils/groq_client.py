import re
from groq import Groq
import streamlit as st
from config import GROQ_API_KEY


def strip_code_fences(text: str) -> str:
    """Remove fenced code blocks (e.g., ```json ... ```) and return plain content."""
    pattern = r"```(?:json|python|markdown)?\s*([\s\S]*?)```"
    return re.sub(pattern, lambda m: m.group(1), text, flags=re.IGNORECASE)


@st.cache_resource(show_spinner=False)
def get_groq_client() -> Groq:
    """Cache Groq client instance."""
    return Groq(api_key=GROQ_API_KEY)


def chat_with_llm(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Send prompt to LLM and return stripped assistant response."""
    client = get_groq_client()
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
    )
    return completion.choices[0].message.content.strip()
