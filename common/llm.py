"""LLM の接続先を環境変数で切り替える（全章共通）
動作確認: 2026-11-06 / Windows 11 / Python 3.13 / openai 3.46.0

  既定（手元の Ollama・無料）:  何も設定しない
  Gemini（無料の鍵）:          LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
                               LLM_API_KEY=<AI Studio の鍵>  LLM_MODEL=gemini-3.1-flash-lite
"""
import os
import time

from openai import OpenAI, APIStatusError

BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")
MODEL = os.getenv("LLM_MODEL", "qwen3-vl:4b")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def chat(messages, tools=None, retries=4):
    """混雑（503）や回数制限（429）のときは、少し待ってやり直す"""
    for i in range(retries):
        try:
            kw = {"model": MODEL, "messages": messages}
            if tools:
                kw["tools"] = tools
            return client.chat.completions.create(**kw).choices[0].message
        except APIStatusError as e:
            if e.status_code not in (429, 503) or i == retries - 1:
                raise
            time.sleep(5 * (i + 1))
