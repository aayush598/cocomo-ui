import streamlit as st
from utils.suggest_features import suggest_features_and_stack
from utils.classify_features import classify_features_by_level
from utils.generate_cocomo_params import generate_cocomo2_parameters
from utils.evaluate_cocomo_effort import evaluate_cocomo_effort
from utils.folder_structure_generator import generate_folder_structure
from utils.generate_specsheet import generate_specification_sheet, display_specification_sheet, validate_cocomo_params, format_features_for_display, extract_key_metrics
from utils.github_upload import upload_to_github, validate_folder_structure, display_upload_status, get_project_summary

st.set_page_config(page_title="AI Project Assistant", layout="wide")
st.title("AI Project Assistant")

# --------- Step 1: User Input ----------
project_idea = st.text_input("Enter your project idea", "chatbot")

if "suggestions" not in st.session_state:
    st.session_state.suggestions = None

if "classified" not in st.session_state:
    st.session_state.classified = None

# --------- Step 2: Generate Features ----------
if st.button("Generate Suggestions & Classify"):
    with st.spinner("Generating features..."):
        suggestions = suggest_features_and_stack(project_idea)
        if "error" in suggestions:
            st.error(f"Error: {suggestions['error']}")
            st.stop()
        st.session_state.suggestions = suggestions

        # Then classify the features
        classified = classify_features_by_level(project_idea, suggestions["suggested_features"])
        if "error" in classified:
            st.error(f"Classification error: {classified['error']}")
            st.stop()
        st.session_state.classified = classified

        # Reset previously selected category if exists
        st.session_state["selected_category"] = "basic"

# --------- Step 3: Display Output if Available ----------
if st.session_state.suggestions:
    st.subheader("🔹 Suggested Features (raw)")
    st.markdown(st.session_state.suggestions["suggested_features"], unsafe_allow_html=True)

    st.subheader("🔹 Suggested Tech Stack")
    st.code(st.session_state.suggestions["suggested_tech_stack"], language="text")

if st.session_state.classified:
    st.subheader("🔹 Classified Feature Levels")
    cols = st.columns(3)
    for col, level in zip(cols, ["basic", "intermediate", "advanced"]):
        with col:
            st.markdown(f"#### {level.capitalize()}")
            st.write("\n".join(f"• {feat}" for feat in st.session_state.classified[level]))

    # Selection persists here and doesn't trigger a reset
    st.radio(
        "Select the level you want to work on:",
        options=["basic", "intermediate", "advanced"],
        index=["basic", "intermediate", "advanced"].index(st.session_state.get("selected_category", "basic")),
        key="selected_category"  # This binds selection to session_state
    )

    st.success(f"✅ You selected **{st.session_state['selected_category'].capitalize()}** features.")

# ✅ Generate COCOMO II Parameters
if st.session_state.classified and "selected_category" in st.session_state:
    selected_level = st.session_state["selected_category"]
    selected_features = st.session_state.classified[selected_level]

    if st.button("Generate COCOMO II Parameters"):
        with st.spinner("Analyzing software project using COCOMO II..."):
            cocomo_data = generate_cocomo2_parameters(
                software=project_idea,
                level=selected_level,
                features=selected_features
            )
            st.session_state["cocomo_params"] = cocomo_data

            if "error" in cocomo_data:
                st.error(f"Failed to fetch COCOMO II parameters: {cocomo_data['error']}")
            else:
                st.success("✅ COCOMO II Parameters Generated")

                st.subheader("📦 Function Points")
                for item in cocomo_data["function_points"]["fp_items"]:
                    st.json(item)

                st.markdown(f"**Language:** {cocomo_data['function_points']['language']}")

                st.subheader("🔁 Reuse")
                st.json(cocomo_data["reuse"])

                st.subheader("🧠 Re-Engineering Level")
                st.json(cocomo_data["revl"])

                st.subheader("🕒 Effort & Schedule")
                st.json(cocomo_data["effort_schedule"])

# ✅ Evaluate COCOMO II Effort (next step only if params exist)
if "cocomo_params" in st.session_state:
    st.subheader("📉 Step 4: Evaluate COCOMO II Effort")

    if st.button("Evaluate COCOMO II Effort / Schedule"):
        with st.spinner("Evaluating effort and schedule..."):
            eval_result = evaluate_cocomo_effort(st.session_state["cocomo_params"])
            st.session_state["eval_result"] = eval_result

        if "error" in eval_result:
            st.error(f"❌ Evaluation failed: {eval_result['error']}")
        else:
            st.success("🎉 COCOMO II Effort Evaluation Complete")
            results = eval_result["results"]

            st.subheader("📊 Function Points & SLOC")
            st.json(results["function_points"])

            st.subheader("🔁 REVL (Reused & Adapted Code)")
            st.json(results["revl"])

            st.subheader("🕒 Effort & Schedule Estimation")
            st.json(results["effort_schedule"])

