# -*- coding: utf-8 -*-
"""
「求是·研伴」ZJU ResearchMate —— 命令行入口
    科研日常 routine 自动化 + 经验知识库问答 + 训练数据一键整理

用法：
    python main.py ingest                      # 导入 data/ingest 下的文档/图片 → 建立知识库
    python main.py collect                     # 执行一次日常采集（扫描新增文件 + 可选网页）
    python main.py report                      # 生成今日科研日报（Markdown）
    python main.py ask "实验室GPU环境怎么配"    # 知识库问答（带引用来源）
    python main.py feed                        # 一键导出脱敏后的训练集 JSONL
    python main.py ocr path/to/image.jpg       # 识别图片文字
    python main.py demo                        # 一键离线演示（上述流程串起来）
    python main.py serve                       # （可选）Gradio 网页版
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import Settings
from core.models import Chunk, QAItem
from llm.local_fallback import LocalFallback
from llm.openai_compat import OpenAICompatProvider
from llm.qwen_provider import QwenEmbeddingProvider, QwenRerankProvider
from ocr.ocr_engine import RapidOCREngine
from parsers.doc_parser import SUPPORTED_SUFFIXES, chunk_text, parse_file
from knowledge.indexer import Indexer
from knowledge.store import KBStore
from qa.answerer import answer
from report.reporter import build_report, save_report, to_markdown
from collectors.scheduler import collect, load_today_records, save_records
from datasets.feed_builder import anonymize, build_qa_pairs, export_jsonl


# ---------------- 依赖装配 ----------------
def build_llm(settings: Settings):
    """按配置选择对话模型：离线兜底 → 千问(数据处理/对话) → 浙大平台(数据来源)。"""
    if settings.offline_mode:
        return LocalFallback()
    if settings.qwen_api_key:
        return OpenAICompatProvider(settings.qwen_base_url, settings.qwen_api_key,
                                    settings.qwen_model, name="qwen")
    if settings.zju_api_key:
        return OpenAICompatProvider(settings.zju_base_url, settings.zju_api_key,
                                    settings.zju_model, name="zju")
    return LocalFallback()


def build_embedder(settings: Settings):
    if not settings.use_embedding:
        return None
    try:
        return QwenEmbeddingProvider(settings.qwen_api_key, settings.qwen_embed_model)
    except Exception:  # noqa: BLE001
        return None


def build_reranker(settings: Settings):
    if settings.offline_mode or not settings.qwen_api_key:
        return None
    try:
        return QwenRerankProvider(settings.qwen_api_key, settings.qwen_rerank_model)
    except Exception:  # noqa: BLE001
        return None


def build_ocr():
    return RapidOCREngine()


def load_indexer(settings: Settings, embedder=None) -> Indexer:
    chunks = KBStore(settings.kb_dir).load()
    return Indexer(chunks=chunks, use_embedding=embedder is not None, embedder=embedder)


# ---------------- 子命令 ----------------
def cmd_ingest(settings, args) -> int:
    settings.ensure_dirs()
    ocr = build_ocr()
    embedder = build_embedder(settings)
    idx = Indexer(use_embedding=embedder is not None, embedder=embedder)

    paths = [p for p in sorted(settings.ingest_dir.iterdir())
             if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES]
    if not paths:
        print(f"[ingest] 未在 {settings.ingest_dir} 找到可导入的文件。")
        return 1

    for p in paths:
        print(f"[ingest] 解析 {p.name} ...")
        text = parse_file(p, ocr=ocr)
        if not text.strip():
            print("  -> 跳过（空内容或解析失败）")
            continue
        for i, c in enumerate(chunk_text(text)):
            idx.add_chunks([Chunk(id=f"{p.name}#{i}", text=c, source=p.name)])

    idx.build()
    KBStore(settings.kb_dir).save(idx.chunks)
    print(f"[ingest] 完成：{len(idx.chunks)} 个知识分块已入库 → {settings.kb_dir}")
    return 0


def cmd_collect(settings, args) -> int:
    settings.ensure_dirs()
    ocr = build_ocr()
    urls = getattr(args, "urls", []) or []
    records = collect(settings, ocr=ocr, web_urls=urls)
    save_records(settings, records)
    for r in records:
        print(f"[collect] {r.source}: {len(r.text)} 字")
    print(f"[collect] 已写入 {len(records)} 条记录")
    return 0


def cmd_report(settings, args) -> int:
    settings.ensure_dirs()
    records = load_today_records(settings)
    if not records:
        print("[report] 今日暂无采集记录，改为直接扫描 ingest 目录生成。")
        records = collect(settings, ocr=build_ocr())
    llm = build_llm(settings)
    report = build_report(records, llm=llm)
    out = save_report(settings, report)
    print(to_markdown(report))
    print(f"\n[report] 已保存 → {out}")
    return 0


def cmd_ask(settings, args) -> int:
    settings.ensure_dirs()
    llm = build_llm(settings)
    reranker = build_reranker(settings)
    idx = load_indexer(settings)
    if not idx.chunks:
        print("[ask] 知识库为空，请先运行 `python main.py ingest`。")
        return 1
    print(answer(args.question, idx, llm, reranker=reranker, top_k=args.top_k))
    return 0


def cmd_feed(settings, args) -> int:
    settings.ensure_dirs()
    llm = build_llm(settings)
    idx = load_indexer(settings)
    if not idx.chunks:
        print("[feed] 知识库为空，请先运行 `python main.py ingest`。")
        return 1
    items = build_qa_pairs(idx, llm, n=args.n)
    items = [QAItem(anonymize(it.instruction), anonymize(it.input),
                    anonymize(it.output), it.source) for it in items]
    out = settings.output_dir / "train.jsonl"
    export_jsonl(items, out)
    print(f"[feed] 已导出 {len(items)} 条脱敏问答对 → {out}")
    return 0


def cmd_ocr(settings, args) -> int:
    ocr = build_ocr()
    print(ocr.recognize(args.image))
    return 0


def cmd_demo(settings, args) -> int:
    print("=" * 60)
    print("「求是·研伴」ZJU ResearchMate  ·  一键离线演示")
    print("=" * 60)
    steps = [
        ("1. 建立知识库", lambda: cmd_ingest(settings, args)),
        ("2. 日常采集", lambda: cmd_collect(settings, args)),
        ("3. 生成日报", lambda: cmd_report(settings, args)),
        ("4. 知识库问答", lambda: cmd_ask(settings, argparse.Namespace(question="实验室GPU环境怎么配置", top_k=3))),
        ("5. 导出训练集", lambda: cmd_feed(settings, args)),
    ]
    for title, fn in steps:
        print("\n" + "#" * 60)
        print(f"## {title}")
        print("#" * 60)
        fn()
    return 0


def cmd_serve(settings, args) -> int:
    try:
        from web.app import build_demo
    except ImportError as e:
        print(f"[serve] 需要安装 gradio：{e}")
        return 1
    llm = build_llm(settings)
    idx = load_indexer(settings)
    build_demo(idx, llm, settings).launch()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="求是·研伴 ZJU ResearchMate")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest", help="导入 data/ingest 建立知识库")

    pc = sub.add_parser("collect", help="执行一次日常采集")
    pc.add_argument("--url", dest="urls", action="append", default=[], help="额外抓取的网页URL（可多次）")

    sub.add_parser("report", help="生成今日日报")

    pa = sub.add_parser("ask", help="知识库问答")
    pa.add_argument("question", help="要问的问题")
    pa.add_argument("--top-k", dest="top_k", type=int, default=5)

    pf = sub.add_parser("feed", help="导出脱敏训练集 JSONL")
    pf.add_argument("--n", type=int, default=0, help="最多生成多少条（0=全部）")

    po = sub.add_parser("ocr", help="识别图片文字")
    po.add_argument("image", help="图片路径")

    pd = sub.add_parser("demo", help="一键离线演示")
    pd.add_argument("--n", type=int, default=0)

    sub.add_parser("serve", help="启动 Gradio 网页（可选）")

    args = p.parse_args(argv)
    settings = Settings()
    settings.ensure_dirs()

    handlers = {
        "ingest": cmd_ingest, "collect": cmd_collect, "report": cmd_report,
        "ask": cmd_ask, "feed": cmd_feed, "ocr": cmd_ocr,
        "demo": cmd_demo, "serve": cmd_serve,
    }
    return handlers[args.cmd](settings, args)


if __name__ == "__main__":
    raise SystemExit(main())
