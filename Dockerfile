# ============================================================================
# 多阶段构建（multi-stage build）
# 阶段 1 只负责把前端源码编译成静态文件，编译完成后整个阶段被丢弃：
# 最终镜像里既没有 node 运行时，也没有 node_modules，只保留 dist 产物。
# ============================================================================

# 阶段 1：前端构建。AS web 是给这个阶段命名，后面用 COPY --from=web 引用。
# node:20-slim 是精简版 Node 20 镜像，只用来跑构建工具，不进入最终镜像。
FROM node:20-slim AS web

# 进入容器后的工作目录；目录不存在会自动创建，后续命令都在 /web 下执行。
WORKDIR /web

# 先只拷依赖清单（package.json 与 package-lock.json），故意不拷源码。
# 原因：依赖清单很少变，源码经常变。单独成层后，改源码时这一层仍命中缓存，
# 下面的 npm ci 就不会重跑。
COPY frontend/package*.json ./

# 按 package-lock.json 精确安装依赖。ci = clean install：
# 版本完全锁定、结果可复现，且不会修改 lock 文件，比 npm install 更快。
RUN npm ci

# 接着拷前端全部源码（src、vite 配置、index.html 等）。
COPY frontend/ ./

# 执行 vite build，编译产物输出到 /web/dist。
RUN npm run build

# ============================================================================
# 阶段 2：最终镜像。只有这个阶段的内容会上线，
# 阶段 1 的四层构建产物到这里全部被丢弃。
# ============================================================================

# 基于 Python 3.12 精简版（自带 python 与 pip，约 130MB / 5 层）。
FROM python:3.12-slim

# 后端代码在容器内的存放位置。
WORKDIR /app

# 先拷后端依赖清单。同样放在装依赖之前、拷代码之前，
# 保证「改代码」不会触发「重装依赖」。
COPY backend/requirements.txt .

# 安装 Python 依赖，装进系统 site-packages。
# --no-cache-dir：不保留 pip 下载的 wheel 缓存。
# 必须写在同一层里——如果改用「下一条 RUN 再 rm」的方式是无效的，
# 因为被删的文件仍原样留在上一层，照样占体积。
RUN pip install --no-cache-dir -r requirements.txt

# 拷后端业务代码（约 242kB）。这一层几乎每次发布都会变化。
COPY backend/app ./app

# 从阶段 1 取前端编译产物。--from=web 引用阶段名，
# 只复制 dist 目录（约 541kB）；node_modules、node 二进制全部丢弃。
COPY --from=web /web/dist ./static

# 创建非 root 用户 appuser（uid 10001），并把 /app 下所有文件改成它的属主。
# 容器默认以 root 运行，而容器内的 root 等同于宿主机的 root，
# 降权是降低容器被攻破后影响面的关键一步。
# 代价：chown 修改文件元数据会触发写时复制，整个 /app 被复制进新层（约 844kB）。
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app

# 切换到非 root 用户，之后容器内的进程（uvicorn）都以此身份运行。
# 注意：宿主机挂载进来的目录（如 ./data）属主也必须是 10001，
# 否则启动时会报 PermissionError: [Errno 13] Permission denied。
USER appuser

# 声明容器监听的端口，仅起说明作用，不会真正开放端口。
# 实际的端口映射写在 docker-compose.yml 的 ports 字段里。
EXPOSE 8000

# 健康检查：启动后每隔 30 秒请求一次 /healthz，连续失败 3 次标记为 unhealthy。
# docker compose 与 deploy.sh 靠它判断容器是否真正启动成功。
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

# 容器启动命令，也是容器内的 1 号进程（PID 1）。
# 采用 exec 形式（JSON 数组）而不是 shell 形式，
# 这样 uvicorn 直接作为 PID 1，能正确接收 docker stop 发来的 SIGTERM 并优雅退出。
# --host 0.0.0.0：监听所有网卡，否则容器外访问不到。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
