import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from app.reviewer import process_review
from app.webhook import verify_github_signature

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GitHub PR Code Review System")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
BOT_USERNAME = "github-actions[bot]"


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    await verify_github_signature(request, WEBHOOK_SECRET)

    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "pull_request":
        return {"status": "ignored", "reason": "not a pull_request event"}

    payload = await request.json()

    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"action '{action}' not handled"}

    sender_login = payload.get("sender", {}).get("login", "")
    if sender_login == BOT_USERNAME:
        return {"status": "ignored", "reason": "bot PR excluded"}

    github_token = request.headers.get("X-GitHub-Token", "")
    if not github_token:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Token header")

    pr_number = payload.get("pull_request", {}).get("number")
    if not pr_number:
        raise HTTPException(status_code=400, detail="Missing pull_request.number")

    await process_review(payload, github_token)

    return {"status": "reviewed", "pr": pr_number}
