from __future__ import annotations

import os

import requests


def send_wechat(title: str, content: str) -> bool:
    """Optional WeChat push via third-party channels.

    Supported environment variables:
    - PUSHPLUS_TOKEN: PushPlus one-to-one/group token.
    - PUSHPLUS_TOPIC: Optional PushPlus topic/group code.
    - SERVERCHAN_SENDKEY: ServerChan SendKey.

    The project does not auto-publish to an official WeChat account. These
    channels only send a private notification/card to WeChat.
    """
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if pushplus_token:
        topic = os.environ.get("PUSHPLUS_TOPIC", "").strip()
        payload = {
            "token": pushplus_token,
            "title": title,
            "content": content,
            "template": "txt",
        }
        if topic:
            payload["topic"] = topic
        try:
            response = requests.post(
                "https://www.pushplus.plus/send",
                json=payload,
                timeout=20,
            )
            if response.ok:
                print("WeChat PushPlus push success.")
                return True
            print(f"WeChat PushPlus push failed: {response.status_code} {response.text}")
            return False
        except Exception as exc:
            print(f"WeChat PushPlus push error: {exc}")
            return False

    serverchan_key = os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if serverchan_key:
        try:
            response = requests.post(
                f"https://sctapi.ftqq.com/{serverchan_key}.send",
                data={"title": title, "desp": content},
                timeout=20,
            )
            if response.ok:
                print("WeChat ServerChan push success.")
                return True
            print(f"WeChat ServerChan push failed: {response.status_code} {response.text}")
            return False
        except Exception as exc:
            print(f"WeChat ServerChan push error: {exc}")
            return False

    print("WeChat push token missing, skip push.")
    return False
