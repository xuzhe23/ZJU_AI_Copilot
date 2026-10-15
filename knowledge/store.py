# -*- coding: utf-8 -*-
"""知识库持久化：JSON 本地存储（零依赖），落盘到 data/kb。"""
from __future__ import annotations

import json
from pathlib import Path

from core.models import Chunk


class KBStore:
    def __init__(self, kb_dir: Path):
        self.dir = Path(kb_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.dir / "index.json"

    def save(self, chunks: list) -> None:
        data = [
            {"id": c.id, "text": c.text, "source": c.source, "meta": c.meta}
            for c in chunks
        ]
        self.index_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load(self) -> list:
        if not self.index_file.exists():
            return []
        data = json.loads(self.index_file.read_text(encoding="utf-8"))
        return [
            Chunk(id=d.get("id", ""), text=d.get("text", ""),
                  source=d.get("source", ""), meta=d.get("meta", {}))
            for d in data
        ]
