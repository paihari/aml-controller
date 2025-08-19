from mcp.server.fastmcp import Tool
import requests
import json
import os

@Tool("dlt_create_update")
def dlt_create_update(catalog: str, target_schema: str, notebooks: list, continuous: bool, storage: str):
    """
    Create or update a DLT pipeline in Databricks.
    """
    
    # Configuration from environment
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    # Pipeline configuration
    pipeline_config = {
        "name": f"dlt-{catalog}-{target_schema}",
        "storage": storage,
        "configuration": {
            "pipelines.useCatalog": "true"
        },
        "target": f"{catalog}.{target_schema}",
        "catalog": catalog,
        "libraries": [{"notebook": {"path": notebook}} for notebook in notebooks],
        "continuous": continuous,
        "edition": "ADVANCED",
        "channels": ["CURRENT"]
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Check if pipeline exists
        list_url = f"{workspace_url}/api/2.0/pipelines"
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()
        
        existing_pipelines = response.json().get("statuses", [])
        pipeline_name = pipeline_config["name"]
        
        existing_pipeline = None
        for pipeline in existing_pipelines:
            if pipeline.get("spec", {}).get("name") == pipeline_name:
                existing_pipeline = pipeline
                break
        
        if existing_pipeline:
            # Update existing pipeline
            pipeline_id = existing_pipeline["pipeline_id"]
            update_url = f"{workspace_url}/api/2.0/pipelines/{pipeline_id}"
            
            response = requests.put(update_url, headers=headers, json=pipeline_config)
            response.raise_for_status()
            
            action = "updated"
        else:
            # Create new pipeline
            create_url = f"{workspace_url}/api/2.0/pipelines"
            response = requests.post(create_url, headers=headers, json=pipeline_config)
            response.raise_for_status()
            
            result = response.json()
            pipeline_id = result["pipeline_id"]
            action = "created"
        
        # Get pipeline details
        get_url = f"{workspace_url}/api/2.0/pipelines/{pipeline_id}"
        response = requests.get(get_url, headers=headers)
        response.raise_for_status()
        
        pipeline_details = response.json()
        
        return {
            "status": "success",
            "action": action,
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "target": f"{catalog}.{target_schema}",
            "notebooks": notebooks,
            "continuous": continuous
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Unexpected error: {str(e)}"
        }