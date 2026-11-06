"""第1章のループの「道具を実行する」部分を、MCP の call_tool に置き換えたエージェント。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client, StdioServerParameters
from common.llm import chat
from common.mcp_tools import to_openai_tools, result_text

SERVER = StdioServerParameters(command=sys.executable,
                               args=[str(Path(__file__).parent / "servers" / "inventory.py")])


async def main(question):
    async with Client(SERVER) as c:
        spec = to_openai_tools((await c.list_tools()).tools)
        msgs = [{"role": "user", "content": question}]
        for step in range(6):                              # 周回の上限（第1章と同じ）
            m = chat(msgs, tools=spec)
            if not m.tool_calls:
                return m.content
            msgs.append(m.model_dump(exclude_none=True))
            for call in m.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                text = result_text(await c.call_tool(call.function.name, args))   # ← ここだけが変わった
                print(f"{step+1}周目: {call.function.name}({args}) -> {text}")
                msgs.append({"role": "tool", "tool_call_id": call.id, "content": text})
        return "（周回の上限に達しました）"


if __name__ == "__main__":
    print("答え:", asyncio.run(main("モニターとキーボードの在庫を教えて")))
