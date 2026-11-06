"""書き込みの道具（create_ticket）の直前で interrupt() し、承認・却下で再開する。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / langgraph 1.2.20 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated, TypedDict

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from mcp import Client, StdioServerParameters
from common.llm import chat
from common.mcp_tools import result_text, to_openai_tools

WRITE_TOOLS = {"create_ticket"}         # 人の承認が要る道具


class State(TypedDict):
    messages: Annotated[list, lambda a, b: a + b]


def build(mcp: Client, tools: list):
    async def llm_node(state):
        msg = await asyncio.to_thread(chat, state["messages"], tools)
        return {"messages": [msg.model_dump(exclude_none=True)]}

    async def tool_node(state):
        out = []
        for c in state["messages"][-1]["tool_calls"]:
            name, args = c["function"]["name"], json.loads(c["function"]["arguments"])
            if name in WRITE_TOOLS:     # 書き込みだけ止める。道具名と引数をそのまま見せる
                answer = interrupt({"tool": name, "args": args})
                if answer != "approve":
                    out.append({"role": "tool", "tool_call_id": c["id"],
                                "content": "人が却下しました。実行していません。やり直さず、却下されたことを利用者に伝えてください"})
                    continue
            r = await mcp.call_tool(name, args)
            out.append({"role": "tool", "tool_call_id": c["id"], "content": result_text(r)})
        return {"messages": out}

    g = StateGraph(State)
    g.add_node("llm", llm_node)
    g.add_node("tools", tool_node)
    g.add_edge(START, "llm")
    g.add_conditional_edges("llm", lambda s: "tools" if s["messages"][-1].get("tool_calls") else END)
    g.add_edge("tools", "llm")
    return g.compile(checkpointer=InMemorySaver())   # 止めた時点の状態を保存する


async def scenario(graph, thread: str, decision: str):
    cfg = {"configurable": {"thread_id": thread}}
    q = "モニターが壊れました。件名「モニター交換」本文「画面が映らない」でチケットを起票して"
    first = {"messages": [{"role": "user", "content": q}]}
    r = await graph.ainvoke(first, cfg)
    ask = r["__interrupt__"][0].value
    print(f"[{decision}] 承認待ち:", ask)
    r = await graph.ainvoke(Command(resume=decision), cfg)
    print(f"[{decision}] 最終回答:", r["messages"][-1]["content"])


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "servers" / "tickets.py")])
    async with Client(params) as mcp:
        tools = to_openai_tools((await mcp.list_tools()).tools)
        graph = build(mcp, tools)
        await scenario(graph, "t-ok", "approve")
        await scenario(graph, "t-ng", "reject")


asyncio.run(main())
