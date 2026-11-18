"""极简 User-Agent 解析：设备类型 / 操作系统 / 浏览器。

只做粗粒度识别（不做 UA 指纹级别的精确判定），用于访问记录的画像字段；
识别不出就返回 None，查询侧按 NULL 处理，不影响其它字段采集。
"""

import re

# 爬虫 / 脚本：命中就不必再判断设备形态
_BOT = re.compile(r"bot|crawler|spider|slurp|headless|curl|wget|python-requests|httpx", re.I)

# 顺序有讲究：先匹配更具体的，再回落到通用规则
_OS_RULES = (
    ("iOS", r"iphone|ipad|ipod"),  # iPhone 的 UA 里也含 Mac OS X，必须在 macOS 之前
    ("Android", r"android"),  # Android 的 UA 里也含 Linux，必须在 Linux 之前
    ("ChromeOS", r"cros"),
    ("Windows", r"windows"),
    ("macOS", r"mac os x|macintosh"),
    ("Linux", r"linux|x11"),
)

# Edge / Chrome 的 UA 都含 Safari，Safari 必须最后判断
_BROWSER_RULES = (
    ("Edge", r"edg/|edga/|edgios/"),
    ("WeChat", r"micromessenger"),
    ("Opera", r"opr/|opera"),
    ("Firefox", r"firefox|fxios"),
    ("Chrome", r"chrome|crios"),
    ("Safari", r"safari"),
)


def _first(ua: str, rules: tuple[tuple[str, str], ...]) -> str | None:
    for name, pattern in rules:
        if re.search(pattern, ua, re.I):
            return name
    return None


def _device(ua: str) -> str | None:
    if not ua:
        return None
    if _BOT.search(ua):
        return "bot"
    if re.search(r"ipad|tablet|playbook|silk", ua, re.I):
        return "tablet"
    if re.search(r"mobile|iphone|ipod|windows phone", ua, re.I):
        return "mobile"
    # Android 平板通常不带 Mobile 标记
    if re.search(r"android", ua, re.I):
        return "tablet"
    return "desktop"


def parse_ua(user_agent: str | None) -> dict[str, str | None]:
    """解析 UA，返回 {"device": ..., "os": ..., "browser": ...}。"""
    ua = user_agent or ""
    return {
        "device": _device(ua),
        "os": _first(ua, _OS_RULES),
        "browser": _first(ua, _BROWSER_RULES),
    }