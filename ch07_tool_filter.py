"""OpenAI Agents SDK の道具の絞り込み: create_static_tool_filter で、LLM に見せる道具を名前で決める（LLM は呼ばない）
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai-agents 0.24.0
"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).parent
from agents import Agent
from agents.mcp import MCPServerStdio, create_static_tool_filter

PARAMS = {"command": sys.executable, "args": ["-X", "utf8", str(HERE / "servers" / "tickets.py")]}


async def names(tool_filter=None):
    async with MCPServerStdio(params=PARAMS, tool_filter=tool_filter) as server:
        agent = Agent(name="確認用", mcp_servers=[server])
        return sorted(t.name for t in await server.list_tools(None, agent))


async def main():
    print("絞り込みなし        ->", await names())
    print("許可する名前を指定  ->", await names(create_static_tool_filter(allowed_tool_names=["get_ticket"])))
    print("禁止する名前を指定  ->", await names(create_static_tool_filter(blocked_tool_names=["create_ticket"])))


asyncio.run(main())
