from __future__ import annotations

import json
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]


def _attach(msg: MIMEMultipart, path: Path) -> None:
    if not path.exists():
        return
    part = MIMEApplication(path.read_bytes(), Name=path.name)
    part["Content-Disposition"] = f'attachment; filename="{path.name}"'
    msg.attach(part)


def send_email(payload: dict[str, Any], test: bool = False) -> bool:
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_APP_PASSWORD")
    if not user or not password:
        print("Email skipped because SMTP credentials are missing.")
        return False

    host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    port = int(os.environ.get("SMTP_PORT") or "587")
    email_from = os.environ.get("EMAIL_FROM") or user
    email_to = os.environ.get("EMAIL_TO", "lipengtao12@gmail.com")
    public_url = os.environ.get("PUBLIC_DASHBOARD_URL", "")

    subject = f"【神外文献日报 V1】{payload.get('generated_at', '')[:10]} 最新文献收集结果"
    if test:
        subject = f"【神外文献日报 V1 测试】{payload.get('generated_at', '')}"

    lines = [
        f"今日筛选文献数量：{payload.get('count', 0)}",
        f"网页链接：{public_url or '未配置 PUBLIC_DASHBOARD_URL；请查看附件 index.html 或仓库根目录 index.html。'}",
        "",
    ]
    for idx, item in enumerate(payload.get("items", []), 1):
        lines.extend(
            [
                f"{idx}. {item.get('title', '')}",
                f"   期刊：{item.get('journal', '')}｜日期：{item.get('published', '')}",
                f"   PMID：{item.get('pmid', '') or 'N/A'}｜DOI：{item.get('doi', '') or 'N/A'}",
                f"   链接：{item.get('url', '')}",
                f"   AI中文总结：{item.get('ai_summary_cn', '')}",
                "",
            ]
        )

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    msg.attach(MIMEText("\n".join(lines), "plain", "utf-8"))
    for rel in ["output/briefing.md", "output/briefing.txt", "data/latest.json", "index.html"]:
        _attach(msg, BASE_DIR / rel)

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(email_from, [email_to], msg.as_string())
    print(f"Email sent to {email_to}")
    return True


def payload_from_latest() -> dict[str, Any]:
    return json.loads((BASE_DIR / "data/latest.json").read_text(encoding="utf-8"))
