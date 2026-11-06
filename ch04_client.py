"""クライアントを自分で書く。高水準の mcp.Client と、低水準の ClientSession の両方で一覧と呼び出し。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite（この回はLLM不使用）
"""
import asyncio
import sys
from pathlib import Path

from mcp import Client, ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(command=sys.executable,
                               args=[str(Path(__file__).parent / "servers" / "inventory.py")])


async def high_level():
    # 接続の握手（server/discover → だめなら initialize）は mcp.Client がやる
    async with Client(SERVER) as c:
        print("[Client] 道具:", [t.name for t in (await c.list_tools()).tools])
        r = await c.call_tool("get_stock", {"item": "マウス"})
        print("[Client] 結果:", r.content[0].text)


async def low_level():
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as s:
        await s.initialize()          # v2 でも必要。省くと list_tools が「Invalid request parameters」で失敗する
        print("[ClientSession] 道具:", [t.name for t in (await s.list_tools()).tools])


asyncio.run(high_level())
asyncio.run(low_level())
