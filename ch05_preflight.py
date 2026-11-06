"""公開前の点検。待ち受け先・鍵なし/鍵あり・道具の中身を、実際に呼んで確かめる。
python ch05_preflight.py [URL] [トークン]   （既定は ch05_http_auth.py のサーバー）
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / LLM不要（モデル名なし）
"""
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from ch05_http_auth import TOKEN, URL as DEFAULT_URL

WRITE_WORDS = ("create", "delete", "update", "send", "write", "remove")
SUSPECT = ("ignore", "previous instructions", "必ず", "以前の指示", "こっそり")
ok = True


def report(good: bool, msg: str):
    global ok
    ok &= good
    print(("OK  " if good else "NG  ") + msg)


async def main(url: str, token: str):
    host = urlparse(url).hostname
    report(host in ("127.0.0.1", "localhost"), f"待ち受け先 {host}（外に開くなら理由を言えること）")
    # 鍵なしで呼ぶ → 断られるべき
    # 2026-07-28 版は Mcp-Method ヘッダーが必須。付けないと鍵とは無関係に 400 になる
    r = httpx2.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    headers={"Mcp-Protocol-Version": "2026-07-28", "Mcp-Method": "tools/list"})
    # 鍵の検査は MCP の処理より前。401/403 以外は鍵で止まらず MCP の層まで届いた（400 も同じ）
    report(r.status_code in (401, 403), f"鍵なし -> {r.status_code}（401 が正しい。他は鍵が効いていない）")
    # 鍵ありで呼ぶ → 通るべき
    http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"})
    async with Client(streamable_http_client(url, http_client=http)) as c:
        tools = (await c.list_tools()).tools
        report(True, f"鍵あり -> 道具 {len(tools)} 個")
        for t in tools:
            w = any(k in t.name for k in WRITE_WORDS)
            bad = [s for s in SUSPECT if s in (t.description or "")]
            print(f"    {t.name}: {'書き込み' if w else '読み取り'}" + (f" 説明文に怪しい語 {bad}" if bad else ""))
            report(not bad, f"{t.name} の説明文")
    print("点検結果:", "合格" if ok else "要対応")


asyncio.run(main(*(sys.argv[1:3] if len(sys.argv) > 2 else [(sys.argv + [DEFAULT_URL])[1], TOKEN])))
