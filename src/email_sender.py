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
    def add_email_section(title: str, items: list[dict[str, Any]]) -> None:
        lines.extend([f"【{title}】", ""])
        if not items:
            lines.extend(["暂无候选内容。", ""])
            return
        for idx, item in enumerate(items, 1):
            lines.extend(
                [
                    f"{idx}. {item.get('title_cn') or item.get('title', '')}",
                    f"   英文：{item.get('title_en') or item.get('title', '')}",
                    f"   期刊：{item.get('journal', '')}｜IF：{item.get('impact_factor', '待核实')}｜分区：{item.get('quartile', '待核实')}｜指标：{item.get('metric_source', '未匹配')}",
                    f"   日期：{item.get('published', '')}｜PMID：{item.get('pmid', '') or 'N/A'}｜DOI：{item.get('doi', '') or 'N/A'}",
                    f"   链接：{item.get('pubmed_url') or item.get('url', '')}",
                    f"   摘要：{item.get('abstract', '') or '暂无摘要'}",
                    f"   AI中文总结：{item.get('ai_summary_cn', '')}",
                    "",
                ]
            )

    add_email_section("神外/脑损伤/脑积水核心文献", payload.get("items", []))
    sections = payload.get("sections", {})
    add_email_section("顶刊神经科学", sections.get("top_journal_neuroscience", []))
    add_email_section("全球热点话题｜学术界值得关注", sections.get("global_hot_topics", []))
    add_email_section("国内外医学与医药新闻", sections.get("medical_news", []))

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
