import requests
import streamlit as st
import json
from typing import Dict, Any, Optional

def upload_to_github(project_name: str, folder_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload project structure to GitHub using the API endpoint.
    
    Args:
        project_name (str): Name of the project
        folder_structure (dict): Project folder structure from session state
        
    Returns:
        dict: Response from the API containing success status and message
    """
    
    # API endpoint
    api_url = "https://krivisio.onrender.com/api/tool4/upload-to-github"
    
    try:
        # Prepare the payload
        payload = {
            "name": project_name,
            "structure": folder_structure.get("structure", [])
        }
        
        # Make the API request
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=120  # 2 minutes timeout for GitHub operations
        )
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "status": result.get("status", "success"),
                "message": result.get("message", "Project uploaded successfully"),
                "repo_name": result.get("repo_name", project_name)
            }
        else:
            # Handle different error status codes
            error_message = f"HTTP {response.status_code}: {response.text}"
            
            if response.status_code == 400:
                error_message = "Bad request - Invalid project structure or missing required fields"
            elif response.status_code == 401:
                error_message = "Unauthorized - GitHub credentials not configured properly"
            elif response.status_code == 403:
                error_message = "Forbidden - GitHub token doesn't have required permissions"
            elif response.status_code == 404:
                error_message = "API endpoint not found"
            elif response.status_code == 500:
                error_message = "Server error - Please try again later"
            elif response.status_code == 503:
                error_message = "Service unavailable - GitHub API might be down"
            
            return {
                "success": False,
                "error": error_message,
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out - GitHub upload might take longer than expected. Please try again."
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection error - Unable to connect to GitHub upload service. Please check your internet connection."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid response format from server"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def validate_folder_structure(folder_structure: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the folder structure before uploading to GitHub.
    
    Args:
        folder_structure (dict): Project folder structure
        
    Returns:
        tuple: (is_valid, error_message)
    """
    
    if not folder_structure:
        return False, "Folder structure is empty"
    
    if "name" not in folder_structure:
        return False, "Project name is missing from folder structure"
    
    if "structure" not in folder_structure:
        return False, "Project structure is missing"
    
    if not isinstance(folder_structure["structure"], list):
        return False, "Project structure must be a list"
    
    if len(folder_structure["structure"]) == 0:
        return False, "Project structure cannot be empty"
    
    # Validate individual structure items
    def validate_structure_item(item, path=""):
        if not isinstance(item, dict):
            return False, f"Invalid structure item at {path}: must be a dictionary"
        
        if "type" not in item:
            return False, f"Missing 'type' field in structure item at {path}"
        
        if "name" not in item:
            return False, f"Missing 'name' field in structure item at {path}"
        
        if item["type"] not in ["file", "folder"]:
            return False, f"Invalid type '{item['type']}' at {path}: must be 'file' or 'folder'"
        
        if item["type"] == "folder" and "children" in item:
            if not isinstance(item["children"], list):
                return False, f"Children must be a list for folder at {path}"
            
            for i, child in enumerate(item["children"]):
                is_valid, error_msg = validate_structure_item(child, f"{path}/{item['name']}")
                if not is_valid:
                    return False, error_msg
        
        return True, ""
    
    for i, item in enumerate(folder_structure["structure"]):
        is_valid, error_msg = validate_structure_item(item, f"root[{i}]")
        if not is_valid:
            return False, error_msg
    
    return True, ""

def display_upload_status(upload_result: Dict[str, Any]) -> None:
    """
    Display the upload status with appropriate styling.
    
    Args:
        upload_result (dict): Result from the upload operation
    """
    
    if upload_result["success"]:
        st.success(f"🎉 {upload_result['message']}")
        
        if "repo_name" in upload_result:
            st.info(f"📁 Repository created: **{upload_result['repo_name']}**")
            
        # Show additional success information
        with st.expander("✅ Upload Details"):
            st.markdown(f"**Status:** {upload_result.get('status', 'success')}")
            st.markdown(f"**Repository:** {upload_result.get('repo_name', 'N/A')}")
            st.markdown("**Next Steps:**")
            st.markdown("1. Check your GitHub account for the new repository")
            st.markdown("2. Clone the repository to your local machine")
            st.markdown("3. Start developing your project!")
            
    else:
        st.error(f"❌ Upload failed: {upload_result['error']}")
        
        # Show troubleshooting tips
        with st.expander("🔧 Troubleshooting Tips"):
            st.markdown("""
            **Common solutions:**
            1. **GitHub credentials**: Ensure GITHUB_USERNAME and GITHUB_TOKEN are configured on the server
            2. **Repository name**: Make sure the repository name doesn't already exist
            3. **Network**: Check your internet connection
            4. **Server status**: The upload service might be temporarily unavailable
            5. **Project structure**: Ensure your project structure is valid
            
            **If the problem persists:**
            - Try again after a few minutes
            - Contact support with the error message above
            """)
            
            if "status_code" in upload_result:
                st.markdown(f"**HTTP Status Code:** {upload_result['status_code']}")

def get_project_summary(folder_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of the project structure for display.
    
    Args:
        folder_structure (dict): Project folder structure
        
    Returns:
        dict: Summary statistics
    """
    
    def count_items(structure):
        file_count = 0
        folder_count = 0
        
        for item in structure:
            if item["type"] == "file":
                file_count += 1
            elif item["type"] == "folder":
                folder_count += 1
                if "children" in item:
                    child_files, child_folders = count_items(item["children"])
                    file_count += child_files
                    folder_count += child_folders
        
        return file_count, folder_count
    
    if not folder_structure or "structure" not in folder_structure:
        return {"files": 0, "folders": 0, "name": "Unknown"}
    
    file_count, folder_count = count_items(folder_structure["structure"])
    
    return {
        "name": folder_structure.get("name", "Unknown"),
        "files": file_count,
        "folders": folder_count
    }