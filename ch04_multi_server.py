"""在庫・規程・チケットの3サーバーを束ねて1つのエージェントにする。
道具名 -> クライアント の対応表で振り分け、起票で得た番号（ハンドル）は次の呼び出しの引数で渡す。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from contextlib import AsyncExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client, StdioServerParameters
from common.llm import chat
from common.mcp_tools import to_openai_tools, result_text

SERVERS = ["inventory", "rules", "tickets"]


async def connect_all(stack):
    """3つの子プロセスを開き、(道具定義の一覧, 道具名->クライアント) を返す。名前の重複は止める"""
    spec, route = [], {}
    for name in SERVERS:
        params = StdioServerParameters(command=sys.executable,
                                       args=[str(Path(__file__).parent / "servers" / f"{name}.py")])
        c = await stack.enter_async_context(Client(params))
        tools = (await c.list_tools()).tools
        for t in tools:
            if t.name in route:                           # 重なると LLM は区別できない
                raise ValueError(f"道具名が重複: {t.name}（サーバー名を頭に付けるなどで避ける）")
            route[t.name] = c
        spec += to_openai_tools(tools)
    return spec, route


async def main(question):
    async with AsyncExitStack() as stack:                 # 抜けるときに3つとも閉じる
        spec, route = await connect_all(stack)
        print("道具:", list(route))
        msgs = [{"role": "user", "content": question}]
        for step in range(8):
            m = chat(msgs, tools=spec)
            if not m.tool_calls:
                return m.content
            msgs.append(m.model_dump(exclude_none=True))
            for call in m.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                text = result_text(await route[call.function.name].call_tool(call.function.name, args))
                print(f"{step+1}周目: {call.function.name}({args}) -> {text}")
                msgs.append({"role": "tool", "tool_call_id": call.id, "content": text})
        return "（周回の上限に達しました）"


if __name__ == "__main__":
    print("答え:", asyncio.run(main(
        "モニターの在庫を調べて、無ければ入荷待ちとして申請チケットを起票し、そのチケットの状態も教えて")))
