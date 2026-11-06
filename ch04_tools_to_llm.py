"""MCP の道具一覧を OpenAI 互換の tools 形式に変換して、LLM に渡す（変換関数は common/mcp_tools.py）。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client, StdioServerParameters
from common.llm import chat
from common.mcp_tools import to_openai_tools

SERVER = StdioServerParameters(command=sys.executable,
                               args=[str(Path(__file__).parent / "ch03_server_tools.py")])


async def main():
    async with Client(SERVER) as c:
        tools = (await c.list_tools()).tools
    spec = to_openai_tools(tools)
    for t in spec:
        if not t["function"]["description"]:          # 説明が空だと LLM は名前から推測するしかない
            print("警告: 説明が空です:", t["function"]["name"])
    print(json.dumps(spec[1], ensure_ascii=False, indent=1))
    m = chat([{"role": "user", "content": "モニターの在庫を道具で調べて"}], tools=spec)
    for call in m.tool_calls or []:
        print("LLM が選んだ呼び出し:", call.function.name, call.function.arguments)


if __name__ == "__main__":
    asyncio.run(main())
