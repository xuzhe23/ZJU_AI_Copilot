# -*- coding: utf-8 -*-
"""知识库索引：本地 TF-IDF + 字符 n-gram（零第三方依赖，保证离线可跑），可选向量升级。"""
from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[一-鿿]")


def tokenize(text: str) -> list:
    """中文按单字、英文按单词切分，对科研术语/报错信息足够友好。"""
    return TOKEN_RE.findall(text.lower())


class Indexer:
    def __init__(self, chunks=None, use_embedding: bool = False, embedder=None):
        self.chunks = list(chunks) if chunks else []
        self.use_embedding = use_embedding
        self.embedder = embedder
        self._df = Counter()      # 文档频率
        self._tfidf = []          # 每个 chunk 的归一化 TF-IDF 向量
        self._vectors = []        # 可选 embedding 向量
        if self.chunks:
            self.build()

    def add_chunks(self, chunks) -> None:
        self.chunks.extend(chunks)

    def build(self) -> None:
        self._df = Counter()
        for c in self.chunks:
            for tok in set(tokenize(c.text)):
                self._df[tok] += 1

        n_docs = max(len(self.chunks), 1)
        self._tfidf = []
        for c in self.chunks:
            tf = Counter(tokenize(c.text))
            vec = {}
            for tok, cnt in tf.items():
                idf = math.log((1 + n_docs) / (1 + self._df[tok])) + 1.0
                vec[tok] = cnt * idf
            norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
            self._tfidf.append({k: v / norm for k, v in vec.items()})

        if self.use_embedding and self.embedder is not None:
            self._vectors = self.embedder.embed([c.text for c in self.chunks])

    def search(self, query: str, top_k: int = 5) -> list:
        if not self.chunks:
            return []
        if self.use_embedding and self._vectors:
            return self._search_embedding(query, top_k)
        return self._search_tfidf(query, top_k)

    def _search_tfidf(self, query: str, top_k: int) -> list:
        n_docs = max(len(self.chunks), 1)
        tf = Counter(tokenize(query))
        qvec = {}
        for tok, cnt in tf.items():
            if self._df.get(tok):
                idf = math.log((1 + n_docs) / (1 + self._df[tok])) + 1.0
                qvec[tok] = cnt * idf
        qnorm = math.sqrt(sum(w * w for w in qvec.values())) or 1.0
        qvec = {k: v / qnorm for k, v in qvec.items()}

        scored = []
        for i, dvec in enumerate(self._tfidf):
            dot = sum(qvec[t] * dvec.get(t, 0.0) for t in qvec)
            scored.append((dot, self.chunks[i]))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:top_k]]

    def _search_embedding(self, query: str, top_k: int) -> list:
        qv = self.embedder.embed([query])[0]
        scored = []
        for i, dv in enumerate(self._vectors):
            dot = sum(a * b for a, b in zip(qv, dv))
            scored.append((dot, self.chunks[i]))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:top_k]]
