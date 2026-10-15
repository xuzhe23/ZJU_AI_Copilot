# -*- coding: utf-8 -*-
"""可插拔 Provider 抽象接口：平台与本地兜底实现同一套签名，运行时按配置选择。"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str = "llm"

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """给定 OpenAI 风格 messages，返回文本回答。"""


class EmbeddingProvider(ABC):
    name: str = "embedding"

    @abstractmethod
    def embed(self, texts: list) -> list:
        """批量向量化，返回与输入等长的浮点向量列表。"""


class RerankProvider(ABC):
    name: str = "rerank"

    @abstractmethod
    def rerank(self, query: str, docs: list, top_n: int = 5) -> list:
        """对 docs 按与 query 的相关度重排，返回原索引列表（截断到 top_n）。"""


class OCREngine(ABC):
    name: str = "ocr"

    @abstractmethod
    def recognize(self, image_path: str) -> str:
        """识别图片中的文字并返回文本。"""
