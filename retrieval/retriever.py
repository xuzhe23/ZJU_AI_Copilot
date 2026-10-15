# -*- coding: utf-8 -*-
"""检索主流程：本地 TF-IDF/字符 n-gram 检索 + 可选重排。"""
from __future__ import annotations


def retrieve(query: str, indexer, top_k: int = 5, reranker=None) -> list:
    """返回与 query 最相关的 top_k 个 Chunk；reranker 可选，失败时静默降级。"""
    candidates = indexer.search(query, top_k=max(top_k * 2, top_k))
    if not candidates:
        return []
    if reranker is not None:
        try:
            order = reranker.rerank(query, [c.text for c in candidates], top_n=top_k)
            ranked = [candidates[i] for i in order if 0 <= i < len(candidates)]
            return ranked[:top_k]
        except Exception:  # noqa: BLE001
            pass
    return candidates[:top_k]
