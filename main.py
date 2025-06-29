import os
import json
import re
import requests
import streamlit as st
from groq import Groq
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

def generate_feature_sets(software: str) -> dict:
    """Ask the LLM for feature suggestions across three complexity tiers and return a dict."""
    system_prompt = (
        "You are a senior software architect. For the given software idea, propose concise but descriptive "
        "feature lists for three tiers of project maturity: Basic, Intermediate, and Advanced. "
        "Each tier should build upon the previous one. Respond **only** "
        "in valid JSON with keys 'basic', 'intermediate', 'advanced'. The value for each key must be an array "
        "of feature strings. Basic should have 4-6 features, Intermediate 6-8 features, Advanced 8-12 features."
    )
    raw = chat_with_llm(f"{system_prompt}\n\nSoftware Idea: {software}")
    cleaned = strip_code_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        st.error("❌ LLM response was not valid JSON. Showing raw text below for debugging.")
        st.text_area("LLM raw response", raw, height=200)
        return {"basic": [], "intermediate": [], "advanced": []}


# -------------------------------------------------
# API convenience wrappers
# -------------------------------------------------

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


# -------------------------------------------------
# Generate COCOMO-II parameters using LLM
# -------------------------------------------------

def generate_cocomo_parameters(software: str, level: str, features: list[str]) -> dict:
    """Generate realistic COCOMO-II parameters based on project description and features"""
    
    features_text = "\n".join(f"- {feature}" for feature in features)
    
    prompt = f"""
You are a software estimation expert with deep knowledge of COCOMO-II methodology. Based on the project description below, generate realistic and appropriate input parameters for all four COCOMO-II API endpoints.

**Project Details:**
- Software: {software}
- Complexity Level: {level}
- Selected Features:
{features_text}

Generate parameters for these four endpoints with realistic values:

1. **Function Points (fp_items + language):**
   - Analyze the features and determine appropriate Function Point items
   - Use FP types: EI (External Input), EO (External Output), EQ (External Inquiry), ILF (Internal Logical File), EIF (External Interface File)
   - Consider complexity levels: Simple (Low DET/FTR), Average (Medium), Complex (High DET/FTR)
   - Choose appropriate programming language

2. **Reuse Parameters:**
   - Consider how much existing code might be reused/adapted
   - Estimate modification percentages based on project type
   - Set appropriate ratings for understanding and familiarity

3. **REVL Parameters:**
   - Consider requirements volatility based on project complexity
   - Estimate new vs adapted code ratios

4. **Effort Parameters:**
   - Consider final SLOC estimates
   - Set schedule constraints based on project urgency

Respond with ONLY a valid JSON object with these exact keys:
```json
{{
  "function_points": {{
    "fp_items": [
      {{"fp_type": "string", "det": number, "ftr_or_ret": number}},
      // 3-6 items based on project complexity
    ],
    "language": "string"
  }},
  "reuse": {{
    "asloc": number,
    "dm": number,
    "cm": number, 
    "im": number,
    "su_rating": "string",
    "aa_rating": "string",
    "unfm_rating": "string",
    "at": number
  }},
  "revl": {{
    "new_sloc": number,
    "adapted_esloc": number,
    "revl_percent": number
  }},
  "effort_schedule": {{
    "sloc_ksloc": number,
    "sced_rating": "string"
  }}
}}
```

Make the values realistic and consistent with each other. Consider:
- Basic projects: Smaller scale, more reuse, standard technologies
- Intermediate projects: Medium scale, moderate reuse, some new technologies  
- Advanced projects: Large scale, less reuse, cutting-edge technologies

Provide only the JSON, no explanations or markdown formatting.
"""
    
    raw = chat_with_llm(prompt)
    cleaned = strip_code_fences(raw)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        st.error("❌ Failed to parse COCOMO parameters JSON. Showing raw response for debugging.")
        st.text_area("Raw LLM response", raw, height=200)
        return {}

# -------------------------------------------------
# Generate comprehensive spec sheet
# -------------------------------------------------

