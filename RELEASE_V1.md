# Neurosurgery Literature Radar V1

## V1 功能说明

V1 是神外/脑损伤/脑积水/干细胞/外泌体文献日报收集器，支持每日自动检索：

- PubMed
- bioRxiv
- medRxiv
- arXiv

聚焦主题：

- traumatic brain injury / TBI
- hydrocephalus / normal pressure hydrocephalus / iNPH
- stem cell / mesenchymal stem cell
- exosome / extracellular vesicles
- microglia / TREM2 / Cystatin C / CST3
- neuroinflammation
- glioma / glioblastoma / spinal cord tumor
- neurosurgery general

## 本地运行命令

```bash
cd ~/AIProjects/neurosurgery-literature-radar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_daily.py --no-email
```

## 本地检查命令

```bash
bash scripts/check_v1.sh
```

## 邮件测试命令

```bash
SMTP_USER=lipengtao12@gmail.com \
SMTP_APP_PASSWORD="你的 Gmail 应用专用密码" \
EMAIL_TO=lipengtao12@gmail.com \
bash scripts/test_email.sh
```

## GitHub Secrets 配置说明

建议配置：

- `SMTP_USER=lipengtao12@gmail.com`
- `SMTP_APP_PASSWORD=Gmail 应用专用密码`
- `EMAIL_TO=lipengtao12@gmail.com`
- `EMAIL_FROM=lipengtao12@gmail.com`
- `OPENAI_API_KEY=可选`
- `OPENAI_MODEL=gpt-4.1-mini`
- `PUBLIC_DASHBOARD_URL=https://LPT111.github.io/neurosurgery-literature-radar/`
- `FEISHU_WEBHOOK_URL=可选`

## Gmail App Password 注意事项

Gmail SMTP 必须使用 Google 账号的应用专用密码。不要使用普通登录密码，不要把密码写入代码或提交到 GitHub。

## 输出文件说明

- `data/latest.json`：结构化日报数据
- `output/briefing.md`：Markdown 早报
- `output/briefing.txt`：纯文本早报
- `index.html`：GitHub Pages 展示页面
- `output/error_report.txt`：错误报告，本地保留，不提交

## 发布记录

- `v1.0.0`：首次公开发布。每日 07:40 北京时间自动检索并生成文献日报，支持 Gmail 邮件推送和 GitHub Pages 展示。

## 后续 V1.1 计划

1. 每日两更
2. 多 cron fallback
3. 邮件/飞书 push-state 去重
4. PubMed 文章类型识别
5. 中文推文模板增强
6. 支持按主题单独订阅
7. 支持周报
