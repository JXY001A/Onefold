"""后台任务：独立进程运行，不依赖 FastAPI 请求上下文。

    runner.py           进程骨架（建表、僵尸回收、线程数、信号、收尾）
    memory*.py          长期记忆提取
    document_index.py   文档解析与建索引

队列状态都在 services/ 里（memory_jobs / document_jobs），worker 只跑循环。
"""