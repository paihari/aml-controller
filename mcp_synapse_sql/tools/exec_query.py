from mcp.server.fastmcp import Tool
import pyodbc
import os
import json

@Tool("exec_query")
def exec_query(sql: str, database: str = "aml_bi"):
    """
    Execute a SQL query on Synapse Serverless SQL pool.
    """
    
    server = os.getenv("SYNAPSE_SERVER")
    username = os.getenv("SYNAPSE_USERNAME")
    password = os.getenv("SYNAPSE_PASSWORD")
    
    if not server:
        return {"status": "error", "message": "Missing Synapse server configuration"}
    
    # Connection string for Synapse Serverless
    conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    
    # Add authentication
    if username and password:
        conn_str += f"UID={username};PWD={password}"
    else:
        # Use Azure AD authentication
        conn_str += "Authentication=ActiveDirectoryManagedIdentity;"
    
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Handle multi-statement SQL
            statements = [stmt.strip() for stmt in sql.split('GO') if stmt.strip()]
            results = []
            
            for statement in statements:
                if statement.upper().startswith('SELECT'):
                    # Query - return results
                    cursor.execute(statement)
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()
                    
                    results.append({
                        "type": "query",
                        "columns": columns,
                        "row_count": len(rows),
                        "rows": [list(row) for row in rows[:100]]  # Limit to 100 rows
                    })
                else:
                    # DDL/DML - execute and get row count
                    cursor.execute(statement)
                    row_count = cursor.rowcount
                    
                    results.append({
                        "type": "command",
                        "rows_affected": row_count,
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement
                    })
            
            conn.commit()
            
            return {
                "status": "success",
                "database": database,
                "results": results
            }
            
    except pyodbc.Error as e:
        return {
            "status": "error",
            "message": f"SQL error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }