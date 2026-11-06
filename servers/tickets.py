"""チケットサーバー（道具その3）。書き込みをする道具なので、第7章で権限を絞る題材にする
起票すると番号（ハンドル）を返し、以後はその番号を引数で渡す（2026-07-28 版の仕様は、
呼び出しをまたぐ状態をセッションではなく「サーバーが発行するハンドル」で持つ）"""
import itertools
from typing import TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError   # 予想した失敗。文がそのままLLMに届く

mcp = MCPServer("tickets")

_seq = itertools.count(1001)


class Ticket(TypedDict):
    title: str
    body: str
    status: str


TICKETS: dict[str, Ticket] = {}


@mcp.tool()
def create_ticket(title: str, body: str) -> str:
    """問い合わせのチケットを起票し、チケット番号を返す"""
    tid = f"T-{next(_seq)}"
    TICKETS[tid] = {"title": title, "body": body, "status": "受付"}
    return tid


@mcp.tool()
def get_ticket(ticket_id: str) -> Ticket:
    """チケット番号から内容と状態を返す"""
    if ticket_id not in TICKETS:
        raise ToolError(f"{ticket_id} というチケットはありません")
    return TICKETS[ticket_id]


if __name__ == "__main__":
    mcp.run()
