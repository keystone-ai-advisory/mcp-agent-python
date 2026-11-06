"""在庫サーバー（道具2つ）。型ヒントがそのまま入力スキーマ、TypedDict が構造化出力になる。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite（この回はLLM不使用）
"""
from typing import Literal, TypedDict

from mcp.server import MCPServer

mcp = MCPServer("inventory")

STOCK = {"ノートPC": 12, "モニター": 0, "キーボード": 37, "マウス": 25}


class StockInfo(TypedDict):
    item: str
    count: int
    available: bool


@mcp.tool()
def list_items() -> list[str]:
    """取り扱っている品名の一覧を返す"""
    return list(STOCK)


Item = Literal["ノートPC", "モニター",
               "キーボード", "マウス"]


@mcp.tool()
def get_stock(item: Item) -> StockInfo:
    """品名を受け取り、在庫数と、渡せるかどうかを返す"""
    n = STOCK[item]
    return {"item": item, "count": n, "available": n > 0}


if __name__ == "__main__":
    mcp.run()      # 引数なし = stdio で待ち受ける
