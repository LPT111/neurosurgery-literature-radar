from __future__ import annotations

import argparse
import os
import traceback
from pathlib import Path

import yaml

from src.email_sender import send_email
from src.feishu import send_feishu
from src.fetchers import fetch_all, fetch_global_hot_topics, fetch_medical_news, fetch_top_journal_neuroscience
from src.journal_metrics import enrich_metrics_many
from src.render import render_feishu_text, write_outputs
from src.scoring import rank_items
from src.summary import enrich_items
from src.wechat import send_wechat


BASE_DIR = Path(__file__).resolve().parent


def load_config() -> dict:
    return yaml.safe_load((BASE_DIR / "config/topics.yaml").read_text(encoding="utf-8"))


def fallback_items(config: dict, reason: str) -> list[dict]:
    return [
        {
            "source": "fallback",
            "topic": "neurosurgery_general",
            "topic_cn": "神经外科综合",
            "id": "fallback:no-items",
            "pmid": "",
            "doi": "",
            "title": "本次真实抓取未返回稳定候选文献，请稍后重试或检查 error_report.txt",
            "journal": "Local fallback",
            "published": "",
            "authors": "",
            "abstract": reason,
            "url": "",
            "score": 0,
        }
    ]


def prepare_items(raw_items: list[dict], config: dict, limit: int) -> list[dict]:
    ranked = rank_items(raw_items, config)
    return enrich_items(enrich_metrics_many(ranked[:limit]))


def push_feishu_briefing(payload: dict) -> bool:
    dashboard_url = os.environ.get("PUBLIC_DASHBOARD_URL", "").strip()
    full_text = render_feishu_text(payload, dashboard_url)
    if len(full_text) > 3800:
        link_line = f"\n\n完整网页：{dashboard_url}" if dashboard_url else ""
        full_text = full_text[:3600] + link_line + "\n\n内容较长，已截断；请打开网页查看完整版本。"
    return send_feishu(full_text)


def push_wechat_briefing(payload: dict) -> bool:
    dashboard_url = os.environ.get("PUBLIC_DASHBOARD_URL", "").strip()
    text = render_feishu_text(payload, dashboard_url)
    if len(text) > 3200:
        text = text[:3200] + "\n\n内容较长，请打开网页查看完整版本。"
    return send_wechat(f"神外文献雷达 V1｜{payload.get('generated_at', '')}", text)


def run(preview: bool = False, no_email: bool = False, email_test: bool = False) -> dict:
    config = load_config()
    errors: list[str] = []
    if email_test:
        from preview_local import sample_items

        items = enrich_items(sample_items())
        payload = write_outputs(items, ["Email test mode: sample data only."], config)
        send_email(payload, test=True)
        return payload

    if preview:
        from preview_local import sample_items

        items = enrich_items(sample_items())
        payload = write_outputs(items, ["Preview mode: sample data only."], config)
    else:
        try:
            raw_items, base_errors = fetch_all(config)
            top_raw, top_errors = fetch_top_journal_neuroscience(config)
            hot_raw, hot_errors = fetch_global_hot_topics(config)
            news_raw, news_errors = fetch_medical_news(config)
            errors = base_errors + top_errors + hot_errors + news_errors

            max_items = int(config.get("max_items", 10))
            items = prepare_items(raw_items, config, max_items)
            top_items = prepare_items(top_raw, config, int(config.get("top_journal_max_items", 8)))
            hot_items = prepare_items(hot_raw, config, int(config.get("global_hot_max_items", 8)))
            news_items = prepare_items(news_raw, config, int(config.get("medical_news_max_items", 10)))

            if not items and not top_items and not hot_items and not news_items:
                errors.append("No matching items selected from live sources.")
            payload = write_outputs(
                items,
                errors,
                config,
                sections={
                    "top_journal_neuroscience": top_items,
                    "global_hot_topics": hot_items,
                    "medical_news": news_items,
                },
            )
        except Exception as exc:
            errors.append(f"Fatal pipeline fallback: {exc}")
            errors.append(traceback.format_exc())
            fallback = enrich_items(enrich_metrics_many(fallback_items(config, str(exc))))
            payload = write_outputs(fallback, errors, config, sections={})

    if not no_email:
        send_email(payload)
        push_feishu_briefing(payload)
        push_wechat_briefing(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Neurosurgery Literature Radar V1")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--email-test", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    run(preview=args.preview, no_email=args.no_email, email_test=args.email_test)


if __name__ == "__main__":
    main()
