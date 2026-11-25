"""归一 · 配置中心。

所有可调参数集中在这一个类里,应用其他模块一律通过 `settings.xxx` 读取。

取值优先级(从高到低):
    1. 显式传参         Settings(global_concurrency=16)
    2. 环境变量         export GLOBAL_CONCURRENCY=16
    3. .env 文件        GLOBAL_CONCURRENCY=16
    4. 字段默认值       global_concurrency: int = 8

字段名与环境变量的映射规则:
    字段名转大写即为环境变量名,且大小写不敏感:
        deepseek_api_key  ←→  DEEPSEEK_API_KEY / DeepSeek_Api_Key 均能匹配

安全约定:
    - 真实密钥(如 DEEPSEEK_API_KEY、JWT_SECRET)只放在 .env 或环境变量里,
      绝不写进本文件(.env 已被 .gitignore 忽略,不会进仓库);
    - 本文件只保留「安全的占位默认值」,供本地开箱即用与阅读文档。
"""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


#TODO: Settings() 实例化的那一刻,BaseSettings 按「显式传参 > 环境变量(os.environ)> .env 文件 > 字段默认值」的顺序,为每个声明过的字段找到最高优先级的来源值,按字段标注做类型转换("8"→int 8)、校验(非法值抛 ValidationError),最后把结果写入实例属性,此后 settings.xxx 直接可用。
class Settings(BaseSettings):
    """应用配置类。

    为什么继承 BaseSettings 而不是普通类(或 pydantic.BaseModel)?
    BaseSettings 是 pydantic BaseModel 的扩展,在「类型校验」之外,额外提供了
    「配置来源解析」能力,一行类定义就能同时获得下面四件事:

    1. 多来源自动合并:按「传参 > 环境变量 > .env 文件 > 默认值」的优先级取值。
       普通类需要自己写 os.getenv(...) or ".env" 解析;BaseModel 则完全不管来源。
    2. 字段名 → 环境变量名自动映射,大小写不敏感(deepseek_api_key ← DEEPSEEK_API_KEY)。
    3. 自动类型转换:环境变量天生都是字符串,BaseSettings 会按字段标注把
       "8" 转成 int 8、"true" 转成 bool True、"~/data" 转成 Path。
    4. 启动即校验(fail-fast):值不合法(如 GLOBAL_CONCURRENCY=abc 给 int 字段)
       会在实例化瞬间抛 ValidationError,进程直接起不来——把配置错误挡在
       启动阶段,而不是等第一个请求进来才崩。

    model_config 是「类级行为配置」,通过 SettingsConfigDict 声明(见下)。
    """

    #TODO: 它声明了这个类的配置读取行为:告诉 BaseSettings 去哪里找值(env_file=".env")、多余键怎么处理(extra="ignore")。它本身不是业务字段,只是 pydantic 实例化时读取的类级开关,不参与 settings.xxx 取值。
    model_config = SettingsConfigDict(
        # env_file:指定从哪个 dotenv 文件补充读取配置。
        # 注意:相对路径是相对于「进程的当前工作目录(cwd)」,而不是本文件所在目录!
        #   - 在 backend/ 下启动(uvicorn app.main:app)→ 读取 backend/.env
        #   - 在项目根启动 → 读取项目根 .env
        #   - Docker 部署时由 docker-compose 的 env_file 注入为真实环境变量,
        #     优先级高于 .env 文件,此处的 .env 不存在也不影响运行。
        env_file=".env",
        # extra:控制「配置来源里出现、但本类没有声明」的键怎么处理。
        # 实测(不设该项时):.env 里多出一个未声明的键(例如从别处拷贝的 .env
        # 遗留了旧变量),会直接抛 ValidationError「Extra inputs are not permitted」,
        # 导致服务启动失败——为无关的额外键陪葬。
        # 设为 "ignore":容忍并忽略这些额外键,只关心类里声明过的字段。
        # 备选值:forbid(默认的严格模式)、allow(收集进 model_extra)。
        extra="ignore",
    )

    app_name: str = "onefold"
    env: str = "dev"  # 运行环境标识:dev / prod,生产环境应通过环境变量覆盖

    # ── 存储 ──────────────────────────────────────────────
    database_url: str = "postgresql+psycopg://localhost:5432/onefold"  #  PostgreSQL 连接串,compose 会覆盖为 db 容器地址
    data_dir: Path = Path("./data")               # 数据根目录(上传文件、备份等)
    max_upload_mb: int = 20                       # 单文件上传大小上限(MB)

    # ── 鉴权 ──────────────────────────────────────────────
    # 注意:默认值仅为本地开发占位,生产环境必须通过环境变量覆盖为强随机值,
    # 否则任何人都能用公开的默认密钥伪造 JWT。
    jwt_secret: str = "change-me-in-env"
    jwt_ttl_hours: int = 24    # 登录态有效期(小时)
    cookie_secure: bool = False  # Cookie 是否仅走 HTTPS;线上必须为 True

    # ── 邮件 / 邮箱验证码 ─────────────────────────────────
    # smtp_host 为空即 dev 模式:验证码写日志;仅非 prod 环境才在响应里回传 dev_code。
    # 配好下面几项后自动切真实发信,业务代码不用改。
    smtp_host: str = ""            # 例如 smtp.qq.com / smtp.163.com / smtp.gmail.com
    smtp_port: int = 465           # 465 = SSL;587 = STARTTLS(需 smtp_ssl=False)
    smtp_user: str = ""            # 发信账号,通常就是邮箱地址
    smtp_password: str = ""        # QQ/163 用「授权码」,不是登录密码
    smtp_from: str = ""            # 发件人,留空则取 smtp_user
    smtp_ssl: bool = True
    email_code_ttl_minutes: int = 10   # 验证码有效期(分钟)
    email_code_cooldown_s: int = 60    # 同一邮箱两次发码的最小间隔(秒)
    email_code_hourly_max: int = 5     # 每小时上限(封)
    email_code_daily_max: int = 10     # 每日上限(封)
    email_code_max_attempts: int = 5   # 单条码允许输错的次数

    # ── 模型(DeepSeek)─────────────────────────────────────
    api_key: str = ""  # 真实密钥只放 .env / 环境变量,严禁硬编码或提交
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-flash"  # 官方主推模型;旧名 deepseek-chat 仍被接受

    # ── 工具(联网搜索 / 网页抓取)─────────────────────────
    # search_enabled=False 时不注册任何工具,聊天行为与未接入工具时完全一致(可随时回滚)。
    # Search / Fetch 走 /v1/tools/* 独立接口,与聊天共用同一把 api_key。
    search_enabled: bool = True
    search_count: int = 5             # 单次搜索返回条数(接口上限 50)
    search_snippet_chars: int = 500   # 每条 summary 截断长度(接口给 600~800 字)
    search_min_score: float = 1.0     # rerank_score 低于此值视为噪音丢弃
    fetch_max_chars: int = 6000       # 抓取正文截断长度
    tool_http_timeout_s: int = 20     # 单次上游请求超时
    tool_http_retries: int = 2        # 408/429/5xx 的重试次数(4xx 不重试)

    # ── Agent 循环 ────────────────────────────────────────
    agent_max_steps: int = 10          # 单轮最多几轮工具循环,防死循环
    agent_tool_timeout_s: int = 15    # 单个工具执行超时(秒)

    # ── 嵌入 / 重排（在线 API，不在服务器加载模型）──────────
    embed_provider: str = "openrouter"
    embed_base_url: str = "https://openrouter.ai/api/v1"
    embed_model: str = "baai/bge-m3"  # 以 OpenRouter 模型页实际 slug 为准
    embed_dim: int = 1024
    # 批量嵌入参数
    embed_batch_size: int = 32
    embed_timeout_s: float = 30.0
    openrouter_api_key: str = ""      # 与 DeepSeek api_key 分开
    rerank_enabled: bool = False
    rerank_model: str = "mongodb/rerank-3-lite"

    # ── RAG / 历史压缩 ──────────────────────────────────────
    rag_enabled: bool = True
    public_kb_guest_read: bool = True    # 访客是否可读公共知识库
    rag_vector_max_distance: float = 0.60  # 向量距离上限，先粗筛
    rag_rerank_min_score: float = 0.35     # rerank 最终阈值
    rag_top_k: int = 5                  # 最终注入的父块数
    rag_lexical_candidates: int = 100   # tsvector/pg_trgm 召回数
    rag_bm25_top: int = 50              # BM25 候选重排后保留数
    rag_vector_top: int = 50            # pgvector 召回数
    rag_rrf_k: int = 60                 # RRF 融合参数
    rag_child_chars: int = 500           # 子块字符上限
    rag_parent_chars: int = 1600         # 父块字符上限
    index_worker_concurrency: int = 1    # 4G 服务器首期串行解析
    index_max_attempts: int = 3          # 文档索引最大重试次数
    history_raw_runs: int = 4          # 最近保留的完整 run 数
    history_compact_tokens: int = 6000 # 超过该 token 触发压缩
    history_summary_max_tokens: int = 800

    # ── 并发与队列(详见 api/chat.py 的双层并发控制)──────────
    global_concurrency: int = 8  # 全局信号量名额:同时执行的 AgentRuntime 任务上限
    per_user_concurrency: int = 1  # 单身份并发上限(当前由身份锁实现为串行)
    queue_timeout_s: int = 60  # 排队超时(秒):排队超过该时长直接返回 queue_timeout

    # ── 配额 ────────────────────────────────────────────────
    # 游客累计免费轮次(一轮 = 一次提问到回答结束),用完引导注册
    guest_max_rounds: int = 20
    user_messages_per_day: int = 100  # 登录用户每日消息条数(待接入)
    guest_docs_max: int = 10           # 访客可上传文档数(待接入)
    user_docs_max: int = 20           # 登录用户可上传文档数(待接入)

    # ── 上下文预算(token)────────────────────────────────────
    # 每段内容的 token 上限,用于组装提示词时给 LLM 的上下文做预算分配。
    context_system: int = 2000    # 系统提示词
    context_tools: int = 2000     # 工具定义
    context_memory: int = 1000    # 长期记忆
    context_rag: int = 4000       # RAG 检索片段
    context_history: int = 8000   # 对话历史
    context_output: int = 4000    # 预留的输出空间
    # 工具结果预算(字符)：最近 context_full_runs 轮完整回放，更早的压缩成检索摘要
    context_tool_result: int = 6000
    context_full_runs: int = 2

    # ── 长期记忆 ──────────────────────────────────────────
    memory_enabled: bool = True          # 总开关；关闭后不入队、不注入
    memory_worker_concurrency: int = 2   # worker 进程内并发提取数
    memory_poll_s: float = 2.0           # 没任务时的轮询间隔
    memory_max_attempts: int = 3         # 单 job 最大尝试次数
    memory_max_turns: int = 10           # 提取时最多看最近几轮
    memory_extract_max_cards: int = 3    # 单轮最多提取卡片
    memory_extract_max_notes: int = 2    # 单轮最多提取笔记
    memory_cards_max: int = 20           # 注入卡片上限
    memory_notes_max: int = 5            # 注入笔记上限
    memory_card_chars: int = 120         # 单张卡片 text 上限
    memory_note_chars: int = 300         # 单条笔记 text 上限
    guest_memory_min_rounds: int = 3     # 访客达到该轮次才提取记忆
    guest_memory_daily_limit: int = 4    # 访客每日提取次数上限
    guest_memory_ttl_days: int = 90      # 访客记忆未活跃清理天数
    memory_prompt_temperature: float = 0.2
    @model_validator(mode="after")
    def _guard_prod_secret(self) -> "Settings":
        """生产环境禁止使用默认 JWT 密钥：默认值是公开的，谁都能伪造登录态。"""
        if self.env == "prod" and self.jwt_secret in ("change-me", "change-me-in-env"):
            raise ValueError("生产环境必须通过环境变量设置强随机 JWT_SECRET")
        return self


# 模块级单例:导入本模块的这一刻,就会完成「读取 .env/环境变量 → 类型转换 → 校验」,
# 任何一步失败都会让进程启动直接崩掉(fail-fast),把配置问题暴露在部署时而非运行时。
# 全应用共享这一个实例,import 即用,无需重复解析。
settings = Settings()

# 启动时确保数据目录存在:parents=True 表示递归创建父目录,
# exist_ok=True 表示目录已存在时不报错(幂等)。
settings.data_dir.mkdir(parents=True, exist_ok=True)
