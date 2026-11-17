"""MCP HTTP 入口（骨架）。真正的 Streamable HTTP app 在后续挂载。"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def info():
    return {
        "service": "onefold-mcp",
        "transports": ["stdio", "streamable-http"],
        "status": "skeleton",
        "note": "stdio 入口：python -m app.mcp_server；HTTP 挂载待实现",
    }


@router.post("")
async def call():
    raise HTTPException(501, "MCP Streamable HTTP is not mounted yet")
