# -*- coding: utf-8 -*-
"""目录监控：监听 ingest 目录新增文件。零依赖实现，可手动扫描或循环监听。"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable


def scan_existing(ingest_dir: Path, suffixes=None) -> list:
    """扫描目录下所有受支持的文件，按文件名排序返回。"""
    d = Path(ingest_dir)
    if not d.exists():
        return []
    out = []
    for p in d.iterdir():
        if p.is_file() and (suffixes is None or p.suffix.lower() in suffixes):
            out.append(p)
    return sorted(out, key=lambda x: x.name)


def watch(ingest_dir: Path, on_new: Callable[[Path], None],
          interval: float = 5.0, once: bool = False):
    """循环监听新增文件；once=True 时只扫一轮后返回。"""
    seen = set()
    while True:
        for p in scan_existing(ingest_dir):
            key = (p.name, p.stat().st_mtime_ns)
            if key not in seen:
                seen.add(key)
                on_new(p)
        if once:
            return
        time.sleep(interval)
