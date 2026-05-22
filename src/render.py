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


def build_payload(items: list[dict[str, Any]], errors: list[str], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "v1.0.0",
        "generated_at": now_cn(config.get("timezone", "Asia/Shanghai")),
        "count": len(items),
        "items": items,
        "errors": errors,
        "notice": "人工审核前推文草稿；不自动发布公众号。",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 神外文献日报 V1",
        "",
        f"生成时间：{payload['generated_at']}",
        f"筛选文献数量：{payload['count']}",
        "",
        "> 人工审核前推文草稿；请在引用、转发或公众号发布前核对原文。",
        "",
    ]
    if not payload["items"]:
        lines.append("本次未抓取到符合条件的文献。")
    for idx, item in enumerate(payload["items"], 1):
        lines.extend(
            [
                f"## {idx}. {item.get('title', '')}",
                "",
                f"- 主题：{item.get('topic_cn', '')}",
                f"- 来源：{item.get('source', '')}",
                f"- 期刊/平台：{item.get('journal', '')}",
                f"- 日期：{item.get('published', '')}",
                f"- 分数：{item.get('score', '')}",
                f"- PMID：{item.get('pmid', '') or 'N/A'}",
                f"- DOI：{item.get('doi', '') or 'N/A'}",
                f"- 链接：{item.get('url', '')}",
                "",
                f"中文总结：{item.get('ai_summary_cn', '')}",
                "",
                f"临床/科研意义：{item.get('clinical_relevance_cn', '')}",
                "",
                "推文草稿：",
                "",
                item.get("wechat_draft_cn", ""),
                "",
            ]
        )
    if payload.get("errors"):
        lines.extend(["## 抓取提示", ""])
        lines.extend([f"- {err}" for err in payload["errors"]])
    return "\n".join(lines).strip() + "\n"


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"【神外文献日报 V1】{payload['generated_at']}",
        f"今日筛选文献数量：{payload['count']}",
        "说明：人工审核前推文草稿，不自动发布公众号。",
        "",
    ]
    if not payload["items"]:
        lines.append("本次未抓取到符合条件的文献。")
    for idx, item in enumerate(payload["items"], 1):
        lines.extend(
            [
                f"{idx}. {item.get('title', '')}",
                f"   主题：{item.get('topic_cn', '')}｜来源：{item.get('source', '')}｜分数：{item.get('score', '')}",
                f"   期刊：{item.get('journal', '')}｜日期：{item.get('published', '')}",
                f"   PMID：{item.get('pmid', '') or 'N/A'}｜DOI：{item.get('doi', '') or 'N/A'}",
                f"   链接：{item.get('url', '')}",
                f"   总结：{item.get('ai_summary_cn', '')}",
                f"   意义：{item.get('clinical_relevance_cn', '')}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_html(payload: dict[str, Any]) -> str:
    cards = ""
    if not payload["items"]:
        cards = '<article class="card"><h2>本次未抓取到符合条件的文献</h2><p>请稍后重试，或查看 output/error_report.txt 中的抓取提示。</p></article>'
    else:
        for item in payload["items"]:
            cards += f"""
      <article class="card">
        <div class="meta"><span>{_esc(item.get('topic_cn'))}</span><span>{_esc(item.get('source'))}</span><span>Score {_esc(item.get('score'))}</span></div>
        <h2>{_esc(item.get('title'))}</h2>
        <p class="journal">{_esc(item.get('journal'))}｜{_esc(item.get('published'))}</p>
        <p class="ids">PMID: {_esc(item.get('pmid') or 'N/A')} ｜ DOI: {_esc(item.get('doi') or 'N/A')}</p>
        <p><a href="{_esc(item.get('url'))}" target="_blank" rel="noopener">打开原文</a></p>
        <section><h3>AI 中文总结</h3><p>{_esc(item.get('ai_summary_cn'))}</p></section>
        <section><h3>临床/科研意义</h3><p>{_esc(item.get('clinical_relevance_cn'))}</p></section>
        <details><summary>人工审核前推文草稿</summary><pre>{_esc(item.get('wechat_draft_cn'))}</pre></details>
      </article>
"""
    errors = "".join([f"<li>{_esc(err)}</li>" for err in payload.get("errors", [])])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Neurosurgery Literature Radar V1</title>
  <style>
    :root {{ --green:#064e3b; --line:#d8e3dc; --soft:#f4faf7; --ink:#17211d; --muted:#63736b; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif; color:var(--ink); background:#fff; }}
    header {{ padding:34px min(5vw,64px); background:linear-gradient(180deg,#f7fbf9,#fff); border-bottom:1px solid var(--line); }}
    .brand {{ color:var(--green); font-weight:900; letter-spacing:.08em; text-transform:uppercase; font-size:13px; }}
    h1 {{ margin:10px 0 8px; font-size:clamp(32px,5vw,58px); letter-spacing:-.06em; color:var(--green); }}
    .sub {{ color:var(--muted); font-size:16px; line-height:1.7; max-width:900px; }}
    main {{ width:min(1120px,calc(100% - 32px)); margin:22px auto 56px; }}
    .stats {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-bottom:18px; }}
    .stat {{ border:1px solid var(--line); background:var(--soft); border-radius:14px; padding:14px; }}
    .stat small {{ color:var(--muted); display:block; margin-bottom:6px; }}
    .stat strong {{ color:var(--green); font-size:22px; }}
    .card {{ border:1px solid var(--line); border-radius:18px; padding:20px; margin:16px 0; box-shadow:0 14px 36px rgba(6,78,59,.06); }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
    .meta span {{ background:var(--soft); color:var(--green); border:1px solid var(--line); border-radius:999px; padding:5px 9px; font-size:12px; font-weight:800; }}
    h2 {{ margin:0 0 10px; font-size:22px; line-height:1.35; letter-spacing:-.03em; }}
    h3 {{ color:var(--green); margin:16px 0 6px; }}
    .journal,.ids {{ color:var(--muted); margin:6px 0; }}
    a {{ color:#075985; font-weight:800; }}
    details {{ margin-top:14px; background:#fbfdfc; border:1px solid var(--line); border-radius:12px; padding:12px; }}
    summary {{ cursor:pointer; color:var(--green); font-weight:900; }}
    pre {{ white-space:pre-wrap; line-height:1.7; font-family:inherit; }}
    .errors {{ color:#7c2d12; }}
    @media (max-width:760px) {{ .stats {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <div class="brand">Neurosurgery Literature Radar V1</div>
    <h1>神外文献日报</h1>
    <p class="sub">每日自动检索 PubMed、bioRxiv、medRxiv、arXiv，聚焦脑损伤、脑积水、干细胞/外泌体、小胶质细胞/TREM2、胶质瘤与脊髓肿瘤。当前页面为人工审核前推文草稿。</p>
  </header>
  <main>
    <section class="stats">
      <div class="stat"><small>生成时间</small><strong>{_esc(payload['generated_at'])}</strong></div>
      <div class="stat"><small>筛选文献</small><strong>{_esc(payload['count'])}</strong></div>
      <div class="stat"><small>版本</small><strong>{_esc(payload['version'])}</strong></div>
    </section>
    {cards}
    <section class="errors"><h3>抓取提示</h3><ul>{errors or '<li>暂无错误报告。</li>'}</ul></section>
  </main>
</body>
</html>
"""


def write_outputs(items: list[dict[str, Any]], errors: list[str], config: dict[str, Any]) -> dict[str, Any]:
    payload = build_payload(items, errors, config)
    (BASE_DIR / "data").mkdir(exist_ok=True)
    (BASE_DIR / "output").mkdir(exist_ok=True)
    (BASE_DIR / "data/latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASE_DIR / "output/briefing.md").write_text(render_markdown(payload), encoding="utf-8")
    (BASE_DIR / "output/briefing.txt").write_text(render_text(payload), encoding="utf-8")
    (BASE_DIR / "index.html").write_text(render_html(payload), encoding="utf-8")
    if errors:
        (BASE_DIR / "output/error_report.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
    return payload
