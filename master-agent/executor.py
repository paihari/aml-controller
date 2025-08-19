import subprocess, json
from verifier import verify_result

def execute_plan(task):
    """
    Executes a single task by calling the appropriate MCP server.
    Returns the result with verification status.
    """
    agent = task["agent"]
    tool = task["tool"]
    args = json.dumps(task["args"])

    # Example: call MCP server via CLI (adapt to your MCP client)
    cmd = ["mcp", agent, tool, args]
    print(f"▶ Running {agent}.{tool} ...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        task_result = {
            "task_id": task["id"], 
            "stdout": result.stdout, 
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
        # Verify the result
        verification = verify_result(task_result)
        task_result["verified"] = verification
        
        if result.returncode != 0:
            print(f"❌ Task {task['id']} failed: {result.stderr}")
        elif verification:
            print(f"✅ Task {task['id']} completed and verified")
        else:
            print(f"⚠️ Task {task['id']} completed but verification failed")
            
        return task_result
        
    except subprocess.TimeoutExpired:
        return {
            "task_id": task["id"],
            "error": "Task timed out after 5 minutes",
            "verified": False
        }
    except Exception as e:
        return {
            "task_id": task["id"],
            "error": str(e),
            "verified": False
        }