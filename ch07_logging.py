"""ログと使用量: 道具名・引数・所要時間・トークン数を標準エラーに記録する。
あわせて、stdio サーバーで print() すると何が起きるかを、使い捨てのサーバーで安全に確かめる(2.3.0 では致命傷にならず、クライアント側にエラーが出る)
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import sys
import tempfile
import time
from contextlib import AsyncExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client, StdioServerParameters
from openai import APIStatusError
from ch07_least_privilege import open_all, ask, READ_ONLY
from common.llm import client, MODEL

USAGE = {"calls": 0, "prompt": 0, "completion": 0}


def log(*a):
    print(*a, file=sys.stderr, flush=True)      # ログは必ず標準エラーへ


def chat_logged(messages, tools=None):
    """chat と同じ形で、応答の usage を足し上げる（common.llm.chat は usage を捨てるため）"""
    for i in range(4):
        try:
            r = client.chat.completions.create(model=MODEL, messages=messages, tools=tools or None)
            break
        except APIStatusError as e:
            if e.status_code not in (429, 503) or i == 3:
                raise
            time.sleep(5 * (i + 1))
    u = r.usage
    USAGE["calls"] += 1
    USAGE["prompt"] += u.prompt_tokens if u else 0
    USAGE["completion"] += u.completion_tokens if u else 0
    log(f"[llm] usage={u.model_dump() if u else None}")
    return r.choices[0].message


def log_tool(name, args, out, sec):
    log(f"[tool] {name} args={args} 結果{len(out)}字 {sec * 1000:.0f}ms")


SERVER = 'from mcp.server import MCPServer\nmcp = MCPServer("t")\n{pre}\n@mcp.tool()\ndef ping() -> str:\n    {body}\n    return "pong"\nmcp.run()\n'


async def try_stdio(pre, body="pass"):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "s.py"
        f.write_text(SERVER.format(pre=pre, body=body), encoding="utf-8")
        try:
            async with asyncio.timeout(15):
                async with Client(StdioServerParameters(command=sys.executable, args=["-X", "utf8", str(f)])) as c:
                    return "成功: " + (await c.call_tool("ping", {})).content[0].text
        except BaseException as e:      # 壊れ方は版で違うので、型と先頭だけ見せる
            return f"失敗: {type(e).__name__}: {str(e)[:100]}"


async def main():
    async with AsyncExitStack() as stack:
        route, tools = await open_all(stack)
        if "--llm" in sys.argv:
            ans, _ = await ask("貸与PCの交換条件と、マウスの在庫を教えてください", route, tools, READ_ONLY,
                               llm=chat_logged, log=log_tool)
            print("答え:", ans)
            print("使用量の合計:", USAGE)
    print("print() を標準出力に書いたサーバー ->", await try_stdio('print("サーバー起動しました")'))
    print("改行なしの print() を書いたサーバー ->", await try_stdio('print("起動", end="", flush=True)'))
    print("道具の中で改行なしの print()      ->", await try_stdio("pass", 'print("処理中", end="", flush=True)'))
    print("標準エラーに書いたサーバー        ->", await try_stdio('import sys; print("起動しました", file=sys.stderr)'))


if __name__ == "__main__":
    asyncio.run(main())
