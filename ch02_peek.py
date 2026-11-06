"""stdio で流れる JSON を横取りして表示する（クライアント ⇄ [この覗き窓] ⇄ サーバー）
見せること: mcp.Client(mode='auto') が最初に何を送るか、道具の一覧・呼び出しがどんな JSON か。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / LLM は使わない
使い方:  python ch02_peek.py      （--proxy 付きは自分自身が覗き窓の子プロセスとして動く）
"""
import asyncio, subprocess, sys, threading
from pathlib import Path

HERE = Path(__file__).parent
SERVER = str(HERE / "servers" / "inventory.py")


def proxy():
    """サーバーを子プロセスで起動し、行ごとに中継しながら stderr に写す"""
    srv = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)

    def pump(src, dst, mark):
        for line in src:
            print(f"{mark} {line.rstrip()[:300]}", file=sys.stderr, flush=True)
            dst.write(line); dst.flush()
        if dst is srv.stdin:
            srv.stdin.close()

    sys.stderr.reconfigure(encoding="utf-8"); sys.stdin.reconfigure(encoding="utf-8"); sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    t = threading.Thread(target=pump, args=(sys.stdin, srv.stdin, "クライアント→サーバー"))
    t.start()
    pump(srv.stdout, sys.stdout, "サーバー→クライアント")
    srv.wait()


async def main():
    from mcp import Client, StdioServerParameters
    params = StdioServerParameters(command=sys.executable, args=[__file__, "--proxy"])
    async with Client(params) as c:
        print("--- 接続完了。protocol_version =", c.protocol_version, file=sys.stderr, flush=True)
        print("--- list_tools()", file=sys.stderr, flush=True)
        await c.list_tools()
        print("--- call_tool(get_stock)", file=sys.stderr, flush=True)
        await c.call_tool("get_stock", {"item": "マウス"})
        print("--- 終了", file=sys.stderr, flush=True)


if __name__ == "__main__":
    proxy() if "--proxy" in sys.argv else asyncio.run(main())
