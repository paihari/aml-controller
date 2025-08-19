from mcp.server.fastmcp import Tool
import pyodbc
import os

@Tool("create_view")
def create_view(view_name: str, sql_query: str, database: str = "aml_bi"):
    """
    Create or alter a view in Synapse Serverless SQL pool.
    """
    
    server = os.getenv("SYNAPSE_SERVER")
    username = os.getenv("SYNAPSE_USERNAME")
    password = os.getenv("SYNAPSE_PASSWORD")
    
    if not server:
        return {"status": "error", "message": "Missing Synapse server configuration"}
    
    # Connection string
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    
    if username and password:
        conn_str += f"UID={username};PWD={password}"
    else:
        conn_str += "Authentication=ActiveDirectoryManagedIdentity;"
    
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Create the view DDL
            create_view_sql = f"CREATE OR ALTER VIEW {view_name} AS\n{sql_query}"
            
            # Execute the DDL
            cursor.execute(create_view_sql)
            conn.commit()
            
            # Verify the view exists
            check_sql = """
            SELECT OBJECT_ID(?) as view_exists
            """
            cursor.execute(check_sql, (view_name,))
            result = cursor.fetchone()
            
            view_exists = result[0] is not None
            
            return {
                "status": "success",
                "view_name": view_name,
                "database": database,
                "view_exists": view_exists,
                "ddl": create_view_sql
            }
            
    except pyodbc.Error as e:
        return {
            "status": "error",
            "message": f"SQL error creating view {view_name}: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }