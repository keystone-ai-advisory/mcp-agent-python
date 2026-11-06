"""固定トークンだけを通す学習用の鍵。TokenVerifier と AuthSettings を組で渡す。
python ch05_http_auth.py          → 鍵つきサーバーを起動（127.0.0.1:3002/mcp）
python ch05_http_auth.py client   → 鍵なし（401）と鍵あり（成功）を試す
本番では、認可サーバーが発行したトークンを確かめる。固定文字列は学習専用。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / LLM不要（モデル名なし）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from servers import tickets

PORT = 3002
URL = f"http://127.0.0.1:{PORT}/mcp"
TOKEN = "study-token-do-not-use-in-production"


class StaticVerifier:  # TokenVerifier（verify_token を持つだけでよい）
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != TOKEN:
            return None  # None を返すと 401
        return AccessToken(token=token, client_id="study-client", scopes=[])


mcp = MCPServer(
    "tickets-auth",
    token_verifier=StaticVerifier(),
    auth=AuthSettings(
        issuer_url="http://127.0.0.1:9000",   # 学習用の見せかけ。本番は認可サーバーの URL
        resource_server_url=None,            # 省略不可の引数。None でよい
    ),
)
mcp.tool()(tickets.create_ticket)
mcp.tool()(tickets.get_ticket)


async def call():
    # 鍵なし: 生の HTTP で状態コードを見る（Client は 401 を MCPError にまとめてしまう）
    r = httpx2.post(URL, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    print("鍵なし:", r.status_code, r.headers.get("www-authenticate"))
    # 鍵あり: Authorization ヘッダー付きの HTTP クライアントを Client に渡す
    http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"})
    async with Client(streamable_http_client(URL, http_client=http)) as c:
        r = await c.call_tool("create_ticket", {"title": "試験", "body": "鍵あり"})
        print("鍵あり: 起票 ->", r.content[0].text)


if __name__ == "__main__":
    if sys.argv[1:] == ["client"]:
        asyncio.run(call())
    else:
        mcp.run(transport="streamable-http", port=PORT)
