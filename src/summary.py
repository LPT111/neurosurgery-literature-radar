from __future__ import annotations

import json
import os
from typing import Any

import requests


def _fallback_title_cn(title: str) -> str:
    return f"论文标题：{title}"


def _rule_summary(item: dict[str, Any]) -> dict[str, str]:
    title = item.get("title", "")
    section_cn = item.get("section_cn") or item.get("topic_cn", "神经外科相关方向")
    topic_cn = item.get("topic_cn", "神经外科相关方向")
    abstract = item.get("abstract", "")
    short_abs = abstract[:260].strip()
    if short_abs and len(abstract) > 260:
        short_abs += "..."
    finding = short_abs or "该条目暂无摘要，建议人工打开原文核对研究设计、样本量和主要结果。"
    return {
        "title_en": title,
        "title_cn": item.get("title_cn") or _fallback_title_cn(title),
        "tweet_title_cn": f"【文献速递】{title}",
        "ai_summary_cn": f"这条内容归入“{section_cn}”，聚焦{topic_cn}。主要信息来自题名、期刊/来源和摘要。{finding}",
        "clinical_relevance_cn": f"对{topic_cn}方向有参考价值，既可关注基础机制，也可关注临床对照、队列、治疗或诊断研究；正式引用前需核对全文。",
        "wechat_draft_cn": (
            f"【文献速递】{title}\n\n"
            "研究背景：该研究与神经外科、脑损伤、脑积水或神经炎症相关，可能为课题设计和综述选题提供线索。\n\n"
            f"核心发现：{finding}\n\n"
            "临床/科研意义：建议重点核对研究对象、模型、干预方式、主要终点和局限性，再判断是否纳入综述或选题库。\n\n"
            "小满点评：这是一条需要人工复核全文的候选文献，当前摘要层面不宜过度外推。\n\n"
            f"参考信息：{item.get('journal', '')}｜IF {item.get('impact_factor', '待核实')}｜{item.get('quartile', '待核实')}｜{item.get('published', '')}｜{item.get('url', '')}"
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
        "task": "请把英文论文题目准确翻译为简体中文，并用克制、准确的中文为医学科研人员生成文献日报字段。不要夸大，不要编造摘要外信息。输出 JSON，字段为 title_cn, title_en, tweet_title_cn, ai_summary_cn, clinical_relevance_cn, wechat_draft_cn。title_cn 必须是自然的简体中文论文题目，不要出现“待校对”。",
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
        required = ["title_cn", "title_en", "tweet_title_cn", "ai_summary_cn", "clinical_relevance_cn", "wechat_draft_cn"]
        if all(data.get(k) for k in required):
            result = {k: str(data[k]) for k in required}
            result["title_en"] = result.get("title_en") or item.get("title", "")
            return result
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
