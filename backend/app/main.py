"""归一 · FastAPI 入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import admin, auth, chat, conversations, documents, mcp, skills, visits
from .config import settings
from .db import init_db

# 初始化数据库
@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


# lifespan 管启动/关闭资源（数据库连接池、模型、MCP 客户端）；yield 前是 startup，后是 shutdown。
app = FastAPI(title="Onefold", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(visits.router, prefix="/api/visits", tags=["visits"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

# 健康检查
@app.get("/healthz")
def healthz():
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


_static = Path("static")
if _static.exists():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="static")
