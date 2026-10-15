# -*- coding: utf-8 -*-
"""千问 / DashScope 的向量化与重排能力（可选，需配置 DASHSCOPE_API_KEY）。

chat 走 OpenAI 兼容接口（见 openai_compat.py），这里补齐 embedding 与 rerank。
两个 Provider 均为可选，拿不到 Key 时主流程会自动退回到本地 TF-IDF 检索。
"""
from __future__ import annotations

import json

import requests

from core.provider_base import EmbeddingProvider, RerankProvider


class QwenEmbeddingProvider(EmbeddingProvider):
    name = "qwen-embedding"

    def __init__(self, api_key: str, model: str = "text-embedding-v3",
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
                 timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._sess = requests.Session()

    def embed(self, texts: list) -> list:
        url = f"{self.base_url}/embeddings"
        payload = {"model": self.model, "input": texts}
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
        return [item["embedding"] for item in data["data"]]


class QwenRerankProvider(RerankProvider):
    name = "qwen-rerank"

    def __init__(self, api_key: str, model: str = "qwen3-rerank",
                 base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
                 timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._sess = requests.Session()

    def rerank(self, query: str, docs: list, top_n: int = 5) -> list:
        payload = {
            "model": self.model,
            "input": {"query": query, "documents": docs},
            "parameters": {"top_n": top_n, "return_documents": False},
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = self._sess.post(
            self.base_url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("output", {}).get("results", [])
        return [r["index"] for r in results]
