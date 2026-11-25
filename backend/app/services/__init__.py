"""业务能力层：供 api / agent / workers 复用，不感知 HTTP 与 SSE。

同名 xxx_yyy 前缀表示同一域内的拆分，例如 memory_* 是长期记忆、
history_* 是历史上下文；域对外的唯一入口是对应门面（memory.py / history.py）。
"""