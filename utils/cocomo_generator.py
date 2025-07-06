import json
import streamlit as st
from utils.groq_client import chat_with_llm, strip_code_fences


# Updated generate_feature_sets to accept suggested_features_text
def generate_feature_sets(software: str, suggested_features_text: str) -> dict:
    """
    Classify suggested features into basic, intermediate, and advanced tiers using LLM.
    
    Args:
        software (str): The project idea (used for context in the prompt).
        suggested_features_text (str): A string containing the suggested features from the ideation API.
        
    Returns:
        dict: A dictionary with 'basic', 'intermediate', and 'advanced' keys,
              each containing a list of classified feature strings.
    """
    prompt = (
        f"You are a senior software architect. Given the following suggested features for a '{software}' project, "
        "classify them into three categories: 'basic', 'intermediate', and 'advanced'. "
        "Each tier should build upon the previous one. "
        "Basic features should cover core functionality, intermediate features should enhance the core, "
        "and advanced features should represent enterprise-level or highly innovative additions.\n\n"
        "Respond **only** in valid JSON with keys 'basic', 'intermediate', and 'advanced'. "
        "The value for each key must be an array of feature strings. "
        "Aim for 4-6 features in 'basic', 6-8 in 'intermediate', and 8-12 in 'advanced'.\n\n"
        "Suggested Features:\n"
        f"{suggested_features_text}\n\n"
        "Example Output:\n"
        "```json\n"
        "{\n"
        "  \"basic\": [\"User Authentication\", \"Basic Data Storage\"],\n"
        "  \"intermediate\": [\"Real-time Chat\", \"File Uploads\"],\n"
        "  \"advanced\": [\"AI-powered Analytics\", \"Microservices Architecture\"]\n"
        "}\n"
        "```"
    )
    
    raw = chat_with_llm(prompt)
    cleaned = strip_code_fences(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        st.error("❌ LLM response for feature classification was not valid JSON. Showing raw text below for debugging.")
        st.text_area("LLM raw response (Feature Classification)", raw, height=200)
        return {"basic": [], "intermediate": [], "advanced": []}

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

**IMPORTANT: Use these exact parameter formats and valid values:**

1. **Function Points:** Use FP types: "EI", "EO", "EQ", "ILF", "EIF"
2. **Reuse Parameters:** 
   - asloc: integer (adapted source lines of code)
   - dm, cm, im: integers 0-100 (percentage values)
   - su_rating: "VL", "L", "N", "H", "VH" (Software Understanding)
   - aa_rating: "1", "2", "3", "4", "5" (Assessment & Assimilation)  
   - unfm_rating: "CF", "MF", "SF", "CFa", "MU" or "CU" (Unfamiliarity)
   - at: integer 0-100 (Automatic Translation percentage)
3. **REVL Parameters:** All integers (SLOC values)
4. **Effort Parameters:**
   - sloc_ksloc: decimal (SLOC in thousands)
   - sced_rating: "VL", "L", "N", "H", "VH" (Schedule rating)

Generate realistic values based on complexity:
- **Basic**: Small scale (1-5 KSLOC), more reuse, standard tech
- **Intermediate**: Medium scale (5-20 KSLOC), moderate reuse
- **Advanced**: Large scale (20+ KSLOC), less reuse, complex tech

Respond with ONLY this JSON format:
{{
  "function_points": {{
    "fp_items": [
      {{"fp_type": "EI", "det": 15, "ftr_or_ret": 2}},
      {{"fp_type": "EO", "det": 12, "ftr_or_ret": 3}},
      {{"fp_type": "ILF", "det": 25, "ftr_or_ret": 4}}
    ],
    "language": "Java"
  }},
  "reuse": {{
    "asloc": 3000,
    "dm": 10,
    "cm": 15,
    "im": 5,
    "su_rating": "N",
    "aa_rating": "2",
    "unfm_rating": "SF",
    "at": 10
  }},
  "revl": {{
    "new_sloc": 8000,
    "adapted_esloc": 2000,
    "revl_percent": 15
  }},
  "effort_schedule": {{
    "sloc_ksloc": 10.0,
    "sced_rating": "N"
  }}
}}

Use these exact value formats. No explanations, just the JSON.
"""
    
    raw = chat_with_llm(prompt)
    cleaned = strip_code_fences(raw)
    
    try:
        params = json.loads(cleaned)
        
        # Validate and fix parameter formats
        if 'reuse' in params:
            reuse = params['reuse']
            # Ensure ratings use correct format
            if reuse.get('su_rating') not in ["VL", "L", "N", "H", "VH"]:
                reuse['su_rating'] = "N"
            if reuse.get('aa_rating') not in ["1", "2", "3", "4", "5"]:
                reuse['aa_rating'] = "3"
            if reuse.get('unfm_rating') not in ["SF", "F", "N", "U", "VU"]:
                reuse['unfm_rating'] = "N"
        
        if 'effort_schedule' in params:
            effort = params['effort_schedule']
            if effort.get('sced_rating') not in ["VL", "L", "N", "H", "VH"]:
                effort['sced_rating'] = "N"
        
        return params
        
    except json.JSONDecodeError:
        st.error("❌ Failed to parse COCOMO parameters JSON. Using fallback parameters.")
        
        # Provide fallback parameters based on complexity level
        complexity_defaults = {
            "basic": {
                "function_points": {
                    "fp_items": [
                        {"fp_type": "EI", "det": 10, "ftr_or_ret": 2},
                        {"fp_type": "EO", "det": 8, "ftr_or_ret": 2},
                        {"fp_type": "ILF", "det": 15, "ftr_or_ret": 3}
                    ],
                    "language": "Python"
                },
                "reuse": {
                    "asloc": 1000,
                    "dm": 10,
                    "cm": 15,
                    "im": 5,
                    "su_rating": "H",
                    "aa_rating": "2",
                    "unfm_rating": "F",
                    "at": 10
                },
                "revl": {
                    "new_sloc": 3000,
                    "adapted_esloc": 1000,
                    "revl_percent": 10
                },
                "effort_schedule": {
                    "sloc_ksloc": 4.0,
                    "sced_rating": "N"
                }
            },
            "intermediate": {
                "function_points": {
                    "fp_items": [
                        {"fp_type": "EI", "det": 15, "ftr_or_ret": 3},
                        {"fp_type": "EO", "det": 12, "ftr_or_ret": 3},
                        {"fp_type": "EQ", "det": 8, "ftr_or_ret": 2},
                        {"fp_type": "ILF", "det": 25, "ftr_or_ret": 4}
                    ],
                    "language": "Java"
                },
                "reuse": {
                    "asloc": 3000,
                    "dm": 20,
                    "cm": 25,
                    "im": 15,
                    "su_rating": "N",
                    "aa_rating": "3",
                    "unfm_rating": "N",
                    "at": 5
                },
                "revl": {
                    "new_sloc": 8000,
                    "adapted_esloc": 3000,
                    "revl_percent": 15
                },
                "effort_schedule": {
                    "sloc_ksloc": 11.0,
                    "sced_rating": "N"
                }
            },
            "advanced": {
                "function_points": {
                    "fp_items": [
                        {"fp_type": "EI", "det": 25, "ftr_or_ret": 4},
                        {"fp_type": "EO", "det": 20, "ftr_or_ret": 4},
                        {"fp_type": "EQ", "det": 15, "ftr_or_ret": 3},
                        {"fp_type": "ILF", "det": 35, "ftr_or_ret": 5},
                        {"fp_type": "EIF", "det": 18, "ftr_or_ret": 3}
                    ],
                    "language": "C++"
                },
                "reuse": {
                    "asloc": 5000,
                    "dm": 35,
                    "cm": 40,
                    "im": 25,
                    "su_rating": "L",
                    "aa_rating": "4",
                    "unfm_rating": "U",
                    "at": 0
                },
                "revl": {
                    "new_sloc": 20000,
                    "adapted_esloc": 5000,
                    "revl_percent": 25
                },
                "effort_schedule": {
                    "sloc_ksloc": 25.0,
                    "sced_rating": "H"
                }
            }
        }
        
        return complexity_defaults.get(level.lower(), complexity_defaults["intermediate"])
