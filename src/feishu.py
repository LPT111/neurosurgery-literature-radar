from __future__ import annotations

import os
import requests


def send_feishu(text: str) -> bool:
    webhook = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook:
        print("Feishu webhook missing, skip push.")
        return False
    try:
        response = requests.post(webhook, json={"msg_type": "text", "content": {"text": text}}, timeout=20)
        if not response.ok:
            print(f"Feishu push failed: {response.status_code} {response.text}")
            return False
        print("Feishu push success.")
        return True
    except Exception as exc:
        print(f"Feishu push error: {exc}")
        return False


def send_feishu_card(title: str, text: str, dashboard_url: str = "") -> bool:
    webhook = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook:
        print("Feishu webhook missing, skip push.")
        return False

    elements: list[dict] = [
        {"tag": "div", "text": {"tag": "lark_md", "content": text}},
    ]
    if dashboard_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "打开网页版"},
                        "type": "primary",
                        "url": dashboard_url,
                    }
                ],
            }
        )
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": elements,
        },
    }
    try:
        response = requests.post(webhook, json=payload, timeout=20)
        if not response.ok:
            print(f"Feishu card push failed: {response.status_code} {response.text}")
            return False
        print("Feishu card push success.")
        return True
    except Exception as exc:
        print(f"Feishu card push error: {exc}")
        return False
