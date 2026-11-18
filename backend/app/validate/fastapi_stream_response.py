"""验证 StreamingResponse 中数据的取出方式。

核心机制：StreamingResponse 在构造时把传入的（异步）生成器存到
`self.body_iterator` 属性上，数据流就藏在这里。所谓"取出数据"，
本质上就是异步迭代 body_iterator。三种方式分别演示如下。
"""

import asyncio

import anyio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.testclient import TestClient

app = FastAPI()


async def fake_video_streamer():
    for i in range(10):
        yield "some fake video bytes"
        await anyio.sleep(0)


@app.get("/")
async def main():
    return StreamingResponse(fake_video_streamer())


# ===== 方式一：直接异步迭代 body_iterator（无服务器参与，最快、最直接）=====
async def consume_body_iterator():
    print("=== 方式一：直接迭代 response.body_iterator ===")
    # 路由函数是普通 async 函数，直接 await 调用即可拿到 StreamingResponse 对象
    response = await main()
    assert isinstance(response, StreamingResponse)
    # 数据全在 body_iterator 里，异步迭代逐个取出 chunk
    content = ''
    async for chunk in response.body_iterator:
        content += chunk
        print(f"  {content!r}")


# ===== 方式二：TestClient 走完整 ASGI 链路（同步风格，测试里最常用）=====
def consume_testclient():
    print("=== 方式二：TestClient.stream 流式读取 ===")
    with TestClient(app) as client:
        # stream() 打开响应后边收边取，逐块读取
        with client.stream("GET", "/") as resp:
            for chunk in resp.iter_bytes():
                print(f"  {chunk!r}")
        # 普通 get() 会等流结束，content 是所有 chunk 拼接后的完整字节串
        resp2 = client.get("/")
        print(f"  一次性拼接结果: {resp2.content!r}")


# ===== 方式三：httpx.AsyncClient + ASGITransport（异步测试的推荐姿势）=====
async def consume_httpx():
    import httpx

    print("=== 方式三：httpx.AsyncClient + ASGITransport ===")
    # ASGITransport 让 httpx 直接调用 ASGI app，不经过真实网络
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 用 stream() 配合 aiter_bytes() 异步逐块取出
        async with client.stream("GET", "/") as resp:
            async for chunk in resp.aiter_bytes():
                print(f"  {chunk!r}")


if __name__ == "__main__":
    asyncio.run(consume_body_iterator())
    # consume_testclient()
    # asyncio.run(consume_httpx())
