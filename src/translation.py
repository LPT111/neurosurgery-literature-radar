from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_PATH = BASE_DIR / "output/translation_cache.json"


TERM_MAP = {
    "traumatic brain injury": "创伤性脑损伤",
    "brain injury": "脑损伤",
    "hydrocephalus": "脑积水",
    "normal pressure hydrocephalus": "正常压力脑积水",
    "microglia": "小胶质细胞",
    "microglial": "小胶质细胞",
    "neuroinflammation": "神经炎症",
    "extracellular vesicles": "细胞外囊泡",
    "exosomes": "外泌体",
    "exosome": "外泌体",
    "stem cell": "干细胞",
    "mesenchymal stem cell": "间充质干细胞",
    "glioblastoma": "胶质母细胞瘤",
    "glioma": "胶质瘤",
    "spinal cord tumor": "脊髓肿瘤",
    "Cystatin C": "Cystatin C",
    "TREM2": "TREM2",
    "ferroptosis": "铁死亡",
    "inflammation": "炎症",
    "clinical trial": "临床试验",
    "randomized": "随机",
    "double-blind": "双盲",
    "placebo-controlled": "安慰剂对照",
    "systematic review": "系统综述",
    "meta-analysis": "荟萃分析",
    "positron emission tomography": "正电子发射断层显像",
    "PET tracers": "PET 示踪剂",
}


def _load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _looks_english(text: str) -> bool:
    letters = len(re.findall(r"[A-Za-z]", text or ""))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text or ""))
    return letters > max(8, cjk * 2)


def _term_fallback(text: str, prefix: str = "术语辅助翻译") -> str:
    compact = re.sub(r"\s+", " ", (text or "")).strip()
    if not compact:
        return ""
    hits = []
    lower = compact.lower()
    for en, cn in TERM_MAP.items():
        if en.lower() in lower and cn not in hits:
            hits.append(cn)
    if not hits:
        return f"{prefix}：{compact}"
    return f"{prefix}：该内容涉及{ '、'.join(hits[:8]) }。原文：{compact}"


def translate_text(text: str, *, max_chars: int = 2800, fallback_prefix: str = "术语辅助翻译") -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return ""
    if not _looks_english(text):
        return text

    source = text[:max_chars]
    cache_key = f"zh-CN::{source}"
    cache = _load_cache()
    if cache_key in cache:
        return cache[cache_key]

    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=en&tl=zh-CN&dt=t&q={quote(source)}"
        )
        response = requests.get(url, timeout=18, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data: Any = response.json()
        translated = "".join(part[0] for part in data[0] if part and part[0]).strip()
        if translated:
            if len(text) > max_chars:
                translated += "……"
            cache[cache_key] = translated
            _save_cache(cache)
            return translated
    except Exception as exc:
        print(f"Translation fallback: {exc}")

    translated = _term_fallback(source, prefix=fallback_prefix)
    cache[cache_key] = translated
    _save_cache(cache)
    return translated


def translate_item_fields(item: dict[str, Any]) -> dict[str, str]:
    title = item.get("title", "")
    abstract = item.get("abstract", "")
    return {
        "title_cn": item.get("title_cn") or translate_text(title, max_chars=500, fallback_prefix="论文标题"),
        "abstract_cn": item.get("abstract_cn") or translate_text(abstract, max_chars=2200, fallback_prefix="摘要要点"),
    }
