from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parents[1]


def now_cn(tz: str = "Asia/Shanghai") -> str:
    return datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d %H:%M:%S")


def _esc(value: Any) -> str:
    return html.escape(str(value or ""))


def build_payload(
    items: list[dict[str, Any]],
    errors: list[str],
    config: dict[str, Any],
    sections: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    sections = sections or {}
    return {
        "version": "v2.0.0",
        "generated_at": now_cn(config.get("timezone", "Asia/Shanghai")),
        "count": len(items),
        "items": items,
        "sections": sections,
        "total_count": len(items) + sum(len(v) for v in sections.values()),
        "errors": errors,
        "notice": "医学科研文献雷达；正式引用前请核对原文。",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 神外文献日报 V2",
        "",
        f"生成时间：{payload['generated_at']}",
        f"核心神外文献数量：{payload['count']}",
        f"全部条目数量：{payload.get('total_count', payload['count'])}",
        "",
        "> 医学科研文献雷达；正式引用前请核对原文。",
        "",
    ]
    if not payload["items"]:
        lines.append("本次未抓取到符合条件的文献。")
    def add_item(idx: int, item: dict[str, Any]) -> None:
        lines.extend(
            [
                f"## {idx}. {item.get('title_cn') or item.get('title', '')}",
                "",
                f"- 英文题目：{item.get('title_en') or item.get('title', '')}",
                f"- 主题：{item.get('topic_cn', '')}",
                f"- 来源：{item.get('source', '')}",
                f"- 期刊/平台：{item.get('journal', '')}",
                f"- 影响因子：{item.get('impact_factor', '待核实')}",
                f"- 分区：{item.get('quartile', '待核实')}",
                f"- 指标来源：{item.get('metric_source', '未匹配')}",
                f"- 日期：{item.get('published', '')}",
                f"- 分数：{item.get('score', '')}",
                f"- PMID：{item.get('pmid', '') or 'N/A'}",
                f"- DOI：{item.get('doi', '') or 'N/A'}",
                f"- PubMed/原文链接：{item.get('pubmed_url') or item.get('url', '')}",
                "",
                f"中文摘要：{item.get('abstract_cn', '') or '暂无中文摘要'}",
                "",
                f"英文摘要：{item.get('abstract', '') or '暂无摘要'}",
                "",
            ]
        )
    for idx, item in enumerate(payload["items"], 1):
        add_item(idx, item)
    section_titles = {
        "top_journal_neuroscience": "顶刊神经科学",
        "global_hot_topics": "全球热点话题｜学术界值得关注",
        "medical_news": "国内外医学与医药新闻",
    }
    for key, title in section_titles.items():
        section_items = payload.get("sections", {}).get(key, [])
        if not section_items:
            continue
        lines.extend([f"# {title}", ""])
        for idx, item in enumerate(section_items, 1):
            add_item(idx, item)
    if payload.get("errors"):
        lines.extend(["## 抓取提示", ""])
        lines.extend([f"- {err}" for err in payload["errors"]])
    return "\n".join(lines).strip() + "\n"


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"【神外文献日报 V2】{payload['generated_at']}",
        f"核心神外文献数量：{payload['count']}",
        f"全部条目数量：{payload.get('total_count', payload['count'])}",
        "说明：医学科研文献雷达；正式引用前请核对原文。",
        "",
    ]
    if not payload["items"]:
        lines.append("本次未抓取到符合条件的文献。")
    def add_text_items(title: str, items: list[dict[str, Any]]) -> None:
        lines.extend([f"【{title}】", ""])
        if not items:
            lines.extend(["暂无候选内容。", ""])
            return
        for idx, item in enumerate(items, 1):
            lines.extend(
                [
                    f"{idx}. {item.get('title_cn') or item.get('title', '')}",
                    f"   英文：{item.get('title_en') or item.get('title', '')}",
                    f"   主题：{item.get('topic_cn', '')}｜来源：{item.get('source', '')}｜分数：{item.get('score', '')}",
                    f"   期刊：{item.get('journal', '')}｜IF：{item.get('impact_factor', '待核实')}｜分区：{item.get('quartile', '待核实')}｜指标：{item.get('metric_source', '未匹配')}",
                    f"   日期：{item.get('published', '')}｜PMID：{item.get('pmid', '') or 'N/A'}｜DOI：{item.get('doi', '') or 'N/A'}",
                    f"   链接：{item.get('pubmed_url') or item.get('url', '')}",
                    f"   中文摘要：{item.get('abstract_cn', '') or '暂无中文摘要'}",
                    f"   英文摘要：{item.get('abstract', '') or '暂无摘要'}",
                    "",
                ]
            )
    add_text_items("神外/脑损伤/脑积水核心文献", payload.get("items", []))
    sections = payload.get("sections", {})
    add_text_items("顶刊神经科学", sections.get("top_journal_neuroscience", []))
    add_text_items("全球热点话题｜学术界值得关注", sections.get("global_hot_topics", []))
    add_text_items("国内外医学与医药新闻", sections.get("medical_news", []))
    return "\n".join(lines).strip() + "\n"


