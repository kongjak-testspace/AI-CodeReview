import os
import logging
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from dotenv import load_dotenv

from app.webhook import verify_github_signature

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="GitHub PR Code Review System")

# Environment variables
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


async def placeholder_review_task(payload: dict):
    """Placeholder background task for review processing.

    This will be replaced with actual reviewer orchestration in Task 7.
    """
    logger.info(
        f"Placeholder: queued review for PR #{payload['pull_request']['number']}"
    )


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events for pull requests.

    Only processes pull_request events with actions: opened, synchronize.
    Ignores PRs created by the bot account.
    """
    # Verify HMAC signature
    await verify_github_signature(request, WEBHOOK_SECRET)

    # Check event type
    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "pull_request":
        return {"status": "ignored", "reason": "not a pull_request event"}

    # Parse payload
    payload = await request.json()

    # Check action
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"action '{action}' not handled"}

    # Check if PR is from bot account
    sender_login = payload.get("sender", {}).get("login", "")
    if sender_login == BOT_USERNAME:
        return {"status": "ignored", "reason": "bot PR excluded"}

    # Extract PR number
    pr_number = payload.get("pull_request", {}).get("number")
    if not pr_number:
        raise HTTPException(status_code=400, detail="Missing pull_request.number")

    # Queue background review task
    background_tasks.add_task(placeholder_review_task, payload)

    return {"status": "queued", "pr": pr_number}
