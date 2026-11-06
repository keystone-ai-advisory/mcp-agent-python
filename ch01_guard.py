"""ch01_react.py に3つの見張りを足す: 周回の上限・同じ呼び出しの繰り返し・存在しない道具
見せること: 暴走する LLM を「台本どおりに暴走する偽の LLM」で再現し、見張りが1つずつ発動する様子。
  ※ 再現を確実にし、LLM の呼び出しを節約するため、既定は偽の LLM（stub）。
    `python ch01_guard.py --live` で本物の LLM に正常な質問を1つ投げ、見張りが邪魔をしないことも確かめられる。
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / 偽LLMは通信なし・--live は gemini-3.1-flash-lite
"""
import json, sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).parent))
from ch01_react import TOOLS, SPEC


def run_agent(question, llm, max_steps=5):
    msgs, seen = [{"role": "user", "content": question}], set()
    for step in range(1, max_steps + 1):
        m = llm(msgs)
        if not m.tool_calls:
            return f"答え: {m.content}"
        msgs.append(m.model_dump(exclude_none=True))
        for c in m.tool_calls:
            name, raw = c.function.name, c.function.arguments or "{}"
            if (name, raw) in seen:                                   # 見張り2: 同じ呼び出しの繰り返し
                return f"停止: {step}周目に {name}{raw} を繰り返したので打ち切りました"
            seen.add((name, raw))
            try:
                if name not in TOOLS:                                 # 見張り3: 存在しない道具
                    raise ValueError(f"その道具はありません。使えるのは {list(TOOLS)} です")
                result = TOOLS[name](**json.loads(raw))
            except Exception as e:                                    # 壊れた JSON・引数違いもここ
                result = f"エラー: {type(e).__name__}: {e}"            # 落とさず、結果として LLM に返す
            print(f"  {step}周目: {name}({raw}) -> {result}")
            msgs.append({"role": "tool", "tool_call_id": c.id, "content": str(result)})
    return f"停止: {max_steps}周しても終わりませんでした"             # 見張り1: 周回の上限


# ---- 偽の LLM（台本どおりに動く）。実物と同じ形の返事を作る ----
def fake_reply(name=None, args=None, content=None, n=[0]):
    n[0] += 1
    calls = [NS(id=f"call_{n[0]}", type="function", function=NS(name=name, arguments=json.dumps(args)
               if isinstance(args, dict) else args))] if name else None
    m = NS(content=content, tool_calls=calls)
    m.model_dump = lambda **kw: {"role": "assistant", "content": content, **(
        {"tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.function.name,
         "arguments": c.function.arguments}} for c in calls]} if calls else {})}
    return m


def never_ends(msgs):                          # 毎回違う引数で呼び続ける
    return fake_reply("add", {"a": len(msgs), "b": 1})


def same_again(msgs):                          # 同じ呼び出しを繰り返す
    return fake_reply("add", {"a": 3, "b": 4})


def wrong_name(msgs):                          # 存在しない道具 → エラーを見て立て直す
    last = msgs[-1]["content"]
    if last.startswith("エラー"):
        return fake_reply("add", {"a": 3, "b": -4})
    if last.lstrip("-").isdigit():
        return fake_reply(content=f"足し算で求めて {last} です")
    return fake_reply("subtract", {"a": 3, "b": 4})


def broken_json(msgs):                         # 引数の JSON が壊れて届く → エラーを見て立て直す
    last = msgs[-1]["content"]
    if last.startswith("エラー"):
        return fake_reply("add", {"a": 3, "b": 4})
    return fake_reply("add", '{"a": 3, "b":') if last.startswith("3から") else fake_reply(content=f"{last} です")


if __name__ == "__main__":
    if "--live" in sys.argv:
        from common.llm import chat
        print(run_agent("3と4を足して、その結果に5を掛けると？道具を使って計算して", lambda m: chat(m, SPEC)))
    else:
        for title, llm in (("1 終わらない（周回上限=3）", never_ends), ("2 同じ呼び出しの繰り返し", same_again),
                           ("3 存在しない道具", wrong_name),
                           ("4 壊れた JSON", broken_json)):
            print(f"[{title}]")
            print(" ", run_agent("3から4を引いて", llm, max_steps=3))
