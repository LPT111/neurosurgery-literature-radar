from __future__ import annotations

import json
import os
from typing import Any

import requests


def _rule_summary(item: dict[str, Any]) -> dict[str, str]:
    title = item.get("title", "")
    topic_cn = item.get("topic_cn", "神经外科相关方向")
    abstract = item.get("abstract", "")
    short_abs = abstract[:260].strip()
    if short_abs and len(abstract) > 260:
        short_abs += "..."
    finding = short_abs or "该条目暂无摘要，建议人工打开原文核对研究设计、样本量和主要结果。"
    return {
        "tweet_title_cn": f"【文献速递】{title}",
        "ai_summary_cn": f"这篇文献聚焦{topic_cn}，主要信息来自题名、期刊和摘要。{finding}",
        "clinical_relevance_cn": f"对{topic_cn}方向有参考价值，适合用于判断机制线索、模型选择、治疗递送策略或临床转化背景；正式引用前需核对全文。",
        "wechat_draft_cn": (
            f"【文献速递】{title}\n\n"
            "研究背景：该研究与神经外科、脑损伤、脑积水或神经炎症相关，可能为课题设计和综述选题提供线索。\n\n"
            f"核心发现：{finding}\n\n"
            "临床/科研意义：建议重点核对研究对象、模型、干预方式、主要终点和局限性，再判断是否纳入综述或选题库。\n\n"
            "小满点评：这是一条需要人工复核全文的候选文献，当前摘要层面不宜过度外推。\n\n"
            f"参考信息：{item.get('journal', '')}｜{item.get('published', '')}｜{item.get('url', '')}"
        ),
    }


def _openai_summary(item: dict[str, Any], model: str) -> dict[str, str] | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    prompt = {
        "title": item.get("title", ""),
        "journal": item.get("journal", ""),
        "published": item.get("published", ""),
        "topic_cn": item.get("topic_cn", ""),
        "abstract": item.get("abstract", ""),
        "task": "请用克制、准确的中文为医学科研人员生成文献日报字段，不要夸大，不要编造摘要外信息。输出 JSON，字段为 tweet_title_cn, ai_summary_cn, clinical_relevance_cn, wechat_draft_cn。",
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是严谨的神经外科与神经科学文献助理。只基于给定信息总结。"},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        required = ["tweet_title_cn", "ai_summary_cn", "clinical_relevance_cn", "wechat_draft_cn"]
        if all(data.get(k) for k in required):
            return {k: str(data[k]) for k in required}
    except Exception as exc:
        print(f"OpenAI summary fallback for {item.get('title', '')[:60]}: {exc}")
    return None


def enrich_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    enriched = []
    for item in items:
        summary = _openai_summary(item, model) or _rule_summary(item)
        copy = dict(item)
        copy.update(summary)
        enriched.append(copy)
    return enriched
