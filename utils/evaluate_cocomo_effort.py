import requests

URL = "https://krivisio.onrender.com/api/tool2/cocomo2_evaluation"

def evaluate_cocomo_effort(cocomo_parameters: dict) -> dict:
    """
    Sends the previously‑generated COCOMO II parameters to the evaluation endpoint.

    Args:
        cocomo_parameters (dict): The full JSON returned by
            /api/tool2/cocomo2/generate-parameters.

    Returns:
        dict: Evaluation results or an error message.
    """
    try:
        response = requests.post(URL, json=cocomo_parameters)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return {"error": str(exc)}
