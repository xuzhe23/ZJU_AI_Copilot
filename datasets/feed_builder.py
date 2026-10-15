# -*- coding: utf-8 -*-
"""训练集导出：从知识库自动生成问答对，脱敏后导出标准 JSONL（instruction/input/output）。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from core.models import QAItem


def build_qa_pairs(indexer, llm=None, n: int = 0) -> list:
    """为每个知识分块生成一条问答对：在线用 LLM 出题，离线用模板。"""
    chunks = indexer.chunks if n <= 0 else indexer.chunks[:n]
    items: list = []
    for c in chunks:
        question = f"请介绍「{c.source}」中的这段内容。"
        if llm is not None and not getattr(llm, "name", "").startswith("local-fallback"):
            try:
                question = llm.chat([
                    {"role": "system", "content": "请针对下面这段知识，生成一个自然的问题（只输出问题本身）。"},
                    {"role": "user", "content": c.text[:800]},
                ]).strip()
            except Exception:  # noqa: BLE001
                pass
        items.append(QAItem(
            instruction="你是浙大科研助手，请依据知识库回答用户问题。",
            input=question, output=c.text.strip(), source=c.source,
        ))
    return items


def anonymize(text: str) -> str:
    """脱敏：手机号/身份证/邮箱/IP/常见学号格式替换为占位符。"""
    text = re.sub(r"1[3-9]\d{9}", "<手机号>", text)
    text = re.sub(r"\b\d{17}[\dXx]\b", "<身份证号>", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<邮箱>", text)
    text = re.sub(r"\d{1,3}(?:\.\d{1,3}){3}", "<IP>", text)
    text = re.sub(r"\b(31\d{7}|2\d{9}|1\d{9})\b", "<学号>", text)
    return text


def export_jsonl(items: list, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps({
                "instruction": it.instruction,
                "input": it.input,
                "output": it.output,
                "source": it.source,
            }, ensure_ascii=False) + "\n")
