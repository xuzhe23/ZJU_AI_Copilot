# -*- coding: utf-8 -*-
"""
配置中心：读取 .env（零依赖手写解析），集中管理所有平台 Key、模型名、路径与离线开关。

所有平台相关参数集中在这里，替换模型名 / 端点只需改 .env，不用动业务代码。
"""
from __future__ import annotations

import os
from pathlib import Path

# 项目根目录（本文件所在目录的上一级）
ROOT_DIR = Path(__file__).resolve().parent.parent


def _parse_dotenv(env_path: Path) -> dict:
    """极简 .env 解析：支持 KEY=VALUE、# 注释、空行；不依赖 python-dotenv。"""
    values: dict = {}
    if not env_path.exists():
        return values
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        values[key] = val
    return values


def _to_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """从环境变量 + .env 读取全部配置，提供类型化访问。"""

    def __init__(self, env_path: str | Path | None = None):
        self.env_path = Path(env_path) if env_path else ROOT_DIR / ".env"
        self._env = _parse_dotenv(self.env_path)

    def get(self, key: str, default: str = "") -> str:
        """优先读系统环境变量，其次 .env，最后 default。"""
        return os.environ.get(key) or self._env.get(key, default)

    # ---- 关键开关 ----
    @property
    def offline_mode(self) -> bool:
        """true=纯本地兜底可跑（零平台依赖）；false=启用平台 API。"""
        return _to_bool(self.get("OFFLINE_MODE", "true"))

    @property
    def use_embedding(self) -> bool:
        """是否启用向量检索（需 DASHSCOPE_API_KEY 且非离线）。"""
        return (not self.offline_mode) and _to_bool(self.get("USE_EMBEDDING", "false")) and bool(self.qwen_api_key)

    # ---- 数据处理 / 对话输出：千问办公 → DashScope(Qwen) ----
    @property
    def qwen_api_key(self) -> str | None:
        k = self.get("DASHSCOPE_API_KEY", "").strip()
        return k or None

    @property
    def qwen_base_url(self) -> str:
        return self.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    @property
    def qwen_model(self) -> str:
        return self.get("QWEN_MODEL", "qwen-plus")

    @property
    def qwen_embed_model(self) -> str:
        return self.get("QWEN_EMBED_MODEL", "text-embedding-v3")

    @property
    def qwen_rerank_model(self) -> str:
        return self.get("QWEN_RERANK_MODEL", "qwen3-rerank")

    # ---- 数据来源：浙大教育智能体平台 / 浙大先生 ----
    @property
    def zju_api_key(self) -> str | None:
        k = self.get("ZJU_API_KEY", "").strip()
        return k or None

    @property
    def zju_base_url(self) -> str:
        return self.get("ZJU_BASE_URL", "https://aihub.zju.edu.cn/v1")

    @property
    def zju_model(self) -> str:
        return self.get("ZJU_MODEL", "qwen-plus")

    # ---- Qoder（可选：仅作写代码辅助 Agent，非对话后端）----
    @property
    def qoder_pat(self) -> str | None:
        k = self.get("QODER_PERSONAL_ACCESS_TOKEN", "").strip()
        return k or None

    # ---- 本地路径 ----
    @property
    def data_dir(self) -> Path:
        return (ROOT_DIR / self.get("DATA_DIR", "data")).resolve()

    @property
    def ingest_dir(self) -> Path:
        return (ROOT_DIR / self.get("INGEST_DIR", "data/ingest")).resolve()

    @property
    def logs_dir(self) -> Path:
        return (ROOT_DIR / self.get("LOGS_DIR", "data/logs")).resolve()

    @property
    def kb_dir(self) -> Path:
        return (ROOT_DIR / self.get("KB_DIR", "data/kb")).resolve()

    @property
    def output_dir(self) -> Path:
        return (ROOT_DIR / self.get("OUTPUT_DIR", "data/outputs")).resolve()

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.ingest_dir, self.logs_dir, self.kb_dir, self.output_dir):
            d.mkdir(parents=True, exist_ok=True)
