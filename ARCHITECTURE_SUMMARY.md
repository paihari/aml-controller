# AML Platform Architecture Summary

## Overview
This repository contains a complete implementation of an **Anti-Money Laundering (AML) Agentic Platform** designed for financial institutions. The platform combines modern cloud-native architecture with AI-driven automation for detecting and investigating suspicious financial activities.

## Key Components

### 🏗️ Infrastructure Layer
- **Landing Zone**: Secure Azure foundation with private networking, customer-managed keys, and RBAC
- **Data Lake**: ADLS Gen2 with medallion architecture (raw/silver/gold layers)
- **Compute**: Databricks workspace with VNet injection and Unity Catalog governance
- **Analytics**: Synapse Serverless SQL pool for serving layer

### 📊 Data Platform
- **Ingestion**: Delta Live Tables for streaming data processing
- **Storage**: Unity Catalog with external locations and fine-grained permissions  
- **Processing**: PySpark-based transformation pipelines
- **Serving**: SQL views optimized for BI consumption

### 🤖 ML & Intelligence
- **Detection Rules**: 5 baseline AML typologies (sanctions, structuring, velocity, corridors, round-tripping)
- **ML Triage**: XGBoost model for alert prioritization with MLflow lifecycle management
- **Feature Engineering**: Automated feature extraction from transaction patterns
- **Model Operations**: Automated training, validation, and deployment workflows

### 👥 Case Management
- **Database**: Azure SQL with optimized schema for investigation workflows
- **Integration**: Real-time sync from alerts to cases via Delta Change Data Feed
- **UI**: Power BI dashboards and Power Apps for investigator workflows
- **Audit**: Complete audit trail of all case actions and dispositions

### 🧠 Agentic Automation
- **Master Orchestrator**: Plans, executes, and verifies complex multi-step workflows
- **MCP Servers**: Specialized agents for Databricks, SQL, MLflow, and Power BI operations
- **Knowledge Base**: Graph-based storage of execution history and system lineage
- **Verification**: Automated validation of all system changes and deployments

## Security Features

✅ **Network Isolation**: All services communicate via private endpoints  
✅ **Encryption**: Customer-managed keys for data at rest and in transit  
✅ **Identity**: Azure AD integration with managed identities  
✅ **Access Control**: Fine-grained RBAC across all components  
✅ **Audit**: Complete audit trail of all data access and modifications  
✅ **Compliance**: Designed for regulatory requirements (PCI, SOX, GDPR)  

## Key Benefits

### For Data Engineers
- Infrastructure-as-code with Terraform
- Automated CI/CD pipelines
- Standardized development patterns
- Built-in monitoring and alerting

### For Data Scientists  
- MLflow integration for experiment tracking
- Feature store with automated feature engineering
- A/B testing framework for model comparison
- Automated model deployment and monitoring

### For AML Investigators
- Real-time alert prioritization with ML scoring
- Interactive dashboards with drill-down capabilities
- Streamlined case management workflows
- Automated report generation

### for Compliance Teams
- Complete audit trail of all decisions
- Regulatory reporting automation  
- Risk scoring and threshold management
- Integration with external watchlists

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Infrastructure** | Azure, Terraform | Cloud resources and IaC |
| **Data Lake** | ADLS Gen2, Delta Lake | Scalable storage with ACID transactions |
| **Processing** | Databricks, Spark | Distributed data processing |
| **Governance** | Unity Catalog | Data governance and access control |
| **ML Platform** | MLflow, XGBoost | Model lifecycle and training |
| **Analytics** | Synapse SQL, Power BI | Business intelligence and reporting |  
| **Database** | Azure SQL | Transactional case management |
| **Orchestration** | Custom Python, MCP | Workflow automation |
| **Integration** | Delta CDF, REST APIs | Real-time data synchronization |

## Implementation Highlights

### Medallion Architecture
```
Raw Layer (Bronze)    → Silver Layer (Conformed)  → Gold Layer (Business)
├── transactions/     → ├── aml_transactions      → ├── alerts
├── parties/         → ├── parties               → ├── alerts_scored  
├── accounts/        → ├── accounts              → ├── features
└── watchlists/      → └── watchlists            → └── reports
```

### AML Detection Rules
1. **Sanctions Screening**: Name/DOB/country matching against OFAC/EU/SECO lists
2. **Structuring Detection**: Multiple small transactions under reporting thresholds  
3. **High-Risk Corridors**: Transactions involving sanctioned countries
4. **Velocity Anomalies**: Unusual spending patterns compared to historical baseline
5. **Round-Tripping**: Circular money movements between same parties

### ML Model Pipeline
```
Training Data → Feature Engineering → Model Training → Validation → Staging → Production → Batch Scoring
     ↑                                    ↓                                        ↓
Case Outcomes ← Investigation Results ← Alert Prioritization ← Triage Scores ← New Alerts
```

### Agentic Workflow Example
```
User Request: "Deploy new AML rules to production"
     ↓
Master Agent: Decomposes into tasks
     ├── Databricks Agent: Update DLT pipeline
     ├── Synapse Agent: Refresh analytical views  
     ├── ML Agent: Retrain and deploy triage model
     └── Power BI Agent: Update dashboards
     ↓
Verification: Validate all changes successful
     ↓
Knowledge Base: Record execution and lineage
```

## Getting Started

1. **Clone Repository**: `git clone <repo-url>`
2. **Configure Environment**: Copy `.env.template` to `.env` and fill values
3. **Deploy Infrastructure**: Follow `DEPLOYMENT_GUIDE.md` step by step
4. **Load Sample Data**: Upload test datasets to validate end-to-end flow
5. **Configure Dashboards**: Import Power BI templates and set data sources
6. **Test Automation**: Run master agent with sample requests

## Next Steps & Roadmap

- **Advanced ML**: Implement graph neural networks for entity resolution
- **Real-time Processing**: Add Kafka/Event Hubs for streaming ingestion  
- **Advanced Analytics**: Add network analysis and behavioral modeling
- **Integration**: Connect to core banking systems and external APIs
- **Mobile**: Develop investigator mobile app for field work
- **AI Assistant**: Add natural language interface for investigators

This platform provides a solid foundation for modern AML operations while remaining flexible and extensible for future requirements.