"""テストケースでエージェントを採点する: 呼ぶべき道具（呼び出し記録で機械判定）と、答えに含むべき語
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
"""
import asyncio
import json
import sys
import time
from contextlib import AsyncExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ch07_least_privilege import open_all, ask, READ_ONLY


async def run_eval(route, tools, allowed=READ_ONLY, runs=1, ask_fn=ask):
    cases = json.loads((Path(__file__).parent / "eval_cases.json").read_text(encoding="utf-8"))
    passed = total = 0
    for case in cases:
        for _ in range(runs):
            answer, calls = await ask_fn(case["question"], route, tools, allowed)
            tool_ok = case["tool"] in [c[0] for c in calls]          # 動き: 機械的に判定
            need, text = case["must_include"], answer or ""
            words_ok = all(w in text for w in need)   # 要点: 語の有無
            passed += tool_ok and words_ok
            total += 1
            print(f"{'OK' if tool_ok and words_ok else 'NG'} 道具={tool_ok} 語={words_ok} {case['question']}")
    return passed, total


async def main():
    async with AsyncExitStack() as stack:
        route, tools = await open_all(stack)
        t0 = time.time()
        passed, total = await run_eval(route, tools)
        print(f"点数: {passed}/{total}  所要 {time.time() - t0:.1f} 秒")


if __name__ == "__main__":
    asyncio.run(main())
