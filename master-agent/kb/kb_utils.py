import json
import datetime
from pathlib import Path

KB_FILE = Path(__file__).parent / "kb_graph.json"

def load_kb():
    """Load the knowledge base from file."""
    if KB_FILE.exists():
        with open(KB_FILE, 'r') as f:
            return json.load(f)
    return {"plans": [], "results": [], "lineage": {}}

def save_kb(kb_data):
    """Save the knowledge base to file."""
    with open(KB_FILE, 'w') as f:
        json.dump(kb_data, f, indent=2, default=str)

def record_plan(plan):
    """Record a task plan in the knowledge base."""
    kb = load_kb()
    
    plan_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "tasks": plan,
        "status": "planned"
    }
    
    kb["plans"].append(plan_record)
    save_kb(kb)
    print(f"📝 Recorded plan with {len(plan)} tasks")

def record_result(task, result):
    """Record a task result in the knowledge base."""
    kb = load_kb()
    
    result_record = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "task_id": task["id"],
        "agent": task["agent"],
        "tool": task["tool"],
        "result": result,
        "status": "completed" if result.get("verified", False) else "failed"
    }
    
    kb["results"].append(result_record)
    
    # Update lineage graph
    lineage_key = f"{task['agent']}.{task['tool']}"
    if lineage_key not in kb["lineage"]:
        kb["lineage"][lineage_key] = []
    
    kb["lineage"][lineage_key].append({
        "task_id": task["id"],
        "timestamp": result_record["timestamp"],
        "status": result_record["status"]
    })
    
    save_kb(kb)
    print(f"📊 Recorded result for task {task['id']}")

def get_recent_plans(limit=5):
    """Get the most recent plans from the knowledge base."""
    kb = load_kb()
    return sorted(kb["plans"], key=lambda x: x["timestamp"], reverse=True)[:limit]

def get_task_history(agent, tool, limit=10):
    """Get execution history for a specific agent/tool combination."""
    kb = load_kb()
    lineage_key = f"{agent}.{tool}"
    
    if lineage_key in kb["lineage"]:
        return sorted(kb["lineage"][lineage_key], 
                     key=lambda x: x["timestamp"], reverse=True)[:limit]
    return []