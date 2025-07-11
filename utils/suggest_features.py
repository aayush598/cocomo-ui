import requests

API_BASE_URL = "https://krivisio.onrender.com"

def suggest_features_and_stack(project_idea: str, max_repos: int = 2) -> dict:
    """
    Sends a POST request to the suggest API and returns the JSON response.

    Args:
        project_idea (str): The idea of the project to analyze.
        max_repos (int): Maximum number of repositories to consider (default is 2).

    Returns:
        dict: Response JSON containing suggested features and tech stack.
    """
    endpoint = f"{API_BASE_URL}/api/tool1/suggest"
    payload = {
        "project_idea": project_idea,
        "max_repos": max_repos
    }
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
