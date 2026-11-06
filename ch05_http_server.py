"""在庫サーバーを Streamable HTTP で公開し、URL でつなぐ。
python ch05_http_server.py          → サーバーを起動（既定は 127.0.0.1:3001/mcp）
python ch05_http_server.py client   → 別の端末から URL でつないで道具を呼ぶ
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / LLM不要（モデル名なし）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp import Client
from servers.inventory import mcp

PORT = 3001  # 何も指定しないと 8000 になる


async def call():
    async with Client(f"http://127.0.0.1:{PORT}/mcp") as c:  # URL を渡すだけ
        print("道具:", [t.name for t in (await c.list_tools()).tools])
        print("結果:", (await c.call_tool("get_stock", {"item": "マウス"})).content[0].text)


if __name__ == "__main__":
    if sys.argv[1:] == ["client"]:
        asyncio.run(call())
    else:
        # host の既定は 127.0.0.1（自分のPCの中だけ）、path の既定は /mcp
        mcp.run(transport="streamable-http", port=PORT)
