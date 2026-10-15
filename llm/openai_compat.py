# -*- coding: utf-8 -*-
"""通用 OpenAI 兼容 Chat 客户端（用 requests 实现，无需 openai SDK）。

同时适配：千问 DashScope compatible-mode、浙大先生/aihub、DeepSeek 等任意
提供 /chat/completions 的端点，做到“一个 Provider 通吃”。
"""
from __future__ import annotations

import json

import requests

from core.provider_base import LLMProvider


class OpenAICompatProvider(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model: str,
                 timeout: int = 60, name: str = "openai-compat"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.name = name
        self._sess = requests.Session()

    def chat(self, messages: list, **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model, "messages": messages, "stream": False}
        payload.update(kwargs)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = self._sess.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
