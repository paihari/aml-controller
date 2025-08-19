from mcp.server.fastmcp import FastMCPServer
from tools.sql_exec import sql_exec
from tools.schema_ensure import schema_ensure
from tools.pbi_refresh import pbi_refresh
from tools.pbi_rbac_set import pbi_rbac_set

server = FastMCPServer("sql_case_pbi")

server.register_tool(sql_exec)
server.register_tool(schema_ensure)
server.register_tool(pbi_refresh)
server.register_tool(pbi_rbac_set)

if __name__ == "__main__":
    server.run()