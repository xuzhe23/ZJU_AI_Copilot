# -*- coding: utf-8 -*-
"""日报生成：把当日采集记录汇总成 Markdown（可选 Excel）。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.models import Record, Report


def build_report(records: list, llm=None, date: str | None = None) -> Report:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    groups: dict = {}
    for r in records:
        groups.setdefault(r.source, []).append(r.text)

    sections = [{"title": src, "items": items} for src, items in groups.items()]
    report = Report(date=date, sections=sections, body=_render(date, sections, ""))

    # 可选：用 LLM 写一段摘要；离线用抽取式摘要，失败静默降级为无摘要
    if llm is not None and sections:
        content = "\n\n".join(
            f"{s['title']}:\n" + "\n".join(f"- {t[:200]}" for t in s["items"])
            for s in sections
        )
        if getattr(llm, "name", "") == "local-fallback":
            report.summary = llm.summarize(content)
        else:
            try:
                summary = llm.chat([
                    {"role": "system", "content": "你是科研日报摘要助手，请用 3 句话概括今天的科研日常，突出进展与异常。"},
                    {"role": "user", "content": content[:4000]},
                ])
                report.summary = summary.strip()
            except Exception as e:  # noqa: BLE001
                report.summary = f"（摘要生成失败：{e}）"
        report.body = _render(date, sections, report.summary)

    return report


def _render(date: str, sections: list, summary: str) -> str:
    lines = [f"# 科研日报 · {date}", ""]
    if summary:
        lines += [f"> 摘要：{summary}", ""]
    if not sections:
        lines += ["（今日暂无采集记录，请先运行 `python main.py collect`）"]
    for s in sections:
        lines += [f"## {s['title']}", ""]
        for it in s["items"]:
            lines.append(f"- {it.strip()[:500]}")
        lines.append("")
    return "\n".join(lines)


def to_markdown(report: Report) -> str:
    return report.body


def save_report(settings, report: Report, md: str | None = None) -> Path:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    md = md or to_markdown(report)
    out = settings.output_dir / f"report-{report.date}.md"
    out.write_text(md, encoding="utf-8")
    return out