def render_feishu_text(payload: dict[str, Any], dashboard_url: str = "") -> str:
    generated = payload.get("generated_at", "")
    total = payload.get("total_count", payload.get("count", 0))
    lines = [
        f"【神外文献雷达 V2】{generated}",
        f"本次筛选：{total} 条文献/资讯",
    ]
    if dashboard_url:
        lines.append(f"完整网页：{dashboard_url}")
    lines.extend(
        [
            "说明：飞书为短版推送；完整题目、中文摘要、英文摘要、PMID/DOI 请打开网页查看。",
            "",
        ]
    )

    def add_short_section(title: str, items: list[dict[str, Any]], limit: int) -> None:
        if not items:
            return
        lines.extend([f"【{title}】", ""])
        for idx, item in enumerate(items[:limit], 1):
            link = item.get("pubmed_url") or item.get("url", "")
            summary = item.get("ai_summary_cn") or item.get("abstract_cn") or ""
            summary = " ".join(str(summary).split())
            if len(summary) > 110:
                summary = summary[:110] + "……"
            lines.extend(
                [
                    f"{idx}. {item.get('title_cn') or item.get('title', '')}",
                    f"   英文：{item.get('title_en') or item.get('title', '')}",
                    f"   期刊：{item.get('journal', '')}｜{item.get('published', '')}",
                    f"   IF：{item.get('impact_factor', '待核实')}｜分区：{item.get('quartile', '待核实')}",
                    f"   链接：{link}",
                    f"   要点：{summary}",
                    "",
                ]
            )

    add_short_section("神外/脑损伤/脑积水核心文献", payload.get("items", []), 3)
    sections = payload.get("sections", {}) or {}
    add_short_section("顶刊神经科学", sections.get("top_journal_neuroscience", []), 2)
    add_short_section("全球热点话题", sections.get("global_hot_topics", []), 1)
    add_short_section("医学与医药新闻", sections.get("medical_news", []), 1)
    lines.append("发稿前核验：研究类型、样本量、主要终点、全文结论、期刊指标和利益冲突。")
    return "\n".join(lines).strip() + "\n"


