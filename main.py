import streamlit as st
from utils.suggest_features import suggest_features_and_stack
from utils.classify_features import classify_features_by_level
from utils.generate_cocomo_params import generate_cocomo2_parameters
from utils.evaluate_cocomo_effort import evaluate_cocomo_effort
from utils.folder_structure_generator import generate_folder_structure



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

    st.subheader("🔹 Suggested Tech Stack")
    st.code(st.session_state.suggestions["suggested_tech_stack"], language="text")

if st.session_state.classified:
    st.subheader("🔹 Classified Feature Levels")
    cols = st.columns(3)
    for col, level in zip(cols, ["basic", "intermediate", "advanced"]):
        with col:
            st.markdown(f"#### {level.capitalize()}")
            st.write("\n".join(f"• {feat}" for feat in st.session_state.classified[level]))

    # Selection persists here and doesn’t trigger a reset
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
            st.subheader("📁 Folder Structure (JSON)")
            st.json(folder_data["folder_structure"]["json_structure"])

            st.subheader("📂 Tree View")
            st.code(folder_data["folder_structure"]["tree_view"], language="text")

# -------- Optional Debug --------
with st.sidebar.expander("🔧 Session State"):
    st.write(st.session_state)
