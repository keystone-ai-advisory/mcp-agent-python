"""社内ヘルプデスク・エージェントの完成形: 3サーバー(stdio) + 許可リスト + 書き込みの承認 + ログ
3つの場面（在庫・規程・起票）を通しで流す。--eval を付けると第7章の採点も続けて流す
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from mcp import Client, StdioServerParameters
from ch07_least_privilege import ask, READ_ONLY, WRITE
from ch07_logging import chat_logged, log_tool, USAGE


async def open_stdio(stack):
    """3つのサーバーを、それぞれ別の子プロセス(stdio)として起動する"""
    route, tools = {}, []
    for name in ("inventory", "rules", "tickets"):
        params = StdioServerParameters(command=sys.executable, args=["-X", "utf8", str(HERE / "servers" / f"{name}.py")])
        c = await stack.enter_async_context(Client(params))
        for t in (await c.list_tools()).tools:
            route[t.name] = c
            tools.append(t)
    return route, tools


def approve(name, args):
    """書き込みは人が決める。HELPDESK_APPROVE=yes なら収録用に自動で承認する"""
    print(f"  [承認] {name} {args}")
    ok = os.getenv("HELPDESK_APPROVE") == "yes" or input("  実行してよいですか [y/N] ").lower() == "y"
    print("  ->", "承認" if ok else "却下")
    return ok


SCENARIOS = ["モニターの在庫はありますか", "貸与PCを交換できる条件を教えてください",
             "モニターの画面が映らなくなりました。交換申請のチケットを、件名「モニター交換」で起票してください"]


async def main():
    async with AsyncExitStack() as stack:
        route, tools = await open_stdio(stack)
        if "--dry" in sys.argv:      # LLM を使わず、3サーバーの起動と許可リストだけ確かめる
            from ch07_least_privilege import call_guarded
            print("道具:", sorted(route))
            print(await call_guarded(route, "get_stock", {"item": "モニター"}, READ_ONLY))
            print(await call_guarded(route, "create_ticket", {"title": "a", "body": "b"}, READ_ONLY))
            return
        for q in SCENARIOS:
            print("\n質問:", q)
            ans, calls = await ask(q, route, tools, READ_ONLY | WRITE, approve=approve, llm=chat_logged, log=log_tool)
            print("答え:", ans)
        print("\n使用量の合計:", USAGE)
        if "--eval" in sys.argv:
            from ch07_eval import run_eval
            p, t = await run_eval(route, tools, READ_ONLY)
            print(f"採点: {p}/{t}")


if __name__ == "__main__":
    asyncio.run(main())
