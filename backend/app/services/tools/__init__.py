"""工具服务：联网搜索、网页抓取、外部内容防注入。"""

from .client import ToolError, post_tool
from .guard import TAG, check_url, wrap_external
from .web import fetch, search

__all__ = ["TAG", "ToolError", "post_tool", "check_url", "wrap_external", "fetch", "search"]
