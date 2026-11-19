"""归一 · FastAPI 入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

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


class SPAStaticFiles(StaticFiles):
    """前端用 BrowserRouter：/chat、/admin 这类路径在磁盘上没有对应文件，
    直接打开或刷新会 404，这里回落到 index.html 交给前端路由处理。
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # API / MCP 的 404 保持原样，避免把接口错误伪装成首页
            if exc.status_code != 404 or path.startswith(("api/", "mcp/")):
                raise
            return await super().get_response("index.html", scope)


_static = Path("static")
if _static.exists():
    # 静态文件：前端构建输出（含 SPA 回落）
    app.mount("/", SPAStaticFiles(directory=str(_static), html=True), name="static")
