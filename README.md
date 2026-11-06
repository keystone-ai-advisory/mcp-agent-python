# mcp-agent-python

Udemy 講座「【2026年11月版】AIエージェント開発入門｜PythonでMCPサーバーから自作・無料のローカルLLMでも動く」の配布コードです。

社内ヘルプデスク・エージェント（在庫・社内規程・チケットの3つの MCP サーバー）を、フレームワークに頼らず一から作り、
後半で OpenAI Agents SDK と LangGraph に載せ替え、権限・承認・評価・ログまで足します。

- 公式 MCP Python SDK **2.3.0**、MCP 仕様 **2026-07-28 版**に合わせています
- LLM は OpenAI 互換の呼び方なので、**Ollama（無料・手元だけ）**でも **Gemini の無料の鍵**でも動きます
- 動作確認: 2026-11-06 / Windows 11 / Python 3.13（uv で Python 3.12.11 の環境にも入れて試験が通ることを確認）

## 準備

```powershell
# uv が入っている前提（https://docs.astral.sh/uv/ の案内に従って入れる）
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
.venv\Scripts\python.exe check_env.py      # 全部そろったかを点検
```

macOS / Linux では `.venv/bin/python` に読み替えてください。

### LLM の接続先（環境変数）

| 変数 | 既定（何も設定しないとき） | Gemini の例 |
|---|---|---|
| `LLM_BASE_URL` | `http://127.0.0.1:11434/v1`（Ollama） | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `LLM_API_KEY` | `ollama` | Google AI Studio で作った鍵 |
| `LLM_MODEL` | `qwen3-vl:4b` | `gemini-3.1-flash-lite` |

- 鍵はコードやファイルに書かず、環境変数で渡してください
- Gemini の無料枠は回数が少なめです（2026-11 時点、`gemini-3.8-flash` は1日20回で尽きました）。収録は `gemini-3.1-flash-lite` で行いました
- 無料の鍵に業務のデータを送らないでください（利用条件は Google の規約で確かめてください）

## ファイルと章の対応

| 章 | ファイル | 内容 |
|---|---|---|
| はじめに | `check_env.py` | 環境の点検 |
| 第1章 | `ch01_raw_toolcall.py` / `ch01_react.py` / `ch01_guard.py` | 道具呼び出しの生の JSON、30行の ReAct ループ、止め方（ch01_guard.py は既定で作り物の LLM、`--live` で本物） |
| 第2章 | `ch02_peek.py` / `ch02_old_vs_new.py` | stdio の通信を覗く、v1 流の書き方で出るエラー |
| 第3章 | `ch03_server_tools.py` / `ch03_server_full.py` / `tests/` | MCPServer で道具・リソース・プロンプト、エラーの返し方、pytest（`pytest tests -q`） |
| 第4章 | `ch04_client.py` / `ch04_tools_to_llm.py` / `ch04_agent.py` / `ch04_multi_server.py` / `ch04_agent_memory.py` | クライアント、道具一覧の変換、エージェント、複数サーバー、会話の記憶 |
| 第5章 | `ch05_http_server.py` / `ch05_http_auth.py` / `ch05_preflight.py` / `ch05_hosts/` | Streamable HTTP、トークン認証、公開前の点検、アプリの設定例（例のみ・未登録） |
| 第6章 | `ch06_agents_sdk.py` / `ch06_langgraph_adapter.py` / `ch06_langgraph_approval.py` | OpenAI Agents SDK、LangGraph（MCP は自前でつなぐ）、interrupt() による人の承認 |
| 第7章 | `ch07_least_privilege.py` / `ch07_tool_filter.py` / `ch07_injection_demo.py` / `ch07_eval.py` / `ch07_logging.py` | 許可リスト、Agents SDK の絞り込み、プロンプトインジェクション、評価、ログと使用量 |
| 第8章 | `ch08_helpdesk_agent.py` | 完成形（`--dry` で LLM なし、`--eval` で採点） |

共通部品: `common/llm.py`（接続先と再試行）、`common/mcp_tools.py`（道具一覧の変換）、`servers/`（在庫・規程・チケットの3サーバー）

## 版

`requirements.txt` で固定しています: mcp[cli]==2.3.0 / openai==3.46.0 / openai-agents==0.24.0 / langgraph==1.2.20 / pytest==8.4.2 / anyio==4.16.0

ライブラリは更新が速いので、版を上げると動かなくなることがあります。まずはこの版のまま動かしてください。
