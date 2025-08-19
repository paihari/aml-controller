from mcp.server.fastmcp import FastMCPServer
from tools.dlt_create_update import dlt_create_update
from tools.jobs_run import jobs_run
from tools.uc_grant import uc_grant

server = FastMCPServer("databricks")

server.register_tool(dlt_create_update)
server.register_tool(jobs_run)
server.register_tool(uc_grant)

if __name__ == "__main__":
    server.run()