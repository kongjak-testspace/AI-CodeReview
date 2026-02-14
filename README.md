# GitHub PR Code Review System
FastAPI webhook service that receives pull request events, runs a selected AI CLI review flow, and posts review output back to GitHub.

## Project Overview
- Trigger: `pull_request` events (`opened`, `synchronize`) with HMAC verification.
- Flow: webhook -> config select -> review pipeline -> inline + summary review comments.

## Config / Env Setup
- Create `.env` with: `GITHUB_TOKEN`, `WEBHOOK_SECRET`, `BOT_USERNAME`.
- Configure defaults and per-repo overrides in `config.yaml`.

## Local Run
- Install deps: `uv sync`
- Start server: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Health check: `curl -s http://127.0.0.1:8000/health`
- Webhook mock test: `bash scripts/test_webhook.sh`

## Docker Run
- Build and run: `docker compose up -d --build`
- Stop: `docker compose down`

## Webhook Setup Summary
- GitHub webhook URL: `http(s)://<host>/webhook`
- Content type: `application/json`, event: `Pull requests`
- Secret must match `WEBHOOK_SECRET`; invalid signatures return `403`.
- Bot-originated PRs (`sender.login == BOT_USERNAME`) are ignored.

## Supported CLIs
- Claude, Codex, Gemini, OpenCode, GitHub Copilot
