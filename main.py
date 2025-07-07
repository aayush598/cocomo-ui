import os
import json
import re
import requests
import streamlit as st
from groq import Groq
import asyncio # Import asyncio for async operations

from utils.cocomo_generator import generate_feature_sets, generate_cocomo_parameters
from utils.spec_generator import build_comprehensive_spec_sheet
from utils.generate_directory_structure import generate_directory_structure

from api.cocomo_api import post_json, get_health_check # Assuming these are defined in api/cocomo_api.py

from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# Configuration
# -------------------------------------------------
COCOMO_API_BASE = "https://cocomo2-python.onrender.com"  # COCOMO API base
GITHUB_EXTRACTOR_API_URL = "https://github-project-extractor.onrender.com" # GitHub Extractor API base

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


def chat_with_llm(prompt: str, model: str = "llama-3.1-8b-instant") -> str: # Changed default model for potentially faster response
    """One‑shot chat helper that returns the assistant text only."""
    client = _get_groq_client()
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
    )
    return completion.choices[0].message.content.strip()


async def get_ideated_features_and_tech_stack(project_idea: str, max_repos: int = 3):
    """
    Calls the /ideate endpoint to get suggested features and tech stack.
    """
    url = f"{GITHUB_EXTRACTOR_API_URL}/ideate"
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    payload = {
        "project_idea": project_idea,
        "max_repos": max_repos
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300) # Increased timeout
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        suggested_features = data.get("suggested_features", "")
        suggested_tech_stack = data.get("suggested_tech_stack", "")
        
        return suggested_features, suggested_tech_stack
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error calling ideation API: {e}")
        return "", ""
    except json.JSONDecodeError:
        st.error("❌ Failed to decode JSON response from ideation API.")
        return "", ""

# -------------------------------------------------
# Feature generation (UPDATED to use ideation API)
# -------------------------------------------------

# Assuming generate_feature_sets is in utils/cocomo_generator.py and needs to be updated
# You'll need to modify generate_feature_sets in utils/cocomo_generator.py to accept and process these.
# For now, I'm providing a placeholder that uses the obtained data.

# Original generate_feature_sets (You'll need to modify this in cocomo_generator.py)
# def generate_feature_sets(project_idea: str) -> dict:
#     # ... existing logic
#     pass

# We'll need a new version of generate_feature_sets that takes the suggested features and tech stack
# as input from the ideate endpoint. This function will then use Groq to categorize them.
# The `generate_feature_sets` function should be updated in `utils/cocomo_generator.py`
# For demonstration purposes, I'll put a conceptual update here.

# --- Conceptual Update for `utils/cocomo_generator.py` ---
# This part goes into your `utils/cocomo_generator.py` file
# def generate_feature_sets(project_idea: str, suggested_features_text: str) -> dict:
#     # This function now takes suggested_features_text directly
#     # It would then use Groq to classify these into basic, intermediate, advanced.
#     # Example prompt for Groq within this function:
#     prompt = (
#         f"Given the following suggested features for a '{project_idea}' project, "
#         "classify them into three categories: 'basic', 'intermediate', and 'advanced'. "
#         "Provide the output as a JSON object with keys 'basic', 'intermediate', and 'advanced', "
#         "each containing a list of features. Ensure each feature is a string.\n\n"
#         "Suggested Features:\n"
#         f"{suggested_features_text}\n\n"
#         "Example Output:\n"
#         "```json\n"
#         "{\n"
#         "  \"basic\": [\"User Authentication\", \"Basic Data Storage\"],\n"
#         "  \"intermediate\": [\"Real-time Chat\", \"File Uploads\"],\n"
#         "  \"advanced\": [\"AI-powered Analytics\", \"Microservices Architecture\"]\n"
#         "}\n"
#         "```"
#     )
#     raw_json = chat_with_llm(prompt)
#     try:
#         feature_categories = json.loads(strip_code_fences(raw_json))
#         return feature_categories
#     except json.JSONDecodeError:
#         st.error("Failed to parse LLM response for feature classification.")
#         return {"basic": [], "intermediate": [], "advanced": []}
#
# --- End of Conceptual Update for `utils/cocomo_generator.py` ---

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
    if st.button("Check COCOMO API Health"): # Renamed button for clarity
        health = get_health_check()
        if health:
            st.success("✅ COCOMO API is healthy")
            st.json(health)
        else:
            st.error("❌ COCOMO API is not responding")

# Main input
st.subheader("1️⃣ Project Description")
software = st.text_input(
    "Describe your software project", 
    placeholder="e.g., Real-time Chat Application for Remote Teams with Video Calling",
    help="Provide a clear, detailed description of the software you want to build"
)

# New input for max_repos
max_repos = st.slider(
    "Number of similar repositories to analyze (for ideation)",
    min_value=1,
    max_value=10,
    value=3,
    help="More repositories might lead to richer suggestions but take longer."
)


# Initialize session state for ideated data
if 'suggested_features_text' not in st.session_state:
    st.session_state['suggested_features_text'] = ""
if 'suggested_tech_stack_text' not in st.session_state:
    st.session_state['suggested_tech_stack_text'] = ""
if 'feature_sets_classified' not in st.session_state:
    st.session_state['feature_sets_classified'] = {}


