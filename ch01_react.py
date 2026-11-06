"""フレームワークを使わない、いちばん小さいエージェント（考える → 道具を使う → 結果を見る）
見せること: ループの中身は3つの判断だけ。道具が要らなくなったら、それが答え。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common.llm import chat

TOOLS = {"add": lambda a, b: a + b,
         "multiply": lambda a, b: a * b}
SPEC = [{"type": "function", "function": {"name": n, "description": f"2つの数の{d}を返す",
         "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                        "required": ["a", "b"]}}} for n, d in (("add", "和"), ("multiply", "積"))]

if __name__ == "__main__":
    msgs = [{"role": "user", "content": "3と4を足して、その結果に5を掛けると？道具を使って計算して"}]
    for step in range(6):                                # 暴走しないよう周回に上限を置く（次の回で強化する）
        m = chat(msgs, SPEC)
        if not m.tool_calls:                             # 道具を呼ばなくなったら、それが答え
            print("答え:", m.content)
            break
        msgs.append(m.model_dump(exclude_none=True))     # LLM の返事そのものを会話に足す
        for c in m.tool_calls:
            args = json.loads(c.function.arguments or "{}")
            result = TOOLS[c.function.name](**args)
            print(f"{step + 1}周目: {c.function.name}({args}) = {result}")
            msgs.append({"role": "tool", "tool_call_id": c.id, "content": str(result)})
