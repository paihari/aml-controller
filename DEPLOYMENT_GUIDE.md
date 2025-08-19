# AML Platform Deployment Guide

This guide walks through deploying the complete AML Agentic Platform from the documentation.

## Prerequisites

- Azure subscription with appropriate permissions
- Databricks account and workspace
- Power BI Pro/Premium licenses
- Azure CLI and Terraform installed
- Python 3.9+ environment

## Phase 1: Infrastructure Setup

### 1. Landing Zone & Security
```bash
# Login and set subscription
az login
az account set --subscription "<subscription-id>"

# Deploy core infrastructure
cd infra
terraform init
terraform plan -var="tenant_id=$(az account show --query tenantId -o tsv)" -var="sa_name=staml<uniqueid>"
terraform apply -auto-approve -var="tenant_id=$(az account show --query tenantId -o tsv)" -var="sa_name=staml<uniqueid>"
```

### 2. Unity Catalog Setup
```bash
cd ../uc
terraform init
terraform apply -auto-approve \
  -var="databricks_account_id=<your-dbx-account-id>" \
  -var="sa_name=staml<uniqueid>"
```

## Phase 2: Data Platform

### 3. Create DLT Pipeline
Upload notebooks to Databricks workspace:
- `/databricks/dlt/transactions.py`
- `/databricks/dlt/watchlists.py` 
- `/databricks/dlt/rules_baseline.py`

Create DLT pipeline via Databricks UI or API with:
- Libraries: All three notebooks above
- Target: `aml.silver`
- Storage: `abfss://logs@<storage>.dfs.core.windows.net/dlt/aml-core`

### 4. Setup Synapse Serverless
```sql
-- Execute in Synapse Serverless SQL pool
-- Update <STORAGE> with your storage account name
\i sql/synapse_setup.sql
\i sql/synapse_views.sql
```

### 5. Case Management Database
```sql
-- Execute in Azure SQL Database
\i sql/case_management_schema.sql
```

## Phase 3: ML & Analytics

### 6. Deploy ML Model
Upload to Databricks:
- `/databricks/ml/triage_model_training.py`
- `/databricks/ml/batch_scoring.py`
- `/databricks/ml/model_promotion.py`

Run training job and promote model to production.

### 7. Power BI Setup
- Connect to Synapse Serverless endpoint
- Import views: `vw_alerts`, `vw_investigator_queue`, `vw_typology_daily`
- Create dashboards with measures from documentation

## Phase 4: Agentic Automation

### 8. Deploy MCP Servers
```bash
# Install dependencies for each server
cd mcp_databricks && pip install -r requirements.txt && cd ..
cd mcp_synapse_sql && pip install -r requirements.txt && cd ..
cd mcp_mlflow && pip install -r requirements.txt && cd ..
cd mcp_sql_case_pbi && pip install -r requirements.txt && cd ..

# Start servers (in separate terminals)
uv run mcp_databricks/server.py
uv run mcp_synapse_sql/server.py  
uv run mcp_mlflow/server.py
uv run mcp_sql_case_pbi/server.py
```

### 9. Configure Master Agent
```bash
cd master-agent
pip install -r requirements.txt

# Test with sample request
python main.py "Deploy baseline rules"
```

## Configuration

### Environment Variables
Create `.env` files for each component:

**Databricks (.env)**:
```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
```

**Synapse (.env)**:
```
SYNAPSE_SERVER=your-synapse-serverless-endpoint.sql.azuresynapse.net
# Either username/password or use managed identity
SYNAPSE_USERNAME=admin
SYNAPSE_PASSWORD=password
```

**Azure SQL (.env)**:
```
SQL_SERVER=your-sql-server.database.windows.net
SQL_USERNAME=admin
SQL_PASSWORD=password
```

**Power BI (.env)**:
```
AZURE_TENANT_ID=your-tenant-id
POWERBI_CLIENT_ID=your-service-principal-client-id
POWERBI_CLIENT_SECRET=your-service-principal-secret
```

## Testing

### 1. Data Flow Test
```bash
# Upload test transaction files to raw/transactions/
# Verify DLT pipeline runs and populates silver/gold tables
```

### 2. ML Pipeline Test
```bash
# Run model training
python databricks/ml/triage_model_training.py

# Run batch scoring
python databricks/ml/batch_scoring.py
```

### 3. Case Sync Test
```bash
# Enable Delta CDF on alerts table
# Start the case sync job
# Verify alerts appear in aml.cases
```

### 4. Power BI Test
```bash
# Refresh datasets
# Verify dashboards load with data
```

### 5. Agentic Test
```bash
# Test master agent with different requests
python master-agent/main.py "ML triage model update"
python master-agent/main.py "Case sync setup"
```

## Monitoring

- Monitor DLT pipeline runs in Databricks
- Check Synapse query performance and costs
- Monitor ML model performance metrics
- Track Power BI refresh status
- Review master agent execution logs in `kb/`

## Security Checklist

- [ ] All storage accounts use private endpoints
- [ ] Key Vault properly configured with RBAC
- [ ] Unity Catalog grants properly set
- [ ] Synapse uses managed identity authentication
- [ ] Power BI workspaces have proper RBAC
- [ ] All secrets stored in Key Vault
- [ ] Network security groups configured

## Troubleshooting

**Common Issues:**
- **DLT Pipeline fails**: Check notebook paths and Unity Catalog permissions
- **Synapse views fail**: Verify external data source and credentials
- **ML model training fails**: Check data quality and feature engineering
- **MCP server connection issues**: Verify environment variables and network access
- **Power BI refresh fails**: Check service principal permissions

**Logs:**
- Databricks: Job run logs and cluster logs
- Synapse: Query history and performance insights
- Master Agent: `master-agent/kb/kb_graph.json`
- MCP Servers: Server console output