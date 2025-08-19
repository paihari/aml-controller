from mcp.server.fastmcp import Tool
import requests
import json
import os

@Tool("uc_grant")
def uc_grant(catalog: str, schema: str, principal: str, privileges: list):
    """
    Grant Unity Catalog permissions to a principal (user or group).
    """
    
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        results = []
        
        # Grant catalog permissions
        if catalog:
            catalog_url = f"{workspace_url}/api/2.1/unity-catalog/grants"
            catalog_payload = {
                "securable_type": "catalog",
                "securable_name": catalog,
                "principal": principal,
                "changes": [{"add": privileges}]
            }
            
            response = requests.patch(catalog_url, headers=headers, json=catalog_payload)
            response.raise_for_status()
            
            results.append({
                "type": "catalog",
                "name": catalog,
                "principal": principal,
                "privileges": privileges,
                "status": "granted"
            })
        
        # Grant schema permissions
        if schema:
            schema_name = f"{catalog}.{schema}" if catalog else schema
            schema_url = f"{workspace_url}/api/2.1/unity-catalog/grants"
            schema_payload = {
                "securable_type": "schema", 
                "securable_name": schema_name,
                "principal": principal,
                "changes": [{"add": privileges}]
            }
            
            response = requests.patch(schema_url, headers=headers, json=schema_payload)
            response.raise_for_status()
            
            results.append({
                "type": "schema",
                "name": schema_name,
                "principal": principal,
                "privileges": privileges,
                "status": "granted"
            })
        
        return {
            "status": "success",
            "grants": results
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