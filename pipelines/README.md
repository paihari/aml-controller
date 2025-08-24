# Pipeline Scripts

This directory contains data processing pipeline scripts used for setup and maintenance of the AML Controller.

## 📄 **Scripts Overview**

### **🔄 Data Loading Pipelines**

#### `opensanctions_pipeline.py`
- **Purpose**: Loads sanctions data from OpenSanctions API
- **Usage**: `python3 opensanctions_pipeline.py`
- **When to use**: Initial setup or when refreshing sanctions database
- **Output**: Populates Supabase with latest sanctions entities

#### `opensanctions_senzing_pipeline.py`
- **Purpose**: Enhanced sanctions loading with Senzing integration
- **Usage**: `python3 opensanctions_senzing_pipeline.py`
- **When to use**: For advanced entity resolution and deduplication
- **Output**: Clean, deduplicated sanctions data

#### `convert_opensanctions.py`
- **Purpose**: Converts OpenSanctions data formats
- **Usage**: `python3 convert_opensanctions.py`
- **When to use**: Data format transformation needs
- **Output**: Converted data files

### **🚀 AML Processing**

#### `run_dynamic_aml.py`
- **Purpose**: Standalone AML engine runner
- **Usage**: `python3 run_dynamic_aml.py`
- **When to use**: Batch processing of transactions outside web API
- **Output**: AML analysis results and alerts

## 🔧 **Setup Requirements**

Before running any pipeline:
1. Ensure environment variables are set (`.env` file)
2. Supabase database is configured
3. Required Python packages installed: `pip install -r requirements.txt`

## ⚠️ **Important Notes**

- These scripts are typically used **once during setup** or for **maintenance**
- They are **not required** for normal AML Controller operation
- The main application (`app.py`) handles real-time processing
- Run these scripts from the project root directory

## 🔄 **Typical Workflow**

1. **Initial Setup**: Run `opensanctions_pipeline.py` to load sanctions data
2. **Daily Operation**: Use main `app.py` for real-time AML processing
3. **Maintenance**: Run pipelines periodically to refresh data