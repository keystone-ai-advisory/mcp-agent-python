"""在庫サーバーの完成形: 道具 + 規程のリソース + 起票文のプロンプト + エラーの返し方。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite（この回はLLM不使用）
"""
from typing import Literal, TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError   # 予想した失敗用

mcp = MCPServer("inventory")

STOCK = {"ノートPC": 12, "モニター": 0, "キーボード": 37, "マウス": 25}
RULES = {"貸与PC": "貸与PCの交換は、購入から4年を過ぎたもの、または故障したものに限る。",
         "周辺機器": "モニター・キーボード・マウスは、在庫があれば翌営業日に渡す。在庫が無いときは入荷待ち。"}


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


@mcp.tool()
def reserve(item: str, qty: int) -> str:
    """在庫を取り置く。足りないときは、次の手を添えたエラーを返す"""
    if item not in STOCK:                                    # 対象が無い: 別の候補を教える
        raise ToolError(
            f"{item} は取り扱いがありません。"
            "list_items で品名を確かめてください")
    if STOCK[item] < qty:                                    # 条件が合わない: どうすればよいか書く
        raise ToolError(
            f"{item} は残り {STOCK[item]} 台です。"
            "数を減らすか、入荷待ちで起票してください")
    STOCK[item] -= qty
    return f"{item} を {qty} 台取り置きました"


@mcp.tool()
def broken_report() -> str:
    """（実演用）サーバー内部で失敗する道具。ToolError 以外の例外を投げる"""
    raise ValueError("/srv/secret/inventory.db を開けません")  # 中身は LLM に届かないのが正しい


@mcp.resource("rules://{name}")
def rule(name: str) -> str:
    """社内規程の本文（name は 貸与PC・周辺機器）"""
    return RULES.get(name, f"{name} という規程はありません")


@mcp.prompt()
def ticket_request(item: str, reason: str) -> str:
    """機器の申請チケットを書くときの型"""
    return f"次の内容で申請チケットを起票してください。品名: {item}。理由: {reason}。規程に合うかも確かめること。"


if __name__ == "__main__":
    mcp.run()
