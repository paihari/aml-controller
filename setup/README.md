# Setup Scripts

This directory contains **one-time setup and utility scripts** for the AML Controller system. These are typically run during initial setup or for specific maintenance tasks.

## 📄 **Scripts Overview**

### **🗃️ Database Setup**

#### `minimalist_schema.sql`
- **Purpose**: SQL schema definition for Supabase sanctions tables
- **Usage**: Execute in Supabase SQL editor or via psql
- **When to use**: Manual database schema setup

#### `create_minimalist_schema.py`
- **Purpose**: Creates AML database schema in Supabase PostgreSQL (Python version)
- **Usage**: `python3 setup/create_minimalist_schema.py`
- **When to use**: Automated database setup or schema recreation

#### `create_table_supabase.py`
- **Purpose**: Creates sanctions table in Supabase via insert operations
- **Usage**: `python3 setup/create_table_supabase.py`
- **When to use**: Table creation if not auto-created

#### `populate_supabase.py`
- **Purpose**: Populate Supabase sanctions table with OpenSanctions data
- **Usage**: `python3 setup/populate_supabase.py`
- **When to use**: Load sanctions data into database after schema setup

### **🧪 Test Data Generation**

#### `create_test_sanctions.py`
- **Purpose**: Creates test transactions with sanctioned entities
- **Usage**: `python3 setup/create_test_sanctions.py`
- **When to use**: Generate specific test data for sanctions matching

### **🌐 Alternative Hosting**

#### `create_simple_host.py`
- **Purpose**: Simple HTTP server with ngrok support for dashboard hosting
- **Usage**: `python3 setup/create_simple_host.py`
- **When to use**: Alternative to main Flask app for simple static hosting

## ⚠️ **Important Notes**

- These are **setup/utility scripts**, not core application modules
- Core application code lives in `/src/` (API, data access, services, utilities)
- These scripts are typically used **once during setup** or for **maintenance**
- They are **not required** for normal AML Controller operation
- The main application (`app.py`) handles real-time processing
- Run these scripts from the project root directory

## 🔧 **Setup Requirements**

Before running any script:
1. Ensure environment variables are set (`.env` file)
2. Supabase database is configured (if using Supabase scripts)
3. Required Python packages installed: `pip install -r requirements.txt`

## 🔄 **Typical Usage**

1. **Initial Setup**: Run database setup scripts once
2. **Daily Operation**: Use main `app.py` for real-time AML processing
3. **Testing**: Run test data generation scripts as needed
4. **Alternative Hosting**: Use simple host script for static demos