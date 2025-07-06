import os
import json
import re
import requests
import streamlit as st
from groq import Groq

from utils.cocomo_generator import generate_feature_sets, generate_cocomo_parameters
from utils.spec_generator import build_comprehensive_spec_sheet

from api.cocomo_api import post_json, get_health_check

from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# Configuration
# -------------------------------------------------
API_BASE = "https://cocomo2-python.onrender.com"  # public FastAPI instance

groq_api_key = os.getenv("GROQ_API_KEY", "")
if not groq_api_key:
    st.warning("⚠️ GROQ_API_KEY environment variable not found. LLM‑powered actions will not work until it is set.")

# -------------------------------------------------
# Utility helpers
# -------------------------------------------------

def strip_code_fences(text: str) -> str:
    """Remove ```json / ```python / ```markdown … fenced blocks, returning the inner content."""
    pattern = r"```(?:json|python|markdown)?\s*([\s\S]*?)```"
    return re.sub(pattern, lambda m: m.group(1), text, flags=re.IGNORECASE)


@st.cache_resource(show_spinner=False)
def _get_groq_client() -> Groq:
    """Cache a single Groq client per session without serialising it."""
    return Groq(api_key=groq_api_key)


def chat_with_llm(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    """One‑shot chat helper that returns the assistant text only."""
    client = _get_groq_client()
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
    )
    return completion.choices[0].message.content.strip()


# -------------------------------------------------
# Feature generation
# -------------------------------------------------
# -------------------------------------------------
# API convenience wrappers
# -------------------------------------------------


# -------------------------------------------------
# Generate COCOMO-II parameters using LLM
# -------------------------------------------------
# -------------------------------------------------
# Generate comprehensive spec sheet
# -------------------------------------------------

# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------

st.set_page_config(page_title="Project Spec & Effort Estimator", page_icon="📊", layout="wide")

# Header
st.title("📊 Comprehensive Project Specification & Effort Estimator")
st.markdown("Generate detailed project specifications with COCOMO-II effort estimation")

# Check API health
with st.sidebar:
    st.subheader("🔍 API Status")
    if st.button("Check API Health"):
        health = get_health_check()
        if health:
            st.success("✅ API is healthy")
            st.json(health)
        else:
            st.error("❌ API is not responding")

# Main input
st.subheader("1️⃣ Project Description")
software = st.text_input(
    "Describe your software project", 
    placeholder="e.g., Real-time Chat Application for Remote Teams with Video Calling",
    help="Provide a clear, detailed description of the software you want to build"
)

if software:
    # Generate feature sets
    with st.spinner("🤖 Generating feature suggestions..."):
        feature_sets = generate_feature_sets(software)
    
    # Feature selection
    st.subheader("2️⃣ Select Project Complexity & Features")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        level = st.radio(
            "Choose complexity tier",
            ("basic", "intermediate", "advanced"),
            help="Basic: Core functionality, Intermediate: Enhanced features, Advanced: Enterprise-level"
        )
    
    with col2:
        avail_features = feature_sets.get(level, [])
        if avail_features:
            selected_features = st.multiselect(
                f"Select features for {level.title()} level",
                options=avail_features,
                default=avail_features,
                help="Choose the features you want to include in your project"
            )
        else:
            st.warning("No features generated. Please check your input or try again.")
            selected_features = []

    if selected_features:
        st.subheader("3️⃣ COCOMO-II Parameter Generation")
        
        if st.button("🎯 Generate  SpecSheet", type="secondary"):
            with st.spinner("🧠 Analyzing project and generating COCOMO-II parameters..."):
                cocomo_params = generate_cocomo_parameters(software, level, selected_features)
            
            if cocomo_params:
                st.success("✅ Parameters generated successfully!")
                
                # Store in session state for later use
                st.session_state['cocomo_params'] = cocomo_params
            else:
                st.error("❌ Failed to generate parameters. Please try manual input instead.")
    
        
        # Execute API calls and generate spec (only show if parameters are available)
        if 'cocomo_params' in st.session_state and st.session_state['cocomo_params']:
            # if st.button("🚀 Run COCOMO-II Analysis & Generate Specification", type="primary", use_container_width=True):
            with st.spinner("Processing COCOMO-II calculations and generating specification..."):
                
                # Get parameters from session state
                cocomo_params = st.session_state['cocomo_params']
                
                # Prepare payloads from stored parameters
                fp_payload = cocomo_params.get('function_points', {})
                reuse_payload = cocomo_params.get('reuse', {})
                revl_payload = cocomo_params.get('revl', {})
                effort_payload = cocomo_params.get('effort_schedule', {})
                
                
            # Execute API calls
            st.subheader("📊 COCOMO-II Estimation Results")
            
            api_results = {}
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Function Points → SLOC**")
                fp_result = post_json("/size/from_function_points", fp_payload)
                if fp_result:
                    api_results['function_points'] = fp_result
                    st.success(f"✅ UFP: {fp_result.get('ufp', 'N/A')}")
                    st.success(f"✅ SLOC: {fp_result.get('sloc', 'N/A')}")
                else:
                    st.error("❌ Failed")
            
            with col2:
                st.markdown("**Reuse → ESLOC**")
                reuse_result = post_json("/size/from_reuse", reuse_payload)
                if reuse_result:
                    api_results['reuse'] = reuse_result
                    st.success(f"✅ ESLOC: {reuse_result.get('esloc', 'N/A')}")
                else:
                    st.error("❌ Failed")
            
            with col3:
                st.markdown("**REVL Adjustment**")
                revl_result = post_json("/size/adjust_with_revl", revl_payload)
                if revl_result:
                    api_results['revl'] = revl_result
                    st.success(f"✅ Total: {revl_result.get('sloc_total', 'N/A')}")
                    st.success(f"✅ After REVL: {revl_result.get('sloc_after_revl', 'N/A')}")
                else:
                    st.error("❌ Failed")
            
            with col4:
                st.markdown("**Effort & Schedule**")
                effort_result = post_json("/estimate/effort_schedule", effort_payload)
                if effort_result:
                    api_results['effort_schedule'] = effort_result
                    st.success(f"✅ PM: {effort_result.get('person_months', 'N/A')}")
                    st.success(f"✅ Months: {effort_result.get('development_time_months', 'N/A')}")
                    st.success(f"✅ Team: {effort_result.get('avg_team_size', 'N/A')}")
                else:
                    st.error("❌ Failed")
            
            # Generate comprehensive spec sheet
            if api_results:
                st.subheader("📋 Comprehensive Project Specification")
                
                with st.spinner("Generating detailed specification document..."):
                    spec_md = build_comprehensive_spec_sheet(software, level.capitalize(), selected_features, api_results)
                
                st.markdown(spec_md, unsafe_allow_html=True)
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Specification (MD)",
                        data=spec_md,
                        file_name=f"{software.replace(' ', '_')}_specification.md",
                        mime="text/markdown"
                    )
                with col2:
                    # Also offer to download the parameters as JSON
                    params_json = json.dumps(cocomo_params, indent=2)
                    st.download_button(
                        label="📊 Download Parameters (JSON)",
                        data=params_json,
                        file_name=f"{software.replace(' ', '_')}_cocomo_params.json",
                        mime="application/json"
                    )
            else:
                st.error("❌ Unable to generate specification due to API failures")
        # else:
        #     st.info("👆 Please generate or input COCOMO-II parameters first to proceed with the analysis.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Built with ❤️ using Streamlit, Groq Llama-3, and COCOMO-II API<br>
    📊 Comprehensive Project Planning & Effort Estimation Tool
</div>
""", unsafe_allow_html=True)