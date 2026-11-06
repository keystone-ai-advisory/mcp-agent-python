"""会話の履歴を持ち越して、「じゃあそれで起票して」のような続きの指示に答える。
履歴を切り詰めるときも、道具の呼び出しとその結果を引き離さない。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from contextlib import AsyncExitStack
from common.llm import chat
from common.mcp_tools import result_text
from ch04_multi_server import connect_all

MAX_MESSAGES = 12


def trim(msgs, limit=MAX_MESSAGES):
    """古い方から捨てる。ただし先頭は必ず user にそろえる。
    assistant(tool_calls) と、それに答える tool の組が途中で切れるのを防ぐ"""
    if len(msgs) <= limit:
        return msgs
    start = len(msgs) - limit
    while start < len(msgs) and msgs[start]["role"] != "user":
        start += 1                                         # 次の user まで進める（組をまるごと捨てる）
    return msgs[start:]


async def ask(msgs, question, spec, route):
    msgs.append({"role": "user", "content": question})
    for _ in range(8):
        m = chat(trim(msgs), tools=spec)
        if not m.tool_calls:
            msgs.append({"role": "assistant", "content": m.content})
            return m.content
        msgs.append(m.model_dump(exclude_none=True))
        for call in m.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            text = result_text(await route[call.function.name].call_tool(call.function.name, args))
            print(f"  [道具] {call.function.name}({args}) -> {text}")
            msgs.append({"role": "tool", "tool_call_id": call.id, "content": text})
    return "（周回の上限に達しました）"


async def main():
    async with AsyncExitStack() as stack:
        spec, route = await connect_all(stack)
        msgs = []                                          # 記憶の正体は、この list だけ
        for q in ["モニターの在庫は？", "じゃあそれで入荷待ちとして起票して", "いま起票した件の状態は？"]:
            print("Q:", q)
            print("A:", await ask(msgs, q, spec, route))


if __name__ == "__main__":
    asyncio.run(main())
