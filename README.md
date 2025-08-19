# AML Agentic Platform

This repo implements an **Agentic AML Platform** with:
- **Master Agent**: Plans, executes, verifies tasks.
- **MCP Servers**: Wrap Azure/Databricks/ML/SQL/PBI functions.

## Agents
- `mcp_databricks`: Databricks (DLT, Jobs, UC).
- `mcp_synapse_sql`: Synapse Serverless (views, queries).
- `mcp_mlflow`: ML lifecycle (train, register, score).
- `mcp_sql_case_pbi`: Case mgmt (SQL, Power BI refresh).

## Running
1. Start MCP servers:
   ```bash
   uv run mcp_databricks/server.py
   uv run mcp_synapse_sql/server.py
   uv run mcp_mlflow/server.py
   uv run mcp_sql_case_pbi/server.py
   ```

2. Run master agent:
   ```bash
   uv run master-agent/main.py "Deploy baseline rules"
   ```

All tasks, results, and lineage are persisted in `master-agent/kb/`.

## Architecture

The platform follows a secure, cloud-native architecture:

- **Landing Zone**: Secure Azure foundation with private networking
- **Data Lake**: ADLS Gen2 with medallion architecture (raw/silver/gold)
- **Processing**: Databricks with Unity Catalog and Delta Live Tables
- **ML**: MLflow for model lifecycle and triage scoring
- **Analytics**: Synapse Serverless SQL + Power BI dashboards
- **Case Management**: Azure SQL + Power Apps integration

## Next Steps
- Fill in **real implementations** in each tool (`az cli`, `databricks-cli`, `pyodbc`, `mlflow`).
- Wrap everything with your **`syntropAIkit.mcp.BaseSession`** (for retry, logging, safe builtins).
- Add **gating/approval logic** in `master-agent/executor.py` before prod runs.
- Connect to your **knowledge graph** so Master Agent reasons over current state.