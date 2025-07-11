import requests

def generate_cocomo2_parameters(software, level, features):
    url = "https://krivisio.onrender.com/api/tool2/cocomo2/generate-parameters"
    payload = {
        "software": software,
        "level": level,
        "features": features
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