if software:
    # Call the ideation API first
    st.subheader("1.5️⃣ Fetching Ideated Features and Tech Stack")
    if st.button("💡 Get Project Ideas & Tech Stack"):
        with st.spinner("🚀 Fetching suggested features and tech stack from similar projects..."):
            suggested_features, suggested_tech_stack = asyncio.run(get_ideated_features_and_tech_stack(software, max_repos))
            # suggested_tech_stack = "Python \n Streamlit \nFsastAPI"
            st.session_state['suggested_features_text'] = suggested_features
            st.session_state['suggested_tech_stack_text'] = suggested_tech_stack

            if suggested_features:
                st.success("✅ Suggested features and tech stack fetched successfully!")
                with st.expander("Review Suggested Features"):
                    st.markdown(suggested_features)
                with st.expander("Review Suggested Tech Stack"):
                    st.markdown(suggested_tech_stack)
                    print(f"Suggested tech stack : {suggested_tech_stack}")
            else:
                st.warning("No suggestions received. Please try a different project idea or adjust max repos.")
    
    # Only proceed if suggested features are available
    if st.session_state['suggested_features_text']:
        # Generate feature sets based on fetched suggestions
        st.subheader("2️⃣ Classify & Select Project Complexity & Features")
        with st.spinner("🤖 Classifying suggested features into complexity tiers..."):
            # Ensure generate_feature_sets is updated to take suggested_features_text
            # and performs the classification.
            st.session_state['feature_sets_classified'] = generate_feature_sets(
                software, st.session_state['suggested_features_text']
            )
        
        feature_sets = st.session_state['feature_sets_classified']

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
                st.warning("No features classified for this level. Please check the ideation results or try a different level.")
                selected_features = []

        if selected_features:
            st.subheader("3️⃣ COCOMO-II Parameter Generation")
            
            if st.button("🎯 Generate SpecSheet", type="secondary"):
                with st.spinner("🧠 Analyzing project and generating COCOMO-II parameters..."):
                    cocomo_params = generate_cocomo_parameters(software, level, selected_features)
                
                if cocomo_params:
                    st.success("✅ Parameters generated successfully!")
                    st.session_state['cocomo_params'] = cocomo_params
                else:
                    st.error("❌ Failed to generate parameters. Please try manual input instead.")
        
            
            # Execute API calls and generate spec (only show if parameters are available)
            if 'cocomo_params' in st.session_state and st.session_state['cocomo_params']:
                with st.spinner("Processing COCOMO-II calculations and generating specification..."):
                    cocomo_params = st.session_state['cocomo_params']
                    
                    fp_payload = cocomo_params.get('function_points', {})
                    reuse_payload = cocomo_params.get('reuse', {})
                    revl_payload = cocomo_params.get('revl', {})
                    effort_payload = cocomo_params.get('effort_schedule', {})
                                    
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
                        params_json = json.dumps(cocomo_params, indent=2)
                        st.download_button(
                            label="📊 Download Parameters (JSON)",
                            data=params_json,
                            file_name=f"{software.replace(' ', '_')}_cocomo_params.json",
                            mime="application/json"
                        )
                    
                    # Download & Structure Options
                    st.markdown("### 🗂️ Directory Structure Generator")
                    if st.button("📁 Generate Suggested Project Structure"):
                        with st.spinner("📁 Generating directory structure..."):
                            # Pass the suggested tech stack to the directory generator
                            # We'll use a simple split for now; ideally, it should be parsed from the LLM output
                            tech_stack_list = [tech.strip() for tech in st.session_state['suggested_tech_stack_text'].split('\n') if tech.strip()]
                            
                            dir_result = generate_directory_structure(
                                project_desc=software,
                                tech_stack=tech_stack_list, # Pass the ideated tech stack
                                preferences="\n".join(selected_features)
                            )

                        if dir_result:
                            tree_view = dir_result.get("tree_view", "")
                            json_structure = dir_result.get("json_structure", {})

                            st.success("✅ Directory structure generated!")
                            st.markdown("**📂 Tree View:**")
                            st.code(tree_view, language="bash")

                            with st.expander("📦 Raw JSON Structure"):
                                st.json(json_structure)

                            st.download_button(
                                label="📥 Download JSON Structure",
                                data=json.dumps(json_structure, indent=2),
                                file_name=f"{software.replace(' ', '_')}_directory_structure.json",
                                mime="application/json"
                            )
                        else:
                            st.error("❌ Could not generate directory structure.")

                    # Download buttons (duplicate, can be removed)
                    # col1, col2 = st.columns(2)
                    # with col1:
                    #     st.download_button(
                    #         label="📥 Download Specification (MD)",
                    #         data=spec_md,
                    #         file_name=f"{software.replace(' ', '_')}_specification.md",
                    #         mime="text/markdown",
                    #         key="md"
                    #     )
                    # with col2:  
                    #     params_json = json.dumps(cocomo_params, indent=2)
                    #     st.download_button(
                    #         label="📊 Download Parameters (JSON)",
                    #         data=params_json,
                    #         file_name=f"{software.replace(' ', '_')}_cocomo_params.json",
                    #         mime="application/json",
                    #         key="param"
                    #     )

                else:
                    st.error("❌ Unable to generate specification due to API failures")