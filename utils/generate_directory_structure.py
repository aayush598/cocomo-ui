import requests
import streamlit as st

def generate_directory_structure(project_desc: str, tech_stack: list[str], preferences: str = "") -> dict:
    """Send project info to directory structure generation API"""
    url = "https://krip-ai-folderstructuregenerator.onrender.com/generate"
    payload = {
        "project_desc": project_desc,
        "tech_stack": tech_stack,
        "preferences": preferences
    }
    try:
        res = requests.post(url, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"❌ Directory structure generation failed: {str(e)}")
        return {}
