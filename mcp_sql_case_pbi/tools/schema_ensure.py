from mcp.server.fastmcp import Tool
import pyodbc
import os

@Tool("schema_ensure")
def schema_ensure(database: str, schema: str, tables: list):
    """
    Ensure database schema and tables exist for case management.
    """
    
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
            results = []
            
            # Create schema if not exists
            schema_sql = f"""
            IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema}')
            BEGIN
                EXEC('CREATE SCHEMA {schema} AUTHORIZATION dbo')
            END
            """
            cursor.execute(schema_sql)
            results.append({"type": "schema", "name": schema, "status": "ensured"})
            
            # Check and create tables based on table names
            for table in tables:
                table_check_sql = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
                """
                cursor.execute(table_check_sql)
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    if table == "cases":
                        create_sql = f"""
                        CREATE TABLE {schema}.cases (
                          case_id       UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
                          alert_id      VARCHAR(128) NOT NULL UNIQUE,
                          subject_id    VARCHAR(128) NOT NULL,
                          typology      VARCHAR(64)  NOT NULL,
                          risk_score    FLOAT        NOT NULL,
                          status        VARCHAR(20)  NOT NULL DEFAULT 'Open',
                          assigned_to   VARCHAR(256) NULL,
                          disposition   VARCHAR(50)  NULL,
                          created_ts    DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME(),
                          updated_ts    DATETIME2    NOT NULL DEFAULT SYSUTCDATETIME()
                        );
                        
                        CREATE INDEX IX_cases_status ON {schema}.cases(status);
                        CREATE INDEX IX_cases_assigned ON {schema}.cases(assigned_to);
                        CREATE INDEX IX_cases_disposition ON {schema}.cases(disposition);
                        """
                        cursor.execute(create_sql)
                        results.append({"type": "table", "name": f"{schema}.cases", "status": "created"})
                        
                    elif table == "case_events":
                        create_sql = f"""
                        CREATE TABLE {schema}.case_events (
                          event_id    BIGINT IDENTITY(1,1) PRIMARY KEY,
                          case_id     UNIQUEIDENTIFIER NOT NULL,
                          event_type  VARCHAR(64) NOT NULL,
                          details_json NVARCHAR(MAX) NULL,
                          created_ts  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                          created_by  VARCHAR(256) NULL,
                          CONSTRAINT fk_case FOREIGN KEY (case_id) REFERENCES {schema}.cases(case_id)
                        );
                        
                        CREATE INDEX IX_case_events_case_id ON {schema}.case_events(case_id);
                        """
                        cursor.execute(create_sql)
                        results.append({"type": "table", "name": f"{schema}.case_events", "status": "created"})
                else:
                    results.append({"type": "table", "name": f"{schema}.{table}", "status": "exists"})
            
            conn.commit()
            
            return {
                "status": "success",
                "database": database,
                "schema": schema,
                "results": results
            }
            
    except pyodbc.Error as e:
        return {
            "status": "error",
            "message": f"SQL error ensuring schema: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }