from __future__ import annotations

import html
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import Any

import feedparser
import requests


NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
HEADERS = {"User-Agent": "neurosurgery-literature-radar/1.0 (+https://github.com/LPT111/neurosurgery-literature-radar)"}


def _request_json(url: str, params: dict[str, Any] | None = None, timeout: int = 25) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _request_text(url: str, params: dict[str, Any] | None = None, timeout: int = 25) -> str:
    response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def normalize_keywords(topic: dict[str, Any]) -> list[str]:
    return [str(k).strip() for k in topic.get("keywords", []) if str(k).strip()]


def keyword_query(keywords: list[str]) -> str:
    parts = []
    for kw in keywords:
        escaped = kw.replace('"', "")
        if " " in escaped:
            parts.append(f'"{escaped}"[Title/Abstract]')
        else:
            parts.append(f'{escaped}[Title/Abstract]')
    return " OR ".join(parts)


def journal_query(journals: list[str]) -> str:
    parts = []
    for journal in journals:
        escaped = str(journal).replace('"', "").strip()
        if escaped:
            parts.append(f'"{escaped}"[Journal]')
    return " OR ".join(parts)


def _text_from_article(article: ET.Element, path: str) -> str:
    node = article.find(path)
    if node is None or node.text is None:
        return ""
    return html.unescape(node.text.strip())


def _article_date(article: ET.Element) -> str:
    pub_date = article.find(".//JournalIssue/PubDate")
    if pub_date is None:
        return ""
    year = pub_date.findtext("Year") or ""
    month = pub_date.findtext("Month") or "01"
    day = pub_date.findtext("Day") or "01"
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    month = month_map.get(month[:3], month)
    if not year:
        return ""
    if not month.isdigit():
        month = "01"
    if not day.isdigit():
        day = "01"
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _extract_doi(article: ET.Element) -> str:
    for node in article.findall(".//ArticleId"):
        if node.attrib.get("IdType") == "doi" and node.text:
            return node.text.strip()
    for node in article.findall(".//ELocationID"):
        if node.attrib.get("EIdType") == "doi" and node.text:
            return node.text.strip()
    return ""


def _extract_abstract(article: ET.Element) -> str:
    texts = []
    for node in article.findall(".//AbstractText"):
        label = node.attrib.get("Label", "")
        text = "".join(node.itertext()).strip()
        if text:
            texts.append(f"{label}: {text}" if label else text)
    return html.unescape(" ".join(texts))


def _extract_authors(article: ET.Element) -> str:
    authors = []
    for author in article.findall(".//Author")[:8]:
        last = author.findtext("LastName") or ""
        fore = author.findtext("ForeName") or ""
        collective = author.findtext("CollectiveName") or ""
        name = collective or " ".join([fore, last]).strip()
        if name:
            authors.append(name)
    return "; ".join(authors)


def fetch_pubmed_for_topic(topic_key: str, topic: dict[str, Any], reldate: int = 7, retmax: int = 40) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    keywords = normalize_keywords(topic)
    query = keyword_query(keywords)
    if not query:
        return [], [f"{topic_key}: empty keywords"]
    try:
        search = _request_json(
            f"{NCBI_BASE}/esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": retmax,
                "sort": "pub date",
                "datetype": "pdat",
                "reldate": reldate,
            },
        )
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return [], []
        time.sleep(0.34)
        # esummary is requested as required; efetch below provides richer DOI/abstract fields.
        _request_json(f"{NCBI_BASE}/esummary.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
        time.sleep(0.34)
        xml_text = _request_text(f"{NCBI_BASE}/efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
        root = ET.fromstring(xml_text)
        items = []
        for article in root.findall(".//PubmedArticle"):
            pmid = _text_from_article(article, ".//PMID")
            title = _text_from_article(article, ".//ArticleTitle")
            journal = _text_from_article(article, ".//Journal/Title")
            published = _article_date(article)
            doi = _extract_doi(article)
            abstract = _extract_abstract(article)
            if not title:
                continue
            items.append(
                {
                    "source": "PubMed",
                    "topic": topic_key,
                    "topic_cn": topic.get("label_cn", topic_key),
                    "id": f"pubmed:{pmid}",
                    "pmid": pmid,
                    "doi": doi,
                    "title": title,
                    "journal": journal,
                    "published": published,
                    "authors": _extract_authors(article),
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                }
            )
        return items, errors
    except Exception as exc:
        return [], [f"PubMed {topic_key}: {exc}"]


def fetch_pubmed_query(
    section: str,
    section_cn: str,
    query: str,
    reldate: int = 14,
    retmax: int = 50,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not query:
        return [], [f"PubMed {section}: empty query"]
    try:
        search = _request_json(
            f"{NCBI_BASE}/esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": retmax,
                "sort": "pub date",
                "datetype": "pdat",
                "reldate": reldate,
            },
        )
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return [], []
        time.sleep(0.34)
        _request_json(f"{NCBI_BASE}/esummary.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
        time.sleep(0.34)
        xml_text = _request_text(f"{NCBI_BASE}/efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
        root = ET.fromstring(xml_text)
        items = []
        for article in root.findall(".//PubmedArticle"):
            pmid = _text_from_article(article, ".//PMID")
            title = _text_from_article(article, ".//ArticleTitle")
            journal = _text_from_article(article, ".//Journal/Title")
            if not title:
                continue
            items.append(
                {
                    "source": "PubMed",
                    "section": section,
                    "section_cn": section_cn,
                    "topic": section,
                    "topic_cn": section_cn,
                    "id": f"pubmed:{pmid}",
                    "pmid": pmid,
                    "doi": _extract_doi(article),
                    "title": title,
                    "journal": journal,
                    "published": _article_date(article),
                    "authors": _extract_authors(article),
                    "abstract": _extract_abstract(article),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                }
            )
        return items, []
    except Exception as exc:
        return [], [f"PubMed {section}: {exc}"]


def _contains_keywords(title: str, abstract: str, keywords: list[str]) -> bool:
    text = f"{title} {abstract}".lower()
    return any(kw.lower() in text for kw in keywords)


def fetch_biorxiv_server(server: str, topics: dict[str, Any], days: int = 7) -> tuple[list[dict[str, Any]], list[str]]:
    end = date.today()
    start = end - timedelta(days=days)
    url = f"https://api.biorxiv.org/details/{server}/{start.isoformat()}/{end.isoformat()}/0"
    try:
        data = _request_json(url, timeout=30)
        collection = data.get("collection", [])
        items = []
        for row in collection:
            title = html.unescape(row.get("title", "").strip())
            abstract = html.unescape(row.get("abstract", "").strip())
            for topic_key, topic in topics.items():
                keywords = normalize_keywords(topic)
                if _contains_keywords(title, abstract, keywords):
                    doi = row.get("doi", "")
                    items.append(
                        {
                            "source": server,
                            "topic": topic_key,
                            "topic_cn": topic.get("label_cn", topic_key),
                            "id": f"{server}:{doi or title}",
                            "pmid": "",
                            "doi": doi,
                            "title": title,
                            "journal": server,
                            "published": row.get("date", ""),
                            "authors": row.get("authors", ""),
                            "abstract": abstract,
                            "url": f"https://doi.org/{doi}" if doi else row.get("jatsxml", ""),
                        }
                    )
                    break
        return items, []
    except Exception as exc:
        return [], [f"{server}: {exc}"]


def fetch_arxiv_for_topic(topic_key: str, topic: dict[str, Any], max_results: int = 25) -> tuple[list[dict[str, Any]], list[str]]:
    keywords = normalize_keywords(topic)
    if not keywords:
        return [], []
    query = " OR ".join([f'all:"{kw}"' for kw in keywords[:6]])
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        # arXiv is useful but can rate-limit automated clients. V1 keeps one
        # short, gentle attempt per topic so the daily radar is not blocked.
        time.sleep(2)
        text = _request_text("https://export.arxiv.org/api/query", params=params, timeout=15)
        feed = feedparser.parse(text)
        items = []
        cutoff = datetime.utcnow() - timedelta(days=14)
        for entry in feed.entries:
            published = entry.get("published", "")[:10]
            try:
                if datetime.fromisoformat(published) < cutoff:
                    continue
            except Exception:
                pass
            title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
            abstract = re.sub(r"\s+", " ", entry.get("summary", "")).strip()
            if not _contains_keywords(title, abstract, keywords):
                continue
            items.append(
                {
                    "source": "arXiv",
                    "topic": topic_key,
                    "topic_cn": topic.get("label_cn", topic_key),
                    "id": entry.get("id", ""),
                    "pmid": "",
                    "doi": "",
                    "title": title,
                    "journal": "arXiv",
                    "published": published,
                    "authors": "; ".join([a.get("name", "") for a in entry.get("authors", [])[:8]]),
                    "abstract": abstract,
                    "url": entry.get("link", entry.get("id", "")),
                }
            )
        return items, []
    except Exception as exc:
        return [], [f"arXiv {topic_key}: {exc}"]


def fetch_all(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    topics = config.get("topics", {})
    all_items: list[dict[str, Any]] = []
    errors: list[str] = []
    for topic_key, topic in topics.items():
        items, errs = fetch_pubmed_for_topic(topic_key, topic)
        all_items.extend(items)
        errors.extend(errs)
        arxiv_items, arxiv_errs = fetch_arxiv_for_topic(topic_key, topic)
        all_items.extend(arxiv_items)
        errors.extend(arxiv_errs)
    for server in ["biorxiv", "medrxiv"]:
        items, errs = fetch_biorxiv_server(server, topics)
        all_items.extend(items)
        errors.extend(errs)
    return all_items, errors


def fetch_top_journal_neuroscience(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    section = config.get("top_journal_neuroscience", {})
    keywords = normalize_keywords(section)
    journals = [str(j).strip() for j in section.get("journals", []) if str(j).strip()]
    query = f"({keyword_query(keywords)}) AND ({journal_query(journals)})"
    return fetch_pubmed_query(
        "top_journal_neuroscience",
        section.get("label_cn", "顶刊神经科学"),
        query,
        reldate=21,
        retmax=80,
    )


def fetch_global_hot_topics(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    section = config.get("global_hot_topics", {})
    keywords = normalize_keywords(section)
    clinical = "clinical trial[Publication Type] OR randomized[Title/Abstract] OR cohort[Title/Abstract] OR multi-center[Title/Abstract]"
    query = f"({keyword_query(keywords)}) OR ({clinical})"
    return fetch_pubmed_query(
        "global_hot_topics",
        section.get("label_cn", "全球学术热点"),
        query,
        reldate=10,
        retmax=80,
    )


def fetch_medical_news(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    feeds = config.get("medical_news_feeds", [])
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    keywords = [
        "neuro", "brain", "spinal", "cancer", "tumor", "glioma", "medicine",
        "drug", "therapy", "clinical", "trial", "fda", "nih", "pharma",
        "biotech", "device", "diagnostic", "alzheimer", "parkinson",
    ]
    cutoff = datetime.utcnow() - timedelta(days=14)
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.get("url", ""))
            if getattr(parsed, "bozo", 0) and not parsed.entries:
                errors.append(f"Medical news {feed.get('name')}: feed parse failed")
                continue
            for entry in parsed.entries[:20]:
                title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
                summary = re.sub(r"\s+", " ", entry.get("summary", "")).strip()
                text = f"{title} {summary}".lower()
                if not any(k in text for k in keywords):
                    continue
                published = entry.get("published", "") or entry.get("updated", "")
                published_date = published[:10] if published else ""
                try:
                    if published_date and datetime.fromisoformat(published_date) < cutoff:
                        continue
                except Exception:
                    pass
                items.append(
                    {
                        "source": feed.get("name", "Medical news"),
                        "section": "medical_news",
                        "section_cn": "国内外医学与医药新闻",
                        "topic": "medical_news",
                        "topic_cn": "国内外医学与医药新闻",
                        "id": entry.get("id") or entry.get("link") or title,
                        "pmid": "",
                        "doi": "",
                        "title": title,
                        "journal": feed.get("name", "Medical news"),
                        "published": published_date,
                        "authors": "",
                        "abstract": summary,
                        "url": entry.get("link", ""),
                    }
                )
        except Exception as exc:
            errors.append(f"Medical news {feed.get('name')}: {exc}")
    return items, errors


def safe_url(value: str) -> str:
    value = value or ""
    if value.startswith("http"):
        return value
    return urllib.parse.quote(value)
