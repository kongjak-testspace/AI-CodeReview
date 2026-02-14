# GitHub PR Code Review System
FastAPI webhook service that receives pull request events, runs a selected AI CLI review flow, and posts review output back to GitHub.

## Project Overview
- Trigger: `pull_request` events (`opened`, `synchronize`) with HMAC verification.
- Flow: webhook -> config select -> review pipeline -> inline + summary review comments.

## Config / Env Setup
- Create `.env` with: `WEBHOOK_SECRET`.
- GitHub token is passed per-request from the Actions workflow (`github.token`), so no PAT needed.
- Reviews are posted as `github-actions[bot]`.
- Configure defaults and per-repo overrides in `config.yaml`.

## Prerequisites
Install the AI CLI tools you want to use on the host machine:
- **Claude**: `curl -fsSL https://claude.ai/install.sh | bash`
- **Codex**: `npm install -g @openai/codex`
- **Gemini**: `npm install -g @google/gemini-cli`
- **GitHub Copilot**: `gh extension install github/gh-copilot`

Each CLI must be authenticated (OAuth) before running the server.

## Deployment

### Install dependencies
```bash
uv sync
```

### Run directly
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Run as systemd service
```bash
sudo cp code-review.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now code-review
sudo systemctl status code-review
```

### Reverse proxy (nginx)
Copy `nginx/review.kongjak.dev.conf` to `/etc/nginx/sites-enabled/` and reload nginx.

## GitHub Actions Trigger
Copy `.github/workflows/code-review.yml` into each target repo. Add these repository secrets:
- `WEBHOOK_SECRET`: Must match the server's `WEBHOOK_SECRET` env var.
- `REVIEW_SERVER_URL`: Your server URL, e.g. `https://review.kongjak.dev`.

The workflow fires on `pull_request` (`opened`, `synchronize`), computes HMAC, and forwards the event payload along with `github.token` to your server. Reviews are posted as `github-actions[bot]`.

## Supported CLIs
- Claude, Codex, Gemini, OpenCode, GitHub Copilot
