def plan_tasks(request: str):
    """
    Decomposes user requests into executable task plans.
    Returns a list of task dictionaries for the executor.
    """
    if "baseline rules" in request.lower():
        return [
            {
              "id": "T-1",
              "agent": "databricks",
              "tool": "dlt_create_update",
              "args": {
                  "catalog": "aml",
                  "target_schema": "silver",
                  "notebooks": [
                      "/Repos/aml/dlt/watchlists.py",
                      "/Repos/aml/dlt/rules_baseline.py"
                  ],
                  "continuous": True,
                  "storage": "abfss://logs@<sa>.dfs.core.windows.net/dlt/aml-core"
              }
            },
            {
              "id": "T-2",
              "agent": "synapse_sql",
              "tool": "create_view",
              "args": {
                  "sql": "CREATE OR ALTER VIEW vw_alerts AS SELECT * FROM OPENROWSET(...)" 
              }
            }
        ]
    
    elif "ml triage" in request.lower():
        return [
            {
              "id": "T-3",
              "agent": "mlflow",
              "tool": "train",
              "args": {
                  "model_name": "aml_alert_triage",
                  "data_table": "aml.gold.alerts_labeled",
                  "features": ["risk_score", "typology", "evidence_features"],
                  "target": "label"
              }
            },
            {
              "id": "T-4",
              "agent": "mlflow",
              "tool": "batch_score",
              "args": {
                  "model_name": "aml_alert_triage",
                  "input_table": "aml.gold.alerts",
                  "output_table": "aml.gold.alerts_scored"
              }
            }
        ]
    
    elif "case sync" in request.lower():
        return [
            {
              "id": "T-5",
              "agent": "sql_case_pbi",
              "tool": "schema_ensure",
              "args": {
                  "database": "amlcases",
                  "schema": "aml",
                  "tables": ["cases", "case_events"]
              }
            },
            {
              "id": "T-6",
              "agent": "databricks",
              "tool": "jobs_run",
              "args": {
                  "job_name": "case_sync_cdf",
                  "notebook_path": "/Repos/aml/case_sync/alerts_to_cases.py"
              }
            }
        ]
    
    return []