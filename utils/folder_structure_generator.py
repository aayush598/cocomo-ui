# utils/folder_structure_generator.py

import requests

API_URL = "https://krivisio.onrender.com/api/generate/folder-structure"

def generate_folder_structure(project_idea: str, user_selected_features: list, suggested_tech_stack: str, total_repos_processed: int = 3, preferences: str = ""):
    """
    Call the backend API to generate a folder structure based on selected features.

    Args:
        project_idea (str): The main idea of the project.
        user_selected_features (list): Features selected by the user.
        suggested_tech_stack (str): Raw tech stack text from earlier suggestion.
        total_repos_processed (int): Number of GitHub repos processed.
        preferences (str): Optional user preferences.

    Returns:
        dict: The JSON response from the backend containing the folder structure.
    """
    payload = {
        "suggested_features": ",".join(user_selected_features),
        "suggested_tech_stack": suggested_tech_stack,
        "total_repos_processed": total_repos_processed,
        "project_idea": project_idea,
        "preferences": preferences
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
