import requests
import streamlit as st
from config import API_BASE
def post_json(endpoint: str, payload: dict | None):
    if not payload:
        return None
    url = f"{API_BASE}{endpoint}"
    try:
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


def get_health_check():
    """Check API health"""
    try:
        res = requests.get(f"{API_BASE}/", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❌ API Health Check Failed: {str(e)}")
        return None

