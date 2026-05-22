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
