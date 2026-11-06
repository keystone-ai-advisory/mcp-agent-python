"""サーバーのテスト。LLM もネットワークも使わない。
- 一覧・正常・エラーの3つは、サーバーの実体を mcp.Client に直接渡す（同じプロセスの中・速い）
- 最後の1つだけ、本物の子プロセス（stdio）で起動して、終了後に子が残らないことまで確かめる
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / pytest 8.4.2 / anyio 4.16.0
実行: pytest tests -q   （pytest==8.4.2。非同期は anyio のプラグインを使う）
"""
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters

sys.path.insert(0, str(Path(__file__).parent.parent))
from ch03_server_full import mcp as server

SERVER_PY = str(Path(__file__).parent.parent / "ch03_server_full.py")
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_list_tools():
    async with Client(server) as c:
        names = {t.name for t in (await c.list_tools()).tools}
    assert {"list_items", "get_stock", "reserve"} <= names


async def test_get_stock_ok():
    async with Client(server) as c:
        r = await c.call_tool("get_stock", {"item": "モニター"})
    assert not r.is_error
    assert r.structured_content == {"item": "モニター", "count": 0, "available": False}


async def test_unknown_item_is_error_with_hint():
    async with Client(server) as c:
        r = await c.call_tool("reserve", {"item": "プリンター", "qty": 1})
    assert r.is_error
    assert "list_items" in r.content[0].text      # 次の手が書いてあること


def _alive(tag: str) -> int:
    """コマンドラインに tag を含むプロセスの数（Windows の PowerShell で数える）"""
    cmd = f"(Get-CimInstance Win32_Process | ? {{ $_.CommandLine -like '*{tag}*' -and $_.ProcessId -ne $PID }} | measure).Count"
    out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return int(out.stdout.strip() or 0)


async def test_stdio_subprocess_and_cleanup():
    tag = f"tag{uuid.uuid4().hex[:8]}"
    params = StdioServerParameters(command=sys.executable, args=[SERVER_PY, tag])
    async with Client(params) as c:
        assert _alive(tag) >= 1                    # 動いている間は子プロセスがいる
        r = await c.call_tool("get_stock", {"item": "マウス"})
        assert r.structured_content["count"] == 25
    assert _alive(tag) == 0                        # 閉じたら残らない
