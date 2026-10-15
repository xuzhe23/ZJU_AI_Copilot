# -*- coding: utf-8 -*-
"""定时调度与日常采集：把“routine 自动化”落到实处（零依赖，可手动触发，APScheduler 可选升级）。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.models import Record
from parsers.doc_parser import SUPPORTED_SUFFIXES, parse_file
from collectors.file_watcher import scan_existing
from collectors.web_fetcher import fetch_text, strip_html


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def collect(settings, ocr=None, web_urls=None) -> list:
    """执行一次日常采集：扫描 ingest 目录文件 + 抓取网页，返回统一 Record 列表。"""
    records: list = []
    for p in scan_existing(settings.ingest_dir, SUPPORTED_SUFFIXES):
        text = parse_file(p, ocr=ocr)
        if text.strip():
            records.append(Record(source=p.name, ts=_now_iso(), text=text, raw_path=str(p)))
    for url in (web_urls or []):
        try:
            html = fetch_text(url)
            records.append(Record(source=url, ts=_now_iso(), text=strip_html(html)))
        except Exception as e:  # noqa: BLE001
            records.append(Record(source=url, ts=_now_iso(), text=f"[抓取失败] {e}"))
    return records


def save_records(settings, records: list) -> Path:
    """把采集记录追加写入 data/logs/YYYY-MM-DD.jsonl。"""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    path = settings.logs_dir / f"{datetime.now():%Y-%m-%d}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_line(), ensure_ascii=False) + "\n")
    return path


def load_today_records(settings) -> list:
    path = settings.logs_dir / f"{datetime.now():%Y-%m-%d}.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        records.append(Record(
            source=d.get("source", ""), ts=d.get("ts", ""), text=d.get("text", ""),
            raw_path=d.get("raw_path", ""), meta=d.get("meta", {}),
        ))
    return records


def run_once(settings, ocr=None, web_urls=None) -> list:
    """手动演示入口：采集一次并落盘。"""
    records = collect(settings, ocr=ocr, web_urls=web_urls)
    save_records(settings, records)
    return records
