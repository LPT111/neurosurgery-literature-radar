# Neurosurgery Literature Radar V1

神外/脑损伤/脑积水/干细胞/外泌体文献日报收集器。项目每日检索 PubMed、bioRxiv、medRxiv、arXiv，筛选 5-10 篇与神经外科科研相关的最新文献，生成网页、JSON、Markdown、TXT 和邮件日报。

## 功能

- PubMed E-utilities 检索，近 7 天 `datetype=pdat`
- bioRxiv / medRxiv API 检索
- arXiv API 检索
- 关键词评分、优先期刊加权、DOI/PMID/标题去重
- 中文文献总结：有 `OPENAI_API_KEY` 时调用 OpenAI；否则使用规则模板
- 输出人工审核前推文草稿，不自动发布公众号
- Gmail SMTP 邮件推送，使用 Gmail App Password
- GitHub Actions 每天北京时间 07:40 自动运行
- GitHub Pages 可展示根目录 `index.html`

## 本地运行

```bash
cd ~/AIProjects/neurosurgery-literature-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_daily.py --no-email
open index.html
```

## 本地检查

```bash
bash scripts/check_v1.sh
```

成功时输出：

```text
V1 local check passed
```

## 邮件测试

```bash
SMTP_USER=lipengtao12@gmail.com \
SMTP_APP_PASSWORD="你的 Gmail 应用专用密码" \
EMAIL_TO=lipengtao12@gmail.com \
bash scripts/test_email.sh
```

如果缺少 SMTP 凭据，主流程不会失败，会打印：

```text
Email skipped because SMTP credentials are missing.
```

## GitHub Actions

workflow 文件：

```text
.github/workflows/literature-radar-v1.yml
```

定时：

- 北京时间 07:40
- UTC 23:40

也支持 `workflow_dispatch` 手动触发，手动触发时会尝试发送测试邮件。

## GitHub Secrets

必需邮件推送：

- `SMTP_USER`
- `SMTP_APP_PASSWORD`
- `EMAIL_TO`
- `EMAIL_FROM`

可选：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `PUBLIC_DASHBOARD_URL`
- `FEISHU_WEBHOOK_URL`
- `SMTP_HOST`
- `SMTP_PORT`

## GitHub Pages

仓库根目录包含 `index.html`。如果未自动开启 Pages，请手动设置：

```text
GitHub 仓库 -> Settings -> Pages -> Deploy from a branch -> main -> root
```

## 输出文件

- `data/latest.json`
- `output/briefing.md`
- `output/briefing.txt`
- `index.html`
- `output/error_report.txt`，本地错误报告，默认不提交

## 说明

本项目只生成医学科研文献筛选和人工审核前推文草稿，不自动发布公众号，不替代全文阅读和专业判断。
