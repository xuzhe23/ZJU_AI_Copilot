# -*- coding: utf-8 -*-
"""图片 OCR：RapidOCR(onnxruntime) 引擎，复用 PaddleOCR 中文模型，轻量自包含。"""
from __future__ import annotations

from core.provider_base import OCREngine


class RapidOCREngine(OCREngine):
    name = "rapidocr"

    def __init__(self):
        self._engine = None
        self._error = ""
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()
        except Exception as e:  # noqa: BLE001
            self._error = str(e)

    def available(self) -> bool:
        return self._engine is not None

    def recognize(self, image_path: str) -> str:
        if self._engine is None:
            raise RuntimeError(
                f"RapidOCR 未就绪：{self._error}（请 pip install rapidocr-onnxruntime）"
            )
        result, _ = self._engine(str(image_path))
        if not result:
            return ""
        lines = [text for _, text, _ in result if text and text.strip()]
        return "\n".join(lines)
