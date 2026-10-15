# -*- coding: utf-8 -*-
"""本地兜底 LLM：无任何平台 API 时，用模板 + 检索片段生成答案/摘要，保证离线可演示。"""
from __future__ import annotations

import re

from core.provider_base import LLMProvider


class LocalFallback(LLMProvider):
    name = "local-fallback"

    def chat(self, messages: list, **kwargs) -> str:
        # 取最后一条 user 消息作为主输入
        user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_text = m.get("content", "")
                break

        question = ""
        context = ""
        # 行首锚定，避免把正文里的“遇到的问题：…”误当成问答标记
        mq = re.search(r"^\s*问题[:：]\s*(.*)", user_text, re.M)
        if mq:
            question = mq.group(1).strip()
        mc = re.search(r"^\s*参考知识片段[:：]\s*(.*)", user_text, re.S | re.M)
        if mc:
            context = mc.group(1).strip()

        if context:
            # 按 "[N] 来源：" 切分，取前 3 条作为候选答案
            parts = [p.strip() for p in re.split(r"\n(?=\[\d+\]\s*来源[:：])", context) if p.strip()]
            top = parts[:3]
            body = "\n".join(f"  • {p[:240]}" for p in top)
            return (
                "【离线模式 · 基于本地知识库检索】\n"
                f"根据你的问题“{question or '（未识别）'}”，在知识库中找到以下相关内容：\n\n{body}\n\n"
                "如需更自然的大模型解答，请在 .env 中配置平台 API Key 并把 OFFLINE_MODE 改为 false。"
            )
        if question:
            return (
                f"【离线模式】收到问题：“{question}”。当前知识库为空或未命中，"
                "请先运行 `python main.py ingest` 导入资料。"
            )
        return "【离线模式】请告诉我你的问题。"

    def summarize(self, text: str, max_len: int = 500) -> str:
        """抽取式摘要：取文本开头若干关键句。"""
        sents = [s.strip() for s in re.split(r"[。！？\n]", text) if s.strip()]
        out, cur = [], 0
        for s in sents:
            if cur + len(s) > max_len:
                break
            out.append(s)
            cur += len(s)
        return "。".join(out) + ("。" if out else "")
