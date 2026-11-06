"""社内規程サーバー（道具その2）。規程の本文はリソース、問い合わせの型はプロンプトとして出す"""
from mcp.server import MCPServer

mcp = MCPServer("rules")

RULES = {
    "貸与PC": "貸与PCの交換は、購入から4年を過ぎたもの、または故障したものに限る。申請はヘルプデスクへチケットで行う。",
    "周辺機器": "モニター・キーボード・マウスは、在庫があれば申請の翌営業日に渡す。在庫が無いときは入荷待ちとする。",
    "在宅勤務": "在宅勤務用の機器の持ち出しは、上長の承認を得てから行う。",
}


@mcp.resource("rules://{name}")
def rule(name: str) -> str:
    """規程の本文（name は 貸与PC・周辺機器・在宅勤務 のいずれか）"""
    return RULES.get(name, f"{name} という規程はありません")


@mcp.tool()
def search_rules(keyword: str) -> list[str]:
    """キーワードを含む規程の名前と本文を返す。キーワードは「貸与PC」「モニター」のような短い語を1つ渡す"""
    return [f"{k}: {v}" for k, v in RULES.items() if keyword in k or keyword in v]


@mcp.prompt()
def ticket_request(item: str, reason: str) -> str:
    """機器の申請チケットを書くときの型"""
    return f"次の内容で機器の申請チケットを起票してください。品名: {item}。理由: {reason}。規程に合っているかも確かめること。"


if __name__ == "__main__":
    mcp.run()
