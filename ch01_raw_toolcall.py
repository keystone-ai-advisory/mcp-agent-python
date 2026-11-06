"""道具呼び出しの生 JSON を、3つの場面で画面に出す（道具の定義 → LLM の返事 → 結果の返し方）
見せること: LLM が関数を実行するのではなく、「この道具をこの引数で呼んで」と JSON で頼んでくるだけ。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common.llm import chat


def show(title, obj):
    print(f"\n=== {title} ===")
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def clean(m):
    """表示用: 長い署名(extra_content)は隠す"""
    d = m.model_dump(exclude_none=True)
    d.pop("extra_content", None)
    for c in d.get("tool_calls", []):
        c.pop("extra_content", None)
    return d


tools = [{"type": "function", "function": {
    "name": "add", "description": "2つの数の和を返す",
    "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                   "required": ["a", "b"]}}}]
show("1. LLM に渡す道具の定義 (tools=)", tools)

msgs = [{"role": "user", "content": "3と4を足すといくつ？道具を使って"}]
reply = chat(msgs, tools)
show("2. LLM の返事: content は空で tool_calls が入る", clean(reply))

call = reply.tool_calls[0]
result = int(json.loads(call.function.arguments)["a"] + json.loads(call.function.arguments)["b"])   # 実行するのは私たちのコード
back = {"role": "tool", "tool_call_id": call.id, "content": str(result)}
show("3. 結果を返すメッセージ (tool_call_id で呼び出しと結びつく)", back)

msgs += [reply.model_dump(exclude_none=True), back]
print("\n=== 4. 結果を見た LLM の最終回答 ===\n" + (chat(msgs, tools).content or ""))