def build_comprehensive_spec_sheet(software: str, level: str, features: list[str], api_results: dict) -> str:
    """Generate a comprehensive spec sheet using project info and API results"""
    
    # Extract key metrics from API results
    fp_result = api_results.get('function_points', {})
    reuse_result = api_results.get('reuse', {})
    revl_result = api_results.get('revl', {})
    effort_result = api_results.get('effort_schedule', {})
    
    sloc = fp_result.get('sloc', 'N/A')
    esloc = reuse_result.get('esloc', 'N/A')
    total_sloc = revl_result.get('sloc_after_revl', 'N/A')
    person_months = effort_result.get('person_months', 'N/A')
    dev_time = effort_result.get('development_time_months', 'N/A')
    team_size = effort_result.get('avg_team_size', 'N/A')
    
    prompt = (
        f"You are a senior technical project manager. Create a comprehensive project specification document in Markdown "
        f"for the **{software}** project at **{level}** complexity level.\n\n"
        f"**Project Features to Include:**\n" +
        "\n".join(f"- {f}" for f in features) +
        f"\n\n**COCOMO-II Estimation Results:**\n"
        f"- Estimated SLOC: {sloc}\n"
        f"- Equivalent SLOC (with reuse): {esloc}\n"
        f"- Total SLOC (with REVL): {total_sloc}\n"
        f"- Estimated Effort: {person_months} person-months\n"
        f"- Development Time: {dev_time} months\n"
        f"- Average Team Size: {team_size} people\n\n"
        "Create a professional specification document with these sections:\n"
        "1. **Executive Summary** - Brief overview and key metrics\n"
        "2. **Project Overview** - Detailed description and objectives\n"
        "3. **Functional Requirements** - Detailed breakdown of each feature\n"
        "4. **Non-Functional Requirements** - Performance, security, scalability\n"
        "5. **Technical Architecture** - System design and tech stack recommendations\n"
        "6. **Development Estimation** - Based on COCOMO-II results with timeline breakdown\n"
        "7. **Risk Assessment** - Potential challenges and mitigation strategies\n"
        "8. **Deliverables & Milestones** - What will be delivered and when\n"
        "9. **Acceptance Criteria** - How success will be measured\n"
        "10. **Resource Requirements** - Team structure and skills needed\n\n"
        "Make it professional, detailed, and actionable. Use the COCOMO-II metrics to provide realistic timelines and resource estimates."
    )
    
    return chat_with_llm(prompt)


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
        
        # Option to auto-generate or manual input
        param_mode = st.radio(
            "Choose parameter input method:",
            ("🤖 Auto-generate using AI", "✋ Manual input"),
            horizontal=True,
            help="AI generation analyzes your project to create realistic parameters automatically"
        )
        
        if param_mode == "🤖 Auto-generate using AI":
            # Auto-generation section
            st.info("💡 AI will analyze your project description and features to generate appropriate COCOMO-II parameters")
            
            if st.button("🎯 Generate Parameters with AI", type="secondary"):
                with st.spinner("🧠 Analyzing project and generating COCOMO-II parameters..."):
                    cocomo_params = generate_cocomo_parameters(software, level, selected_features)
                
                if cocomo_params:
                    st.success("✅ Parameters generated successfully!")
                    
                    # Store in session state for later use
                    st.session_state['cocomo_params'] = cocomo_params
                    
                    # Display generated parameters in expandable sections
                    with st.expander("📐 Generated Function Points Parameters", expanded=True):
                        fp_params = cocomo_params.get('function_points', {})
                        st.json(fp_params)
                    
                    with st.expander("🔁 Generated Reuse Parameters"):
                        reuse_params = cocomo_params.get('reuse', {})
                        st.json(reuse_params)
                    
                    with st.expander("🧮 Generated REVL Parameters"):
                        revl_params = cocomo_params.get('revl', {})
                        st.json(revl_params)
                    
                    with st.expander("🧠 Generated Effort Parameters"):
                        effort_params = cocomo_params.get('effort_schedule', {})
                        st.json(effort_params)
                else:
                    st.error("❌ Failed to generate parameters. Please try manual input instead.")
        
        else:
            # Manual input section (original code)
            st.markdown("**Manual Parameter Input**")
            
            # Create tabs for different input sections
            tab1, tab2, tab3, tab4 = st.tabs(["📐 Function Points", "🔁 Reuse Parameters", "🧮 REVL Parameters", "🧠 Effort Parameters"])
            
            with tab1:
                st.markdown("**Function Points to SLOC Conversion**")
                
                # Dynamic function point items
                num_fp_items = st.number_input("Number of Function Point Items", min_value=1, max_value=10, value=3)
                
                fp_items = []
                fp_types = ["EI", "EO", "EQ", "ILF", "EIF"]
                
                for i in range(num_fp_items):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        fp_type = st.selectbox(f"FP Type {i+1}", fp_types, key=f"fp_type_{i}")
                    with col_b:
                        det = st.number_input(f"DET {i+1}", min_value=1, max_value=100, value=10, key=f"det_{i}")
                    with col_c:
                        ftr_ret = st.number_input(f"FTR/RET {i+1}", min_value=1, max_value=50, value=2, key=f"ftr_{i}")
                    
                    fp_items.append({"fp_type": fp_type, "det": det, "ftr_or_ret": ftr_ret})
                
                language = st.selectbox("Programming Language", 
                                      ["Java", "C++", "Python", "JavaScript", "C#", "PHP", "Ruby", "Go"], 
                                      index=0)
            
            with tab2:
                st.markdown("**Reuse/Adaptation Parameters**")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    asloc = st.number_input("Adapted SLOC", min_value=0, value=3000, 
                                          help="Lines of adapted/reused code")
                    dm = st.slider("Design Modified (%)", 0, 100, 10, 
                                 help="Percentage of design modification needed")
                    cm = st.slider("Code Modified (%)", 0, 100, 15, 
                                 help="Percentage of code modification needed")
                    im = st.slider("Integration Modified (%)", 0, 100, 5, 
                                 help="Percentage of integration effort needed")
                
                with col_b:
                    su_rating = st.selectbox("Software Understanding", ["VL", "L", "N", "H", "VH"], index=2)
                    aa_rating = st.selectbox("Assessment & Assimilation", ["1", "2", "3", "4", "5"], index=1)
                    unfm_rating = st.selectbox("Unfamiliarity", ["SF", "F", "N", "U", "VU"], index=0)
                    at = st.slider("Automatic Translation (%)", 0, 100, 10)
            
            with tab3:
                st.markdown("**REVL (Requirements Evolution) Parameters**")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    new_sloc = st.number_input("New SLOC", min_value=0, value=5000,
                                             help="Lines of new code to be developed")
                    adapted_esloc = st.number_input("Adapted ESLOC", min_value=0, value=3000,
                                                  help="Equivalent SLOC from reuse calculation")
                
                with col_b:
                    revl_percent = st.slider("REVL Percentage", 0, 50, 10,
                                           help="Requirements volatility percentage")
            
            with tab4:
                st.markdown("**Effort & Schedule Parameters**")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    sloc_ksloc = st.number_input("Total SLOC (in thousands)", min_value=0.1, value=8.8, step=0.1,
                                               help="Total SLOC after REVL adjustment (in KSLOC)")
                
                with col_b:
                    sced_rating = st.selectbox("Schedule Constraint", 
                                             ["VL", "L", "N", "H", "VH"], 
                                             index=2,
                                             help="Schedule pressure rating")
            
            # Store manual parameters in session state
            manual_params = {
                "function_points": {
                    "fp_items": fp_items,
                    "language": language
                },
                "reuse": {
                    "asloc": asloc,
                    "dm": dm,
                    "cm": cm,
                    "im": im,
                    "su_rating": su_rating,
                    "aa_rating": aa_rating,
                    "unfm_rating": unfm_rating,
                    "at": at
                },
                "revl": {
                    "new_sloc": new_sloc,
                    "adapted_esloc": adapted_esloc,
                    "revl_percent": revl_percent
                },
                "effort_schedule": {
                    "sloc_ksloc": sloc_ksloc,
                    "sced_rating": sced_rating
                }
            }
            st.session_state['cocomo_params'] = manual_params
        
        # Execute API calls and generate spec (only show if parameters are available)
        if 'cocomo_params' in st.session_state and st.session_state['cocomo_params']:
            st.subheader("4️⃣ Generate Analysis")
            if st.button("🚀 Run COCOMO-II Analysis & Generate Specification", type="primary", use_container_width=True):
                with st.spinner("Processing COCOMO-II calculations and generating specification..."):
                    
                    # Get parameters from session state
                    cocomo_params = st.session_state['cocomo_params']
                    
                    # Prepare payloads from stored parameters
                    fp_payload = cocomo_params.get('function_points', {})
                    reuse_payload = cocomo_params.get('reuse', {})
                    revl_payload = cocomo_params.get('revl', {})
                    effort_payload = cocomo_params.get('effort_schedule', {})
                    
                    # Display the parameters being used
                    with st.expander("📋 Parameters Being Used", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown("**Function Points**")
                            st.json(fp_payload)
                        with col2:
                            st.markdown("**Reuse**")
                            st.json(reuse_payload)
                        with col3:
                            st.markdown("**REVL**")
                            st.json(revl_payload)
                        with col4:
                            st.markdown("**Effort**")
                            st.json(effort_payload)
                
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
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Specification as Markdown",
                        data=spec_md,
                        file_name=f"{software.replace(' ', '_')}_specification.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("❌ Unable to generate specification due to API failures")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Built with ❤️ using Streamlit, Groq Llama-3, and COCOMO-II API<br>
    📊 Comprehensive Project Planning & Effort Estimation Tool
</div>
""", unsafe_allow_html=True)