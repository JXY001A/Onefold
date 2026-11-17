"""归一 MCP 服务（stdio 入口）。

后续在这里注册只读工具（web_search / fetch_url / doc_search），
并在 app/main.py 挂载 Streamable HTTP 版本。
"""

from mcp.server import MCPServer

mcp = MCPServer("onefold")


@mcp.tool(description="Health check for the Onefold MCP server")
def hello(name: str = "world") -> str:
    return f"hello {name}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
