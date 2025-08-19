from mcp.server.fastmcp import Tool
import pyodbc
import os
import json

@Tool("sql_exec")
def sql_exec(sql: str, database: str, connection_string: str = None):
    """
    Execute SQL statements on Azure SQL Database.
    """
    
    if not connection_string:
        server = os.getenv("SQL_SERVER")
        username = os.getenv("SQL_USERNAME")
        password = os.getenv("SQL_PASSWORD")
        
        if not server:
            return {"status": "error", "message": "Missing SQL server configuration"}
        
        connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        
        if username and password:
            connection_string += f"UID={username};PWD={password}"
        else:
            connection_string += "Authentication=ActiveDirectoryManagedIdentity;"
    
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            
            # Handle multi-statement SQL
            statements = [stmt.strip() for stmt in sql.split('GO') if stmt.strip()]
            results = []
            
            for statement in statements:
                if statement.upper().startswith(('SELECT', 'WITH')):
                    # Query - return results
                    cursor.execute(statement)
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    results.append({
                        "type": "query",
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                        "columns": columns,
                        "row_count": len(rows),
                        "rows": [list(row) for row in rows[:100]]  # Limit to 100 rows for response size
                    })
                else:
                    # DDL/DML - execute and get row count
                    cursor.execute(statement)
                    row_count = cursor.rowcount
                    
                    results.append({
                        "type": "command",
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                        "rows_affected": row_count
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
            "message": f"SQL error: {str(e)}",
            "sql_state": getattr(e.args[0], 'state', 'Unknown') if e.args else 'Unknown'
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }