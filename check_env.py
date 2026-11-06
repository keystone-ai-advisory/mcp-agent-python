"""環境の点検: Python・ライブラリの版・LLM の応答・Node の版を順に確かめ、足りないものを日本語で出す
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / mcp 2.3.0 / openai 3.46.0 / gemini-3.1-flash-lite
標準ライブラリだけで動く（ライブラリが無くても点検そのものは落ちない）。
"""
import json, os, shutil, subprocess, sys, urllib.request
from importlib.metadata import PackageNotFoundError, version

PINS = {"mcp": "2.3.0", "openai": "3.46.0"}                       # 第1章から必須
LATER = {"openai-agents": "0.24.0", "langgraph": "1.2.20", "pytest": "8.4.2"}  # 第6章以降
BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")
bad = 0


def report(ok, label, hint=""):
    global bad
    bad += 0 if ok else 1
    print(f"[{'OK' if ok else 'NG'}] {label}" + (f"\n     → {hint}" if hint and not ok else ""))


v = sys.version_info
report(v >= (3, 12), f"Python {v.major}.{v.minor}.{v.micro}（3.12 以上を推奨）", "uv python install 3.12 などで入れ直す")

for name, want in {**PINS, **LATER}.items():
    try:
        have = version(name)
        report(have == want, f"{name} {have}（固定: {want}）", f"pip install {name}=={want}")
    except PackageNotFoundError:
        if name in PINS:
            report(False, f"{name} が入っていない", f"pip install {name}=={want}")
        else:
            print(f"[--] {name} 未インストール（第6章以降で使う。固定: {want}）")

try:                                                                # プロキシ設定を拾わず直接つなぐ
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(BASE_URL.rstrip("/") + "/models", headers={"Authorization": f"Bearer {API_KEY}"})
    n = len(json.load(opener.open(req, timeout=10)).get("data", []))
    report(True, f"LLM に接続できた: {BASE_URL}（モデル {n} 件。使用: {os.getenv('LLM_MODEL', 'qwen3-vl:4b')}）")
except Exception as e:
    report(False, f"LLM に接続できない: {BASE_URL}（{type(e).__name__}）",
           "Ollama なら起動して `ollama pull <モデル>`。Gemini なら LLM_BASE_URL / LLM_API_KEY / LLM_MODEL を確かめる")

node = shutil.which("node")
if node:
    out = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    nums = tuple(int(x) for x in out.lstrip("v").split(".")[:3])
    report(nums >= (22, 19, 0), f"Node {out}（Inspector には 22.19 以上）", "https://nodejs.org から LTS を入れ直す")
else:
    report(False, "Node が見つからない（第3章の Inspector で使う）", "https://nodejs.org から LTS を入れる")

print("\n全部そろいました" if bad == 0 else f"\n{bad} 件、直してから先へ進みましょう")
sys.exit(1 if bad else 0)
