from mcp.server.fastmcp import Tool
import requests
import os
import json

@Tool("promote")
def promote(model_name: str, stage: str, version: str = None):
    """
    Promote a model to a specific stage (Staging or Production).
    """
    
    databricks_host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not databricks_host or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # If version not specified, get the latest version
        if not version:
            list_url = f"{databricks_host}/api/2.0/mlflow/registered-models/get"
            response = requests.get(list_url, headers=headers, params={"name": model_name})
            response.raise_for_status()
            
            model_info = response.json()
            versions = model_info.get("registered_model", {}).get("latest_versions", [])
            
            if not versions:
                return {"status": "error", "message": f"No versions found for model {model_name}"}
            
            # Get the latest version number
            version = str(max([int(v["version"]) for v in versions]))
        
        # Transition model version stage
        transition_url = f"{databricks_host}/api/2.0/mlflow/model-versions/transition-stage"
        
        payload = {
            "name": model_name,
            "version": version,
            "stage": stage
        }
        
        response = requests.post(transition_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "status": "success",
            "model_name": model_name,
            "version": version,
            "stage": stage,
            "current_stage": result.get("model_version", {}).get("current_stage"),
            "message": f"Model {model_name} version {version} promoted to {stage}"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "message": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Promotion failed: {str(e)}"
        }