import requests
import json
import streamlit as st


def generate_specification_sheet(project_idea, selected_level, selected_features, cocomo_params):
    """
    Generate a specification sheet for the project using the COCOMO II parameters.
    
    Args:
        project_idea (str): The project idea/name
        selected_level (str): The selected difficulty level (basic, intermediate, advanced)
        selected_features (list): List of selected features
        cocomo_params (dict): COCOMO II parameters from previous step
    
    Returns:
        dict: Response containing the specification sheet or error message
    """
    
    # API endpoint
    url = "https://krivisio.onrender.com/api/generate/specsheet"
    
    # Prepare the request payload
    payload = {
        "software": project_idea,
        "level": selected_level,
        "features": selected_features,
        "api_results": {
            "additionalProp1": {
                "function_points": cocomo_params.get("function_points", {}),
                "reuse": cocomo_params.get("reuse", {}),
                "revl": cocomo_params.get("revl", {}),
                "effort_schedule": cocomo_params.get("effort_schedule", {})
            }
        }
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            return {
                "specsheet": result.get("specsheet", ""),
                "success": True
            }
        else:
            return {
                "error": f"API request failed with status code {response.status_code}: {response.text}",
                "success": False
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out. The API server might be busy. Please try again later.",
            "success": False
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Connection error. Please check your internet connection and try again.",
            "success": False
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"An error occurred while making the request: {str(e)}",
            "success": False
        }
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON response received from the API.",
            "success": False
        }
    except Exception as e:
        return {
            "error": f"An unexpected error occurred: {str(e)}",
            "success": False
        }


def display_specification_sheet(specsheet_content):
    """
    Display the specification sheet in a formatted way in Streamlit.
    
    Args:
        specsheet_content (str): The specification sheet content in markdown format
    """
    
    # Display the specification sheet
    st.subheader("📄 Project Specification Sheet")
    
    # Create a container for better formatting
    with st.container():
        # Display the markdown content
        st.markdown(specsheet_content, unsafe_allow_html=True)
        
        # Add download button for the specification sheet
        st.download_button(
            label="📥 Download Specification Sheet",
            data=specsheet_content,
            file_name="project_specification.md",
            mime="text/markdown",
            help="Download the specification sheet as a markdown file"
        )


def validate_cocomo_params(cocomo_params):
    """
    Validate that the COCOMO parameters contain the required fields.
    
    Args:
        cocomo_params (dict): COCOMO II parameters
    
    Returns:
        tuple: (is_valid, error_message)
    """
    
    required_fields = ["function_points", "reuse", "revl", "effort_schedule"]
    
    for field in required_fields:
        if field not in cocomo_params:
            return False, f"Missing required field: {field}"
    
    # Validate function_points structure
    if "fp_items" not in cocomo_params["function_points"]:
        return False, "Missing fp_items in function_points"
    
    if "language" not in cocomo_params["function_points"]:
        return False, "Missing language in function_points"
    
    # Validate that fp_items is a list
    if not isinstance(cocomo_params["function_points"]["fp_items"], list):
        return False, "fp_items must be a list"
    
    return True, ""


def format_features_for_display(features):
    """
    Format the features list for better display.
    
    Args:
        features (list): List of features
    
    Returns:
        str: Formatted features string
    """
    
    if not features:
        return "No features selected"
    
    formatted_features = []
    for i, feature in enumerate(features, 1):
        formatted_features.append(f"{i}. {feature}")
    
    return "\n".join(formatted_features)


def extract_key_metrics(specsheet_content):
    """
    Extract key metrics from the specification sheet for quick display.
    
    Args:
        specsheet_content (str): The specification sheet content
    
    Returns:
        dict: Extracted key metrics
    """
    
    metrics = {
        "estimated_effort": "N/A",
        "development_time": "N/A",
        "estimated_sloc": "N/A"
    }
    
    try:
        # Simple regex patterns to extract metrics
        import re
        
        # Extract estimated effort
        effort_match = re.search(r'Estimated Effort:\*\*\s*([^*\n]+)', specsheet_content)
        if effort_match:
            metrics["estimated_effort"] = effort_match.group(1).strip()
        
        # Extract development time
        time_match = re.search(r'Development Time:\*\*\s*([^*\n]+)', specsheet_content)
        if time_match:
            metrics["development_time"] = time_match.group(1).strip()
        
        # Extract estimated SLOC
        sloc_match = re.search(r'Estimated SLOC:\s*([^*\n]+)', specsheet_content)
        if sloc_match:
            metrics["estimated_sloc"] = sloc_match.group(1).strip()
            
    except Exception as e:
        st.warning(f"Could not extract metrics: {str(e)}")
    
    return metrics