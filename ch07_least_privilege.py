"""道具の許可リスト（自作）: 読むだけの道具だけを LLM に見せ、許可外の名前で呼ばれたら実行せずに断る
（第7章〜第8章の部品としても使う: open_all / call_guarded / ask）
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import logging
import sys
import time
from contextlib import AsyncExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client
from servers import inventory, rules, tickets
from common.llm import chat
from common.mcp_tools import to_openai_tools, result_text

logging.getLogger("httpx").setLevel(logging.WARNING)   # 通信の INFO ログで画面を埋めない

READ_ONLY = {"list_items", "get_stock", "search_rules", "get_ticket"}   # 読むだけ
WRITE = {"create_ticket"}                                               # 書き込み


async def open_all(stack, servers=(inventory.mcp, rules.mcp, tickets.mcp)):
    """サーバーを開き、道具名 → クライアントの対応表と、道具の一覧を返す"""
    route, tools = {}, []
    for s in servers:
        c = await stack.enter_async_context(Client(s))
        for t in (await c.list_tools()).tools:
            route[t.name] = c
            tools.append(t)
    return route, tools


async def call_guarded(route, name, args, allowed):
    """許可リストに無い名前は、サーバーに送らずに断る"""
    if name not in allowed or name not in route:
        return f"エラー: {name} は許可されていない道具です"
    return result_text(await route[name].call_tool(name, args))


async def ask(question, route, tools, allowed, approve=None, llm=chat, log=None, max_turns=6):
    """LLM には許可した道具だけを見せる。書き込みは approve(name, args) が True のときだけ実行"""
    shown = to_openai_tools([t for t in tools if t.name in allowed])
    msgs = [{"role": "system", "content": "社内ヘルプデスクの担当です。道具で調べて、日本語で簡潔に答えてください。手元の道具で出来ない操作は、出来ないと答えてください。"},
            {"role": "user", "content": question}]
    calls = []
    for _ in range(max_turns):
        m = llm(msgs, shown)
        msgs.append(m.model_dump(exclude_none=True))
        if not m.tool_calls:
            return m.content, calls
        for tc in m.tool_calls:
            name, args = tc.function.name, json.loads(tc.function.arguments or "{}")
            t0 = time.time()
            if name in WRITE and approve and not approve(name, args):
                out = "エラー: 人が承認しなかったため実行していません。やり直さず、そのことを利用者に伝えてください"
            else:
                out = await call_guarded(route, name, args, allowed)
            calls.append((name, args, out))
            if log:
                log(name, args, out, time.time() - t0)
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": out})
    return "(周回の上限に達しました)", calls


async def main():
    async with AsyncExitStack() as stack:
        route, tools = await open_all(stack)
        print("LLM に見せる道具:", sorted(READ_ONLY & set(route)))
        # 1) 許可外の名前で呼ばれたら断る（LLM なしで確認）
        print("書き込みを直接呼ぶ ->", await call_guarded(route, "create_ticket", {"title": "x", "body": "y"}, READ_ONLY))
        print("存在しない名前 ->", await call_guarded(route, "delete_all", {}, READ_ONLY))
        # 2) 読むだけの許可で、起票を頼む（create_ticket は見えない）
        ans, calls = await ask("モニターの在庫を調べて、無ければ起票もしてください", route, tools, READ_ONLY)
        print("呼んだ道具:", [c[0] for c in calls], "\n答え:", ans)


if __name__ == "__main__":
    asyncio.run(main())