# ✅ Generate Specification Sheet
if "cocomo_params" in st.session_state and st.session_state.classified and "selected_category" in st.session_state:
    st.subheader("📄 Step 5: Generate Specification Sheet")
    
    selected_level = st.session_state["selected_category"]
    selected_features = st.session_state.classified[selected_level]
    
    # Display current project details
    with st.expander("📋 Current Project Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Project:** {project_idea}")
            st.markdown(f"**Level:** {selected_level.capitalize()}")
        with col2:
            st.markdown("**Selected Features:**")
            st.markdown(format_features_for_display(selected_features))
    
    if st.button("Generate Specification Sheet"):
        # Validate COCOMO parameters before making API call
        is_valid, error_msg = validate_cocomo_params(st.session_state["cocomo_params"])
        
        if not is_valid:
            st.error(f"❌ Invalid COCOMO parameters: {error_msg}")
            st.info("Please regenerate COCOMO II parameters before creating the specification sheet.")
        else:
            with st.spinner("Generating specification sheet..."):
                specsheet_result = generate_specification_sheet(
                    project_idea=project_idea,
                    selected_level=selected_level,
                    selected_features=selected_features,
                    cocomo_params=st.session_state["eval_result"]
                )
                
                if specsheet_result["success"]:
                    st.success("✅ Specification Sheet Generated Successfully!")
                    st.session_state["specsheet"] = specsheet_result["specsheet"]
                                       
                    # Display the specification sheet
                    display_specification_sheet(specsheet_result["specsheet"])
                    
                else:
                    st.error(f"❌ Failed to generate specification sheet: {specsheet_result['error']}")
                    
                    # Show troubleshooting tips
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common solutions:**
                        1. Check your internet connection
                        2. Try again after a few minutes (server might be busy)
                        3. Regenerate COCOMO II parameters if they seem incomplete
                        4. Contact support if the problem persists
                        """)

# ✅ Generate Folder Structure
if st.session_state.classified and "selected_category" in st.session_state:
    selected_level = st.session_state["selected_category"]
    selected_features = st.session_state.classified[selected_level]

    if st.button("Generate Folder Structure"):
        with st.spinner("Generating folder structure based on your selected features..."):
            folder_data = generate_folder_structure(
                project_idea=project_idea,
                user_selected_features=selected_features,
                suggested_tech_stack=st.session_state.suggestions["suggested_tech_stack"],
                total_repos_processed=st.session_state.suggestions.get("total_repos_processed", 3)
            )

        if "error" in folder_data:
            st.error(f"❌ Failed to generate folder structure: {folder_data['error']}")
        else:
            st.success("✅ Folder Structure Generated")
            st.session_state["folder_structure"] = folder_data["folder_structure"]["json_structure"]
            
            st.subheader("📁 Folder Structure (JSON)")
            st.json(folder_data["folder_structure"]["json_structure"])

            st.subheader("📂 Tree View")
            st.code(folder_data["folder_structure"]["tree_view"], language="text")

# ✅ Upload to GitHub
if "folder_structure" in st.session_state:
    st.subheader("🚀 Step 6: Upload to GitHub")
    
    # Display project summary before upload
    project_summary = get_project_summary(st.session_state["folder_structure"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Project Name", project_summary["name"])
    with col2:
        st.metric("📄 Files", project_summary["files"])
    with col3:
        st.metric("🗂️ Folders", project_summary["folders"])
    
    # Option to customize repository name
    repo_name = st.text_input(
        "Repository Name (optional)", 
        value=project_idea,
        help="Leave empty to use the project idea as repository name"
    )
    
    # Use project_idea if repo_name is empty
    final_repo_name = repo_name.strip() if repo_name.strip() else project_idea
    
    # Validate folder structure before showing upload button
    is_valid, validation_error = validate_folder_structure(st.session_state["folder_structure"])
    
    if not is_valid:
        st.error(f"❌ Invalid folder structure: {validation_error}")
        st.info("Please regenerate the folder structure before uploading to GitHub.")
    else:
        # Show upload button
        if st.button("🚀 Upload to GitHub", type="primary"):
            with st.spinner("Uploading project to GitHub... This may take a few minutes."):
                upload_result = upload_to_github(
                    project_name=final_repo_name,
                    folder_structure=st.session_state["folder_structure"]
                )
                
                # Store upload result in session state
                st.session_state["upload_result"] = upload_result
                
                # Display upload status
                display_upload_status(upload_result)
        
        # Show upload requirements
        with st.expander("ℹ️ GitHub Upload Requirements"):
            st.markdown("""
            **Requirements for GitHub upload:**
            1. **Server Configuration**: The server must have valid GitHub credentials configured
            2. **Repository Name**: Must be unique in your GitHub account
            3. **Internet Connection**: Stable connection required for upload
            4. **Valid Structure**: Project must have a valid folder structure
            
            **What happens during upload:**
            - Creates a new repository in your GitHub account
            - Uploads all files and folders according to your project structure
            - Initializes the repository with basic files (README, .gitignore, etc.)
            - Sets up the complete project structure as generated
            
            **Note**: The upload process may take 1-2 minutes depending on project size.
            """)

# Display previous upload result if available
if "upload_result" in st.session_state:
    st.subheader("📋 Last Upload Status")
    display_upload_status(st.session_state["upload_result"])

# -------- Optional Debug --------
with st.sidebar.expander("🔧 Session State"):
    st.write(st.session_state)