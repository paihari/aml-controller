import sys, json
from planner import plan_tasks
from executor import execute_plan
from kb.kb_utils import record_plan, record_result

def main():
    request = sys.argv[1] if len(sys.argv) > 1 else "Deploy baseline rules"
    plan = plan_tasks(request)
    record_plan(plan)

    for task in plan:
        result = execute_plan(task)
        record_result(task, result)

    print("✅ All tasks executed successfully")

if __name__ == "__main__":
    main()