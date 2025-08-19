from mcp.server.fastmcp import FastMCPServer
from tools.train import train
from tools.register import register
from tools.promote import promote
from tools.batch_score import batch_score

server = FastMCPServer("mlflow")

server.register_tool(train)
server.register_tool(register)
server.register_tool(promote)
server.register_tool(batch_score)

if __name__ == "__main__":
    server.run()