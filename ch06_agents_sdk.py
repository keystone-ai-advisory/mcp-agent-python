"""OpenAI Agents SDK で MCP サーバー（在庫）をつなぎ、Gemini で動かす。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / openai-agents 0.24.0 / gemini-3.1-flash-lite
"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from common.llm import BASE_URL, API_KEY, MODEL   # 接続先は全章共通の環境変数（未設定なら手元の Ollama）

set_tracing_disabled(True)   # OpenAI の鍵が無いので、トレースの送信を止める

model = OpenAIChatCompletionsModel(
    model=MODEL,
    openai_client=AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY),
)


async def main():
    # MCP サーバーを子プロセスで起動。道具一覧は1回だけ取り寄せる
    async with MCPServerStdio(
        params={"command": sys.executable, "args": [str(HERE / "servers" / "inventory.py")]},
        cache_tools_list=True,
    ) as server:
        agent = Agent(name="ヘルプデスク", model=model, mcp_servers=[server],
                      instructions="社内ヘルプデスクです。在庫は道具で調べて、日本語で簡潔に答える。")
        result = await Runner.run(agent, "モニターとマウスの在庫を教えて")
        print(result.final_output)


asyncio.run(main())
