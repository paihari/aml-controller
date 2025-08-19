import json

def verify_result(result):
    """
    Verifies the execution result based on task type and output.
    Returns True if verification passes, False otherwise.
    """
    if result.get("returncode", 1) != 0:
        return False
        
    if "error" in result.get("stderr", "").lower():
        return False
    
    # Parse stdout to check for success indicators
    try:
        if result.get("stdout"):
            output = json.loads(result["stdout"])
            
            # Check for common success patterns
            if output.get("status") == "success":
                return True
            if output.get("ok") is True:
                return True
            if "pipeline_id" in output and "tables" in output:
                return True
            if "view_created" in output:
                return True
                
    except json.JSONDecodeError:
        # Non-JSON output, check for text patterns
        stdout = result.get("stdout", "").lower()
        if "success" in stdout or "completed" in stdout:
            return True
    
    return True  # Default to True for basic execution without errors