import requests

API_BASE_URL = "https://krivisio.onrender.com"

def classify_features_by_level(project_idea: str, suggested_features_text: str) -> dict:
    """
    Sends the suggested features to the classify-features endpoint to get feature levels.

    Args:
        project_idea (str): Project idea title.
        suggested_features_text (str): Suggested features content in markdown/text.

    Returns:
        dict: Response JSON containing basic, intermediate, and advanced features.
    """
    endpoint = f"{API_BASE_URL}/api/tool1/classify-features"
    payload = {
        "project_idea": project_idea,
        "suggested_features_text": suggested_features_text
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
