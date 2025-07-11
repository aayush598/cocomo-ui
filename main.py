import streamlit as st
from utils.suggest_features import suggest_features_and_stack

st.title("Suggest Features & Tech Stack")

project_idea = st.text_input("Enter your project idea", "video calling")

if st.button("Suggest Features & Stack"):
    with st.spinner("Fetching suggestions..."):
        result = suggest_features_and_stack(project_idea)  # default max_repos = 2
    
    if "error" in result:
        st.error(f"Error: {result['error']}")
    else:
        st.subheader("Suggested Features")
        st.markdown(result["suggested_features"])
        
        st.subheader("Suggested Tech Stack")
        st.code(result["suggested_tech_stack"], language="text")
        
        st.info(f"Total Repositories Processed: {result['total_repos_processed']}")
