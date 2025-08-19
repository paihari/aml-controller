from mcp.server.fastmcp import FastMCPServer
from tools.exec_query import exec_query
from tools.create_view import create_view
from tools.cetas import cetas

server = FastMCPServer("synapse_sql")

server.register_tool(exec_query)
server.register_tool(create_view)
server.register_tool(cetas)

if __name__ == "__main__":
    server.run()