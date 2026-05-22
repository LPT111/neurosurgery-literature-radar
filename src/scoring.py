from __future__ import annotations

import re
from typing import Any


HIGH_PRIORITY_TERMS = [
    "traumatic brain injury",
    "hydrocephalus",
    "normal pressure hydrocephalus",
    "extracellular vesicles",
    "exosome",
    "microglia",
    "TREM2",
    "Cystatin C",
    "CST3",
    "neuroinflammation",
    "stem cell",
    "intranasal",
    "glioblastoma",
    "spinal cord tumor",
]


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        doi = (item.get("doi") or "").strip().lower()
        pmid = (item.get("pmid") or "").strip()
        title_key = normalize_title(item.get("title", ""))
        key = f"doi:{doi}" if doi else f"pmid:{pmid}" if pmid else f"title:{title_key}"
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def score_item(item: dict[str, Any], priority_journals: list[str]) -> int:
    text = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
    score = 0
    for term in HIGH_PRIORITY_TERMS:
        if term.lower() in text:
            score += 10
    topic = item.get("topic", "")
    if topic in {"traumatic_brain_injury", "hydrocephalus", "stem_cell_exosome", "microglia_trem2"}:
        score += 8
    journal = (item.get("journal") or "").lower()
    if any(j.lower() == journal or j.lower() in journal for j in priority_journals):
        score += 20
    if item.get("abstract"):
        score += 8
    if item.get("doi"):
        score += 4
    if item.get("pmid"):
        score += 4
    if item.get("source") in {"PubMed"}:
        score += 5
    if item.get("source") in {"biorxiv", "medrxiv"}:
        score += 2
    if re.search(r"clinical|trial|patient|cohort|therapy|treatment|mechanism|single-cell|spatial|omics", text):
        score += 6
    return score


def rank_items(items: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    priority_journals = config.get("priority_journals", [])
    deduped = dedupe_items(items)
    for item in deduped:
        item["score"] = score_item(item, priority_journals)
    return sorted(deduped, key=lambda x: (x.get("score", 0), x.get("published", "")), reverse=True)
