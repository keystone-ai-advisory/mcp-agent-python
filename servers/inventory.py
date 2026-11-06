"""在庫サーバー（社内ヘルプデスク・エージェントの道具その1）"""
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError   # 予想した失敗。文がそのままLLMに届く

mcp = MCPServer("inventory")

STOCK = {"ノートPC": 12, "モニター": 0, "キーボード": 37, "マウス": 25}


@mcp.tool()
def list_items() -> list[str]:
    """取り扱っている品名の一覧を返す"""
    return list(STOCK)


@mcp.tool()
def get_stock(item: str) -> str:
    """品名を受け取り、在庫数を返す。品名は list_items の表記に合わせる"""
    if item not in STOCK:
        raise ToolError(f"{item} は取り扱いがありません。list_items で品名を確かめてください")
    return f"{item} の在庫は {STOCK[item]} 台です"


if __name__ == "__main__":
    mcp.run()
