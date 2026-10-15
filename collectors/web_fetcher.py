# -*- coding: utf-8 -*-
"""网页/接口采集：抓取文献更新、教务通知、GPU 任务状态页等（requests，超时+重试）。"""
from __future__ import annotations

import re
import time

import requests

UA = "Mozilla/5.0 ZJU-ResearchMate/1.0"


def fetch_text(url: str, timeout: int = 10, retries: int = 2) -> str:
    last = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retries:
                time.sleep(1 + i)
    raise last


def strip_html(html: str) -> str:
    """把 HTML 粗略转成纯文本（演示用，足够抓状态页/通知页）。"""
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
