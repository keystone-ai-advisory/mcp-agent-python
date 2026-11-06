"""v1 流の書き方を mcp 2.3.0 で実行して、出るエラーを並べる
見せること: ネットの古いサンプルが 2026年8月以降の環境でどう壊れるか。エラー文が直し方のヒントになる。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / LLM は使わない
"""
import asyncio, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def show(title, fn):
    try:
        print(f"[{title}] 成功: {fn()}")
    except Exception as e:
        print(f"[{title}] {type(e).__name__}: {str(e).splitlines()[0][:150]}")


def v1_import():
    from mcp.server.fastmcp import FastMCP          # v1 の import
    return FastMCP


def v1_port():
    from mcp.server import MCPServer
    return MCPServer("x", port=9000)                 # v1 は待ち受けをここで指定した


async def tools():
    from mcp import Client
    from servers import inventory
    async with Client(inventory.mcp) as c:
        return (await c.list_tools()).tools


def v1_input_schema():
    t = asyncio.run(tools())[0]
    return t.inputSchema                              # v1 の項目名（camelCase）


def v1_structured():
    from mcp import Client
    from servers import inventory

    async def go():
        async with Client(inventory.mcp) as c:
            return await c.call_tool("get_stock", {"item": "マウス"})
    return asyncio.run(go()).structuredContent        # async with の外で属性を読む（中で失敗すると ExceptionGroup に包まれる）


def v2_ok():
    t = asyncio.run(tools())[0]
    return f"input_schema={t.input_schema}"           # v2 は snake_case


show("1 from mcp.server.fastmcp import FastMCP", v1_import)
show("2 MCPServer('x', port=9000)", v1_port)
show("3 tool.inputSchema", v1_input_schema)
show("4 result.structuredContent", v1_structured)
show("5 v2 の書き方 tool.input_schema", v2_ok)
