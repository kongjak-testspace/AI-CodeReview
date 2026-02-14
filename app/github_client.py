"""GitHub API client for cloning repos, fetching diffs, and posting reviews."""

import asyncio
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class GitHubClient:
    """Async GitHub API client for PR code review operations."""

    def __init__(self, token: str) -> None:
        """Initialize client with GitHub token.

        Args:
            token: GitHub personal access token or bot token
        """
        self.token = token
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def clone_repo(self, clone_url: str, ref: str, target_dir: str) -> None:
        """Clone repository and checkout specific ref.

        Args:
            clone_url: Git clone URL (https://github.com/owner/repo.git)
            ref: Branch or commit ref to checkout
            target_dir: Target directory for clone

        Raises:
            RuntimeError: If git commands fail
        """
        # Clone with depth 50 for Codex compatibility
        clone_proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "50",
            "--no-single-branch",
            clone_url,
            target_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await clone_proc.communicate()

        if clone_proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown git clone error"
            logger.error(f"git clone failed: {error_msg}")
            raise RuntimeError(f"git clone failed: {error_msg}")

        # Checkout target ref
        checkout_proc = await asyncio.create_subprocess_exec(
            "git",
            "checkout",
            ref,
            cwd=target_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await checkout_proc.communicate()

        if checkout_proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown git checkout error"
            logger.error(f"git checkout failed: {error_msg}")
            raise RuntimeError(f"git checkout failed: {error_msg}")

        logger.info(f"Cloned {clone_url} to {target_dir} and checked out {ref}")

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetch PR unified diff.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Unified diff text

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        response = await self.client.get(
            url,
            headers={"Accept": "application/vnd.github.diff"},
        )
        response.raise_for_status()
        diff_text = response.text
        logger.info(f"Fetched diff for PR #{pr_number} ({len(diff_text)} bytes)")
        return diff_text

    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_sha: str,
        summary: str,
        comments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Post code review with inline comments.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            commit_sha: Commit SHA to review
            summary: Review summary body
            comments: List of inline comments with path, line, body, side

        Returns:
            API response JSON

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

        # Map comments to GitHub API format with side: RIGHT
        api_comments = [
            {
                "path": comment["path"],
                "line": comment["line"],
                "body": comment["body"],
                "side": "RIGHT",
            }
            for comment in comments
        ]

        payload = {
            "commit_id": commit_sha,
            "body": summary,
            "event": "COMMENT",
            "comments": api_comments,
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"Posted review to PR #{pr_number}: {len(api_comments)} comments, "
            f"summary length {len(summary)}"
        )
        return result

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()
        logger.info("GitHubClient closed")