def render_html(payload: dict[str, Any]) -> str:
    def render_card(item: dict[str, Any]) -> str:
        return f"""
      <article class="card">
        <div class="meta"><span>{_esc(item.get('topic_cn'))}</span><span>{_esc(item.get('source'))}</span><span>Score {_esc(item.get('score'))}</span><span>IF {_esc(item.get('impact_factor', '待核实'))}</span><span>{_esc(item.get('quartile', '待核实'))}</span><span>{_esc(item.get('metric_source', '未匹配'))}</span></div>
        <h2>{_esc(item.get('title_cn') or item.get('title'))}</h2>
        <p class="title-en">{_esc(item.get('title_en') or item.get('title'))}</p>
        <p class="journal">{_esc(item.get('journal'))}｜{_esc(item.get('published'))}</p>
        <p class="ids">PMID: {_esc(item.get('pmid') or 'N/A')} ｜ DOI: {_esc(item.get('doi') or 'N/A')}</p>
        <p><a class="open-link" href="{_esc(item.get('pubmed_url') or item.get('url'))}" target="_blank" rel="noopener">打开 PubMed / 原文</a></p>
        <details><summary>中文摘要</summary><p>{_esc(item.get('abstract_cn') or '暂无中文摘要')}</p></details>
        <details><summary>英文摘要</summary><p>{_esc(item.get('abstract') or '暂无摘要')}</p></details>
      </article>
"""
    def render_section(key: str, title: str, items: list[dict[str, Any]]) -> str:
        body = "".join(render_card(item) for item in items) if items else '<article class="card"><h2>本版块暂无候选内容</h2><p>可稍后重新抓取，或调整关键词。</p></article>'
        return f"""
    <section class="section-block" id="{_esc(key)}">
      <div class="section-head">
        <div>
          <div class="eyebrow">{_esc(key)}</div>
          <h2>{_esc(title)}</h2>
        </div>
        <strong>{len(items)} 条</strong>
      </div>
      {body}
    </section>
"""
    cards = render_section(
        "core_neurosurgery",
        "神外/脑损伤/脑积水核心文献",
        payload.get("items", []),
    )
    sections = payload.get("sections", {})
    cards += render_section(
        "top_journal_neuroscience",
        "顶刊神经科学",
        sections.get("top_journal_neuroscience", []),
    )
    cards += render_section(
        "global_hot_topics",
        "全球热点话题｜学术界值得关注",
        sections.get("global_hot_topics", []),
    )
    cards += render_section(
        "medical_news",
        "国内外医学与医药新闻",
        sections.get("medical_news", []),
    )
    errors = "".join([f"<li>{_esc(err)}</li>" for err in payload.get("errors", [])])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Neurosurgery Literature Radar V2</title>
  <style>
    html {{ scroll-behavior:smooth; }}
    :root {{ --green:#064e3b; --line:#d8e3dc; --soft:#f4faf7; --ink:#17211d; --muted:#63736b; --paper:#ffffff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif; color:var(--ink); background:#fff; }}
    header {{ padding:34px min(5vw,64px); background:linear-gradient(180deg,#f7fbf9,#fff); border-bottom:1px solid var(--line); }}
    .brand {{ color:var(--green); font-weight:900; letter-spacing:.08em; text-transform:uppercase; font-size:13px; }}
    h1 {{ margin:10px 0 8px; font-size:clamp(32px,5vw,58px); letter-spacing:-.06em; color:var(--green); }}
    .page {{ width:min(1420px,calc(100% - 32px)); margin:22px auto 56px; display:grid; grid-template-columns:240px minmax(0,1fr); gap:22px; align-items:start; }}
    .toc {{ position:sticky; top:18px; border:1px solid var(--line); border-radius:18px; background:rgba(255,255,255,.94); padding:14px; box-shadow:0 14px 36px rgba(6,78,59,.05); }}
    .toc-title {{ color:var(--green); font-weight:900; font-size:13px; letter-spacing:.1em; text-transform:uppercase; margin:2px 0 10px; }}
    .toc a {{ display:flex; justify-content:space-between; gap:10px; align-items:center; padding:10px 11px; border-radius:12px; color:#244238; text-decoration:none; font-weight:800; font-size:13px; }}
    .toc a:hover {{ background:var(--soft); text-decoration:none; }}
    .toc small {{ color:var(--muted); font-weight:800; }}
    main {{ min-width:0; }}
    .stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:18px; }}
    .stat {{ border:1px solid var(--line); background:var(--soft); border-radius:14px; padding:14px; }}
    .stat small {{ color:var(--muted); display:block; margin-bottom:6px; }}
    .stat strong {{ color:var(--green); font-size:22px; }}
    .card {{ border:1px solid var(--line); border-radius:18px; padding:20px; margin:16px 0; box-shadow:0 14px 36px rgba(6,78,59,.06); }}
    .section-block {{ margin:28px 0 44px; }}
    .section-head {{ display:flex; justify-content:space-between; gap:18px; align-items:flex-end; border-bottom:2px solid var(--green); padding-bottom:12px; margin-bottom:16px; }}
    .section-head h2 {{ color:var(--green); font-size:30px; margin:0 0 6px; }}
    .section-head p {{ color:var(--muted); margin:0; line-height:1.65; max-width:860px; }}
    .section-head strong {{ color:var(--green); white-space:nowrap; }}
    .eyebrow {{ color:var(--muted); font-size:12px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; margin-bottom:4px; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
    .meta span {{ background:var(--soft); color:var(--green); border:1px solid var(--line); border-radius:999px; padding:5px 9px; font-size:12px; font-weight:800; }}
    h2 {{ margin:0 0 10px; font-size:22px; line-height:1.35; letter-spacing:-.03em; }}
    h3 {{ color:var(--green); margin:16px 0 6px; }}
    .title-en {{ color:#29433a; font-weight:700; line-height:1.55; }}
    .journal,.ids {{ color:var(--muted); margin:6px 0; }}
    a {{ color:#075985; font-weight:800; }}
    .open-link {{ display:inline-flex; align-items:center; justify-content:center; min-height:36px; padding:8px 13px; border-radius:999px; background:var(--green); color:white; text-decoration:none; }}
    .open-link:hover {{ color:white; text-decoration:none; filter:brightness(1.05); }}
    details {{ margin-top:14px; background:#fbfdfc; border:1px solid var(--line); border-radius:12px; padding:12px; }}
    summary {{ cursor:pointer; color:var(--green); font-weight:900; }}
    pre {{ white-space:pre-wrap; line-height:1.7; font-family:inherit; }}
    .errors {{ color:#7c2d12; }}
    @media (max-width:980px) {{ .page {{ grid-template-columns:1fr; }} .toc {{ position:relative; top:auto; }} }}
    @media (max-width:760px) {{ .stats {{ grid-template-columns:1fr; }} .section-head {{ display:block; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand">Neurosurgery Literature Radar V2</div>
    <h1>神外文献日报</h1>
  </header>
  <div class="page">
    <nav class="toc" aria-label="页面目录">
      <div class="toc-title">目录</div>
      <a href="#overview">顶部总览 <small>Top</small></a>
      <a href="#core_neurosurgery">核心文献 <small>{_esc(payload['count'])}</small></a>
      <a href="#top_journal_neuroscience">顶刊神经科学 <small>{_esc(len(sections.get('top_journal_neuroscience', [])))}</small></a>
      <a href="#global_hot_topics">全球热点话题 <small>{_esc(len(sections.get('global_hot_topics', [])))}</small></a>
      <a href="#medical_news">医学与医药新闻 <small>{_esc(len(sections.get('medical_news', [])))}</small></a>
      <a href="#fetch-notes">抓取提示 <small>Log</small></a>
    </nav>
    <main>
      <section class="stats" id="overview">
        <div class="stat"><small>生成时间</small><strong>{_esc(payload['generated_at'])}</strong></div>
        <div class="stat"><small>核心文献</small><strong>{_esc(payload['count'])}</strong></div>
        <div class="stat"><small>全部条目</small><strong>{_esc(payload.get('total_count', payload['count']))}</strong></div>
        <div class="stat"><small>版本</small><strong>{_esc(payload['version'])}</strong></div>
      </section>
      {cards}
      <section class="errors" id="fetch-notes"><h3>抓取提示</h3><ul>{errors or '<li>暂无错误报告。</li>'}</ul></section>
    </main>
  </div>
</body>
</html>
"""


def write_outputs(
    items: list[dict[str, Any]],
    errors: list[str],
    config: dict[str, Any],
    sections: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    payload = build_payload(items, errors, config, sections)
    (BASE_DIR / "data").mkdir(exist_ok=True)
    (BASE_DIR / "output").mkdir(exist_ok=True)
    (BASE_DIR / "data/latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASE_DIR / "output/briefing.md").write_text(render_markdown(payload), encoding="utf-8")
    (BASE_DIR / "output/briefing.txt").write_text(render_text(payload), encoding="utf-8")
    (BASE_DIR / "index.html").write_text(render_html(payload), encoding="utf-8")
    if errors:
        (BASE_DIR / "output/error_report.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
    return payload
