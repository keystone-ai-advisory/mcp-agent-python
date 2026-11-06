"""MCP の道具一覧を、OpenAI 互換の tools 形式に変換する（第4章で作り、第6章でも使う）"""


def to_openai_tools(tools):
    """mcp.Client.list_tools() の .tools を、chat.completions の tools= に渡せる形にする"""
    return [{"type": "function",
             "function": {"name": t.name,
                          "description": t.description or "",
                          "parameters": t.input_schema}}      # v2 は snake_case（旧 inputSchema）
            for t in tools]


def result_text(result):
    """call_tool の結果を、LLM に返す1つの文字列にする"""
    text = "\n".join(getattr(c, "text", "") for c in result.content)   # 一覧は1行に1つ
    return f"エラー: {text}" if result.is_error else text
