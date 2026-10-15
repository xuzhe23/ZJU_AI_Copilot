# -*- coding: utf-8 -*-
"""可选 Gradio 网页版：把问答与日报做成可交互 Demo（未装 gradio 不影响 CLI）。"""
from __future__ import annotations


def build_demo(indexer, llm, settings):
    try:
        import gradio as gr
    except ImportError as e:
        raise ImportError("需要安装 gradio：pip install gradio") from e

    from qa.answerer import answer

    def ask_fn(q):
        return answer(q, indexer, llm, top_k=5)

    with gr.Blocks(title="求是·研伴") as demo:
        gr.Markdown("# 求是·研伴 ZJU ResearchMate")
        with gr.Tab("知识库问答"):
            q = gr.Textbox(label="问题", placeholder="例如：实验室GPU环境怎么配置？")
            btn = gr.Button("提问")
            out = gr.Markdown()
            btn.click(ask_fn, inputs=q, outputs=out)
        with gr.Tab("日报"):
            gr.Markdown("在命令行运行 `python main.py report` 生成日报，输出到 data/outputs/。")
    return demo
