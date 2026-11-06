"""LangGraph 単体（langchain 系なし）で、LLM 節と道具節の2節グラフから MCP を呼ぶ。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / langgraph 1.2.20 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated, TypedDict

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from langgraph.graph import END, START, StateGraph
from mcp import Client, StdioServerParameters
from common.llm import chat
from common.mcp_tools import result_text, to_openai_tools


def add(a: list, b: list) -> list:      # メッセージは上書きせず足していく
    return a + b


class State(TypedDict):
    messages: Annotated[list, add]


async def run(mcp: Client, tools: list, question: str):
    async def llm_node(state):          # 節1: LLM を呼ぶ
        msg = await asyncio.to_thread(chat, state["messages"], tools)
        return {"messages": [msg.model_dump(exclude_none=True)]}

    async def tool_node(state):         # 節2: 道具の呼び出しを実行（開いたままの mcp を使う）
        out = []
        for c in state["messages"][-1]["tool_calls"]:
            r = await mcp.call_tool(c["function"]["name"], json.loads(c["function"]["arguments"]))
            out.append({"role": "tool", "tool_call_id": c["id"], "content": result_text(r)})
        return {"messages": out}

    def route(state):                   # 呼び出しがあれば道具節へ、無ければ終わり
        return "tools" if state["messages"][-1].get("tool_calls") else END

    g = StateGraph(State)
    g.add_node("llm", llm_node)
    g.add_node("tools", tool_node)
    g.add_edge(START, "llm")
    g.add_conditional_edges("llm", route)
    g.add_edge("tools", "llm")
    final = await g.compile().ainvoke({"messages": [{"role": "user", "content": question}]})
    print(final["messages"][-1]["content"])


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "servers" / "inventory.py")])
    # セッションはグラフの外で開き、ainvoke が終わるまで閉じない
    async with Client(params) as mcp:
        tools = to_openai_tools((await mcp.list_tools()).tools)
        await run(mcp, tools, "モニターとマウスの在庫を教えて")


asyncio.run(main())
