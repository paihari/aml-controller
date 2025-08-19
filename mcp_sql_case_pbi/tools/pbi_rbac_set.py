from mcp.server.fastmcp import Tool
import requests
import os
import json

@Tool("pbi_rbac_set") 
def pbi_rbac_set(workspace_id: str, user_email: str, role: str):
    """
    Set RBAC permissions for a user in a Power BI workspace.
    """
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("POWERBI_CLIENT_ID")
    client_secret = os.getenv("POWERBI_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        return {"status": "error", "message": "Missing Power BI authentication credentials"}
    
    # Validate role
    valid_roles = ["Admin", "Member", "Contributor", "Viewer"]
    if role not in valid_roles:
        return {
            "status": "error",
            "message": f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"
        }
    
    try:
        # Get OAuth token
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
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Add user to workspace
        add_user_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        
        user_payload = {
            "emailAddress": user_email,
            "groupUserAccessRight": role
        }
        
        response = requests.post(add_user_url, headers=headers, json=user_payload)
        
        # Handle different response codes
        if response.status_code == 200:
            result_status = "updated"
        elif response.status_code == 201:
            result_status = "added"
        else:
            response.raise_for_status()
        
        # Get updated workspace users to verify
        users_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
        users_response = requests.get(users_url, headers=headers)
        users_response.raise_for_status()
        
        users = users_response.json().get("value", [])
        user_info = next((u for u in users if u.get("emailAddress") == user_email), None)
        
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "user_email": user_email,
            "role": role,
            "action": result_status,
            "user_info": {
                "displayName": user_info.get("displayName") if user_info else None,
                "groupUserAccessRight": user_info.get("groupUserAccessRight") if user_info else role,
                "principalType": user_info.get("principalType") if user_info else "User"
            },
            "message": f"User {user_email} {result_status} with role {role}"
        }
        
    except requests.exceptions.RequestException as e:
        error_detail = ""
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
        
        return {
            "status": "error",
            "message": f"Power BI API request failed: {error_detail}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"RBAC assignment failed: {str(e)}"
        }