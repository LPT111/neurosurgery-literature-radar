from __future__ import annotations

import argparse
import traceback
from pathlib import Path

import yaml

from src.email_sender import send_email
from src.fetchers import fetch_all
from src.render import write_outputs
from src.scoring import rank_items
from src.summary import enrich_items


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
            raw_items, errors = fetch_all(config)
            ranked = rank_items(raw_items, config)
            max_items = int(config.get("max_items", 10))
            selected = ranked[:max_items]
            if not selected:
                errors.append("No matching items selected from live sources.")
            items = enrich_items(selected)
            payload = write_outputs(items, errors, config)
        except Exception as exc:
            errors.append(f"Fatal pipeline fallback: {exc}")
            errors.append(traceback.format_exc())
            fallback = enrich_items(fallback_items(config, str(exc)))
            payload = write_outputs(fallback, errors, config)

    if not no_email:
        send_email(payload)
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
