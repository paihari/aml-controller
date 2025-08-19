from mcp.server.fastmcp import Tool
import requests
import json
import os
import time

@Tool("jobs_run")
def jobs_run(job_name: str, notebook_path: str, parameters: dict = None):
    """
    Create and run a Databricks job with the specified notebook.
    """
    
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        return {"status": "error", "message": "Missing Databricks credentials"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Job configuration
    job_config = {
        "name": job_name,
        "new_cluster": {
            "spark_version": "13.3.x-scala2.12",
            "node_type_id": "Standard_DS3_v2",
            "num_workers": 1,
            "spark_conf": {
                "spark.databricks.cluster.profile": "singleNode",
                "spark.master": "local[*]"
            },
            "custom_tags": {
                "ResourceClass": "SingleNode"
            }
        },
        "notebook_task": {
            "notebook_path": notebook_path,
            "base_parameters": parameters or {}
        },
        "timeout_seconds": 3600,
        "max_concurrent_runs": 1
    }
    
    try:
        # Check if job exists
        list_url = f"{workspace_url}/api/2.1/jobs/list"
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()
        
        existing_jobs = response.json().get("jobs", [])
        existing_job = None
        
        for job in existing_jobs:
            if job.get("settings", {}).get("name") == job_name:
                existing_job = job
                break
        
        if existing_job:
            job_id = existing_job["job_id"]
            # Update existing job
            update_url = f"{workspace_url}/api/2.1/jobs/reset"
            update_payload = {
                "job_id": job_id,
                "new_settings": job_config
            }
            response = requests.post(update_url, headers=headers, json=update_payload)
            response.raise_for_status()
        else:
            # Create new job
            create_url = f"{workspace_url}/api/2.1/jobs/create"
            response = requests.post(create_url, headers=headers, json=job_config)
            response.raise_for_status()
            
            result = response.json()
            job_id = result["job_id"]
        
        # Run the job
        run_url = f"{workspace_url}/api/2.1/jobs/run-now"
        run_payload = {"job_id": job_id}
        
        response = requests.post(run_url, headers=headers, json=run_payload)
        response.raise_for_status()
        
        run_result = response.json()
        run_id = run_result["run_id"]
        
        # Wait for job to start
        time.sleep(5)
        
        # Get run status
        status_url = f"{workspace_url}/api/2.1/jobs/runs/get"
        status_response = requests.get(status_url, headers=headers, params={"run_id": run_id})
        status_response.raise_for_status()
        
        run_details = status_response.json()
        
        return {
            "status": "success",
            "job_id": job_id,
            "run_id": run_id,
            "job_name": job_name,
            "notebook_path": notebook_path,
            "run_state": run_details.get("state", {}).get("life_cycle_state"),
            "run_url": f"{workspace_url}/#job/{job_id}/run/{run_id}"
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