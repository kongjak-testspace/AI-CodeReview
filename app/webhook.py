import hmac
import hashlib
from fastapi import Request, HTTPException


async def verify_github_signature(request: Request, secret: str) -> None:
    """Verify GitHub webhook signature using HMAC-SHA256.

    Args:
        request: FastAPI request object
        secret: Webhook secret for HMAC computation

    Raises:
        HTTPException: 403 if signature is invalid or missing
    """
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Parse signature (format: "sha256=<hex_digest>")
    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Invalid signature format")

    expected_signature = signature_header[7:]  # Remove "sha256=" prefix

    # Get raw request body
    body = await request.body()

    # Compute HMAC-SHA256
    computed_signature = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    # Timing-safe comparison
    if not hmac.compare_digest(computed_signature, expected_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
