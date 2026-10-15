# -*- coding: utf-8 -*-
"""知识库问答主流程：检索 → 组装上下文 → 生成带引用答案。"""
from __future__ import annotations

from retrieval.retriever import retrieve

SYSTEM_PROMPT = (
    "你是浙江大学科研助手「求是·研伴」。请严格依据用户提供的“参考知识片段”回答；"
    "若片段信息不足，请明确说明，并可给出通用建议。回答简洁、分点，并标注引用的片段编号。"
)


def answer(question: str, indexer, llm, reranker=None, top_k: int = 5) -> str:
    chunks = retrieve(question, indexer, top_k=top_k, reranker=reranker)
    if not chunks:
        return "知识库中没有检索到相关内容，请先运行 `python main.py ingest` 导入资料，或换个问法。"

    context = "\n\n".join(f"[{i + 1}] 来源：{c.source}\n{c.text}" for i, c in enumerate(chunks))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"问题：{question}\n\n参考知识片段：\n{context}"},
    ]
    try:
        reply = llm.chat(messages)
    except Exception as e:  # noqa: BLE001
        reply = f"（大模型调用失败：{e}；以下为检索到的原文片段。）"

    citations = "\n".join(f"[{i + 1}] {c.source}" for i, c in enumerate(chunks))
    return f"{reply}\n\n────────────\n引用来源：\n{citations}"
