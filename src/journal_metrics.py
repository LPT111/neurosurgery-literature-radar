from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


# Approximate reference metrics for display and triage only. Impact factors and
# JCR/CAS quartiles change yearly; verify against the latest Journal Citation
# Reports or CAS list before formal writing, submission, or grant use.
JOURNAL_METRICS: dict[str, dict[str, Any]] = {
    "nature": {"impact_factor": "50+", "quartile": "JCR Q1 / CAS 1区"},
    "science": {"impact_factor": "40+", "quartile": "JCR Q1 / CAS 1区"},
    "cell": {"impact_factor": "40+", "quartile": "JCR Q1 / CAS 1区"},
    "nature medicine": {"impact_factor": "50+", "quartile": "JCR Q1 / CAS 1区"},
    "nature neuroscience": {"impact_factor": "20+", "quartile": "JCR Q1 / CAS 1区"},
    "neuron": {"impact_factor": "15+", "quartile": "JCR Q1 / CAS 1区"},
    "brain": {"impact_factor": "10+", "quartile": "JCR Q1 / CAS 1区"},
    "the lancet neurology": {"impact_factor": "40+", "quartile": "JCR Q1 / CAS 1区"},
    "jama neurology": {"impact_factor": "20+", "quartile": "JCR Q1 / CAS 1区"},
    "science translational medicine": {"impact_factor": "15+", "quartile": "JCR Q1 / CAS 1区"},
    "acta neuropathologica": {"impact_factor": "10+", "quartile": "JCR Q1 / CAS 1区"},
    "journal of neuroinflammation": {"impact_factor": "5+", "quartile": "JCR Q1/Q2"},
    "journal of nanobiotechnology": {"impact_factor": "10+", "quartile": "JCR Q1 / CAS 1区"},
    "stem cell research & therapy": {"impact_factor": "5+", "quartile": "JCR Q1/Q2"},
    "new england journal of medicine": {"impact_factor": "100+", "quartile": "JCR Q1 / CAS 1区"},
    "the lancet": {"impact_factor": "90+", "quartile": "JCR Q1 / CAS 1区"},
    "jama": {"impact_factor": "50+", "quartile": "JCR Q1 / CAS 1区"},
    "bmj": {"impact_factor": "90+", "quartile": "JCR Q1"},
    "annals of neurology": {"impact_factor": "10+", "quartile": "JCR Q1 / CAS 1区"},
    "neurology": {"impact_factor": "8+", "quartile": "JCR Q1/Q2"},
}


BASE_DIR = Path(__file__).resolve().parents[1]
_EXTERNAL_METRICS_CACHE: dict[str, dict[str, str]] | None = None


def normalize_journal_name(journal: str) -> str:
    return "".join(ch for ch in (journal or "").strip().lower() if ch.isalnum())


def journal_alias_keys(journal: str) -> list[str]:
    raw = (journal or "").strip()
    keys = [normalize_journal_name(raw)]
    for sep in [":", "("]:
        if sep in raw:
            keys.append(normalize_journal_name(raw.split(sep, 1)[0]))
    lowered = raw.lower()
    if lowered.startswith("the "):
        keys.append(normalize_journal_name(raw[4:]))
    else:
        keys.append(normalize_journal_name(f"the {raw}"))
    return [key for idx, key in enumerate(keys) if key and key not in keys[:idx]]


def load_external_metrics() -> dict[str, dict[str, str]]:
    """Load optional precise journal metrics from config/journal_metrics.csv.

    Expected columns:
    journal,impact_factor,quartile

    Optional columns are allowed and ignored. This lets the project use a
    user-provided JCR/CAS export without scraping licensed databases.
    """
    global _EXTERNAL_METRICS_CACHE
    if _EXTERNAL_METRICS_CACHE is not None:
        return _EXTERNAL_METRICS_CACHE
    path = BASE_DIR / "config" / "journal_metrics.csv"
    if not path.exists():
        _EXTERNAL_METRICS_CACHE = {}
        return {}
    metrics: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            journal = (row.get("journal") or row.get("Journal") or "").strip()
            if not journal:
                continue
            value = {
                "impact_factor": (row.get("impact_factor") or row.get("Impact Factor") or row.get("if") or "待核实").strip(),
                "quartile": (row.get("quartile") or row.get("Quartile") or row.get("partition") or "待核实").strip(),
                "metric_source": (row.get("source") or row.get("Source") or "config/journal_metrics.csv").strip(),
                "jcr_quartile": (row.get("jcr_quartile") or "").strip(),
                "cas_quartile": (row.get("cas_quartile") or "").strip(),
                "jif_rank": (row.get("jif_rank") or "").strip(),
                "category": (row.get("category") or "").strip(),
            }
            for key in journal_alias_keys(journal):
                metrics.setdefault(key, value)
    _EXTERNAL_METRICS_CACHE = metrics
    return metrics


def journal_metric(journal: str) -> dict[str, str]:
    name = (journal or "").strip().lower()
    compact = normalize_journal_name(name)
    external = load_external_metrics()
    for alias in journal_alias_keys(name):
        if alias in external:
            return external[alias]
    for key, metric in JOURNAL_METRICS.items():
        key_compact = normalize_journal_name(key)
        is_single_flagship = key in {"nature", "science", "cell", "jama", "bmj"}
        matched = compact == key_compact if is_single_flagship else (compact == key_compact or key_compact in compact)
        if matched:
            return {
                "impact_factor": str(metric["impact_factor"]),
                "quartile": str(metric["quartile"]),
                "metric_source": "内置参考表",
            }
    return {"impact_factor": "待核实", "quartile": "待核实", "metric_source": "未匹配"}


def enrich_metrics(item: dict[str, Any]) -> dict[str, Any]:
    copy = dict(item)
    metric = journal_metric(copy.get("journal", ""))
    copy.setdefault("impact_factor", metric["impact_factor"])
    copy.setdefault("quartile", metric["quartile"])
    copy.setdefault("metric_source", metric.get("metric_source", "未匹配"))
    copy.setdefault("pubmed_url", copy.get("url", "") if copy.get("pmid") else "")
    return copy


def enrich_metrics_many(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [enrich_metrics(item) for item in items]
