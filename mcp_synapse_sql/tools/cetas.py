from mcp.server.fastmcp import Tool
import pyodbc
import os

@Tool("cetas")
def cetas(table_name: str, sql_query: str, storage_location: str, database: str = "aml_bi"):
    """
    Create External Table As Select (CETAS) in Synapse Serverless.
    """
    
    server = os.getenv("SYNAPSE_SERVER")
    username = os.getenv("SYNAPSE_USERNAME") 
    password = os.getenv("SYNAPSE_PASSWORD")
    
    if not server:
        return {"status": "error", "message": "Missing Synapse server configuration"}
    
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    
    if username and password:
        conn_str += f"UID={username};PWD={password}"
    else:
        conn_str += "Authentication=ActiveDirectoryManagedIdentity;"
    
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Check if external data source exists
            ds_check_sql = "SELECT name FROM sys.external_data_sources WHERE name = 'ds_gold'"
            cursor.execute(ds_check_sql)
            ds_exists = cursor.fetchone() is not None
            
            if not ds_exists:
                return {
                    "status": "error", 
                    "message": "External data source 'ds_gold' not found. Run setup first."
                }
            
            # Drop existing external table if exists
            drop_sql = f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP EXTERNAL TABLE {table_name}"
            cursor.execute(drop_sql)
            
            # Create CETAS statement
            cetas_sql = f"""
            CREATE EXTERNAL TABLE {table_name}
            WITH (
                LOCATION = '{storage_location}',
                DATA_SOURCE = ds_gold,
                FILE_FORMAT = [parquet_file_format]
            ) AS
            {sql_query}
            """
            
            # Check if parquet file format exists, create if not
            ff_check_sql = "SELECT name FROM sys.external_file_formats WHERE name = 'parquet_file_format'"
            cursor.execute(ff_check_sql)
            ff_exists = cursor.fetchone() is not None
            
            if not ff_exists:
                create_ff_sql = """
                CREATE EXTERNAL FILE FORMAT parquet_file_format
                WITH (
                    FORMAT_TYPE = PARQUET,
                    DATA_COMPRESSION = 'org.apache.hadoop.io.compress.SnappyCodec'
                )
                """
                cursor.execute(create_ff_sql)
            
            # Execute CETAS
            cursor.execute(cetas_sql)
            conn.commit()
            
            # Verify table exists
            table_check_sql = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?"
            cursor.execute(table_check_sql, (table_name,))
            table_exists = cursor.fetchone()[0] > 0
            
            return {
                "status": "success",
                "table_name": table_name,
                "database": database,
                "storage_location": storage_location,
                "table_exists": table_exists,
                "cetas_sql": cetas_sql
            }
            
    except pyodbc.Error as e:
        return {
            "status": "error",
            "message": f"SQL error creating CETAS table {table_name}: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Unexpected error: {str(e)}"
        }