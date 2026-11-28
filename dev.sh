#!/usr/bin/env bash
# 本地开发一键启动：API + 记忆 worker + 文档索引 worker。
# 用法：
#   ./dev.sh                 启动全部三个服务
#   ./dev.sh api index       只启动指定服务（api / memory / index 任意组合）
# 运行中按键（前台终端）：
#   a 启停 API   m 启停 memory worker   i 启停 index worker   q 全部退出
#   Ctrl+C / 关终端 同样全部退出；运行中的服务意外退出时会联动停止其余服务。
set -u

[ -n "${BASH_VERSION:-}" ] || { echo "请用 ./dev.sh 或 bash dev.sh 运行（需要 bash）" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend" || exit 1

PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

API_PORT="${API_PORT:-8001}"

if lsof -ti:"$API_PORT" >/dev/null 2>&1; then
  echo "[dev] 端口 $API_PORT 已被占用（可能是已在运行的旧实例）。" >&2
  echo "[dev] 先停止它再启动：lsof -ti:$API_PORT | xargs kill" >&2
  exit 1
fi

DB_PORT="$(sed -nE 's#^DATABASE_URL=.*:([0-9]+)/.*#\1#p' .env 2>/dev/null | head -1)"
DB_PORT="${DB_PORT:-55432}"
if ! nc -z 127.0.0.1 "$DB_PORT" >/dev/null 2>&1; then
  echo "[dev] 警告：127.0.0.1:$DB_PORT 未监听，数据库可能没启动（docker start onefold-pg）" >&2
fi

tag() {
  local t="$1"
  while IFS= read -r line; do printf '[%s] %s\n' "$t" "$line"; done
}

api_pid=0 memory_pid=0 index_pid=0
api_on=0 memory_on=0 index_on=0
stopping=0

start_api() {
  "$PY" -m uvicorn app.main:app --reload --port "$API_PORT" > >(tag api) 2>&1 &
  api_pid=$!
  api_on=1
}
start_memory() {
  "$PY" -m app.workers.memory > >(tag memory) 2>&1 &
  memory_pid=$!
  memory_on=1
}
start_index() {
  "$PY" -m app.workers.document_index > >(tag index) 2>&1 &
  index_pid=$!
  index_on=1
}

# 结束单个服务及其子进程（uvicorn --reload 会派生 reloader 子进程）
stop_pid() {
  local p="$1"
  [ "$p" -gt 0 ] || return 0
  pkill -P "$p" 2>/dev/null
  kill "$p" 2>/dev/null
  wait "$p" 2>/dev/null
}

stop_api() {
  stop_pid "$api_pid"
  # 兜底：reloader 被强杀时可能留下仍占用端口的 server 孤儿进程
  local holders
  holders="$(lsof -ti:"$API_PORT" 2>/dev/null)"
  if [ -n "$holders" ]; then kill $holders 2>/dev/null; fi
  api_pid=0
  api_on=0
}
stop_memory() { stop_pid "$memory_pid"; memory_pid=0; memory_on=0; }
stop_index() { stop_pid "$index_pid"; index_pid=0; index_on=0; }

cleanup() {
  [ "$stopping" = 1 ] && return
  stopping=1
  trap - INT TERM HUP EXIT
  echo ""
  echo "[dev] 正在停止所有服务…"
  stop_api
  stop_memory
  stop_index
}

trap cleanup INT TERM HUP EXIT

status_line() {
  local s
  s="api=$([ "$api_on" = 1 ] && echo 运行中 || echo 已停止)"
  s="$s memory=$([ "$memory_on" = 1 ] && echo 运行中 || echo 已停止)"
  s="$s index=$([ "$index_on" = 1 ] && echo 运行中 || echo 已停止)"
  echo "[dev] 状态: $s"
}

toggle() {
  case "$1" in
    a|api)
      if [ "$api_on" = 1 ]; then stop_api; echo "[dev] API 已停止"; else start_api; echo "[dev] API 已启动"; fi
      ;;
    m|memory)
      if [ "$memory_on" = 1 ]; then stop_memory; echo "[dev] memory worker 已停止"; else start_memory; echo "[dev] memory worker 已启动"; fi
      ;;
    i|index)
      if [ "$index_on" = 1 ]; then stop_index; echo "[dev] index worker 已停止"; else start_index; echo "[dev] index worker 已启动"; fi
      ;;
    q|quit)
      exit 0
      ;;
    *)
      return
      ;;
  esac
  status_line
}

# 监督：运行中的服务意外退出 → 停止全部并以非零码退出
check_deaths() {
  local dead=""
  if [ "$api_on" = 1 ] && ! kill -0 "$api_pid" 2>/dev/null; then dead="api"; fi
  if [ -z "$dead" ] && [ "$memory_on" = 1 ] && ! kill -0 "$memory_pid" 2>/dev/null; then dead="memory worker"; fi
  if [ -z "$dead" ] && [ "$index_on" = 1 ] && ! kill -0 "$index_pid" 2>/dev/null; then dead="index worker"; fi
  if [ -n "$dead" ]; then
    echo "[dev] 服务 $dead 意外退出，停止其余服务…" >&2
    cleanup
    exit 1
  fi
}

# 解析要启动的服务（默认全部）
want_api=0
want_memory=0
want_index=0
if [ "$#" -eq 0 ]; then want_api=1; want_memory=1; want_index=1; fi
for arg in "$@"; do
  case "$arg" in
    api) want_api=1 ;;
    memory) want_memory=1 ;;
    index) want_index=1 ;;
    *)
      echo "[dev] 未知参数: $arg（可选 api / memory / index）" >&2
      exit 1
      ;;
  esac
done

if [ "$want_api" = 1 ]; then start_api; echo "[dev] API    → http://127.0.0.1:$API_PORT （热重载）"; fi
if [ "$want_memory" = 1 ]; then start_memory; echo "[dev] memory → app.workers.memory"; fi
if [ "$want_index" = 1 ]; then start_index; echo "[dev] index  → app.workers.document_index"; fi
echo ""

if [ -t 0 ]; then
  echo "[dev] 按键控制：a=API  m=memory  i=index（启停切换）  q=全部退出 / Ctrl+C"
  while :; do
    if read -t 1 -n 1 -s key; then toggle "$key"; fi
    check_deaths
  done
else
  # 非交互运行（如重定向日志）时不做按键控制
  while :; do
    sleep 1
    check_deaths
  done
fi
