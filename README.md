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

## GitHub Actions Trigger (Recommended)
Instead of configuring webhooks manually, copy `.github/workflows/code-review.yml` into each target repo. Add these repository secrets:
- `WEBHOOK_SECRET`: Must match the server's `WEBHOOK_SECRET` env var.
- `REVIEW_SERVER_URL`: Your server URL, e.g. `https://review.example.com`.

The workflow fires on `pull_request` (`opened`, `synchronize`), computes HMAC, and POSTs the event payload to your server.

## Manual Webhook Setup (Alternative)
- GitHub webhook URL: `http(s)://<host>/webhook`
- Content type: `application/json`, event: `Pull requests`
- Secret must match `WEBHOOK_SECRET`; invalid signatures return `403`.
- Bot-originated PRs (`sender.login == BOT_USERNAME`) are ignored.

## Supported CLIs
- Claude, Codex, Gemini, OpenCode, GitHub Copilot
