from mcp.server.fastmcp import Tool
import requests
import os
import json

@Tool("pbi_refresh")
def pbi_refresh(dataset_id: str, workspace_id: str = None):
    """
    Trigger a refresh of a Power BI dataset.
    """
    
    # Get Power BI service credentials
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("POWERBI_CLIENT_ID")
    client_secret = os.getenv("POWERBI_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        return {"status": "error", "message": "Missing Power BI authentication credentials"}
    
    try:
        # Get OAuth token for Power BI
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        
        access_token = token_response.json()["access_token"]
        
        # Power BI API headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Determine API endpoint
        if workspace_id:
            refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        else:
            refresh_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes"
        
        # Trigger refresh
        refresh_payload = {
            "type": "full",
            "commitMode": "transactional",
            "maxParallelism": 2
        }
        
        response = requests.post(refresh_url, headers=headers, json=refresh_payload)
        response.raise_for_status()
        
        # Check response for request ID
        location_header = response.headers.get('Location', '')
        request_id = location_header.split('/')[-1] if location_header else "unknown"
        
        # Get refresh status
        if workspace_id:
            status_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        else:
            status_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes"
        
        status_response = requests.get(f"{status_url}?$top=1", headers=headers)
        status_response.raise_for_status()
        
        refreshes = status_response.json().get("value", [])
        latest_refresh = refreshes[0] if refreshes else {}
        
        return {
            "status": "success",
            "dataset_id": dataset_id,
            "workspace_id": workspace_id,
            "request_id": request_id,
            "refresh_status": latest_refresh.get("status", "Unknown"),
            "refresh_type": latest_refresh.get("refreshType", "Full"),
            "start_time": latest_refresh.get("startTime"),
            "message": "Dataset refresh triggered successfully"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Power BI API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Dataset refresh failed: {str(e)}"
        }