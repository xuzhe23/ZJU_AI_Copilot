# -*- coding: utf-8 -*-
"""数据模型：数据流中流转的四种核心对象。"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Record:
    """采集 / OCR 产出的原始记录。"""
    source: str                      # 来源：文件名 / URL / 设备名
    ts: str                          # ISO 时间戳
    text: str                        # 正文
    raw_path: str = ""               # 原始文件路径
    meta: dict = field(default_factory=dict)

    def to_line(self) -> dict:
        return asdict(self)


@dataclass
class Chunk:
    """分块后的知识单元。"""
    id: str
    text: str
    source: str
    meta: dict = field(default_factory=dict)


@dataclass
class QAItem:
    """训练用问答对（instruction/input/output 标准格式）。"""
    instruction: str
    input: str
    output: str
    source: str = ""


@dataclass
class Report:
    """日报。"""
    date: str
    sections: list = field(default_factory=list)   # [{"title":..., "items":[...]}]
    body: str = ""
    summary: str = ""
