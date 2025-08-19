from mcp.server.fastmcp import Tool
import requests
import os
import json

@Tool("register")
def register(model_name: str, run_id: str, description: str = ""):
    """
    Register a model from an MLflow run to the Model Registry.
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
        # First, check if the registered model exists
        get_model_url = f"{databricks_host}/api/2.0/mlflow/registered-models/get"
        response = requests.get(get_model_url, headers=headers, params={"name": model_name})
        
        if response.status_code == 404:
            # Create registered model if it doesn't exist
            create_model_url = f"{databricks_host}/api/2.0/mlflow/registered-models/create"
            create_payload = {
                "name": model_name,
                "description": description or f"AML {model_name} model for alert triage"
            }
            
            response = requests.post(create_model_url, headers=headers, json=create_payload)
            response.raise_for_status()
            
            print(f"Created new registered model: {model_name}")
        
        # Create model version from run
        create_version_url = f"{databricks_host}/api/2.0/mlflow/model-versions/create"
        
        payload = {
            "name": model_name,
            "source": f"runs:/{run_id}/model",
            "description": description or f"Model version from run {run_id}"
        }
        
        response = requests.post(create_version_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        model_version = result.get("model_version", {})
        
        return {
            "status": "success",
            "model_name": model_name,
            "version": model_version.get("version"),
            "run_id": run_id,
            "stage": model_version.get("current_stage"),
            "source": model_version.get("source"),
            "message": f"Model {model_name} registered successfully from run {run_id}"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Model registration failed: {str(e)}"
        }