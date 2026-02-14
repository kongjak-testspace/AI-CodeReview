import asyncio
import logging
import shutil
import tempfile

from app.cli.base import get_adapter
from app.config import load_config
from app.github_client import GitHubClient
from app.parser import parse_review_output
from app.prompt import build_review_prompt


logger = logging.getLogger(__name__)
_semaphore = asyncio.Semaphore(3)


async def process_review(payload: dict, github_token: str) -> None:
    async with _semaphore:
        github_client: GitHubClient | None = None
        temp_dir = tempfile.mkdtemp(prefix="pr-review-")

        try:
            repository = payload.get("repository", {})
            pull_request = payload.get("pull_request", {})
            head = pull_request.get("head", {})

            owner = repository.get("owner", {}).get("login", "")
            repo = repository.get("name", "")
            pr_number = pull_request.get("number")
            commit_sha = head.get("sha", "")
            clone_url = head.get("repo", {}).get("clone_url", "")
            head_ref = head.get("ref", "")

            if not owner or not repo or not pr_number or not commit_sha:
                raise ValueError("Missing owner/repo/pr_number/commit_sha in payload")
            if not clone_url or not head_ref:
                raise ValueError("Missing clone_url/head_ref in payload")

            app_config = load_config()
            repo_config = app_config.get_repo_config(f"{owner}/{repo}")

            github_client = GitHubClient(github_token)

            await github_client.clone_repo(clone_url, head_ref, temp_dir)
            diff = await github_client.get_pr_diff(owner, repo, pr_number)
            prompt = build_review_prompt(diff, repo_config.language)

            adapter = get_adapter(repo_config.cli)
            raw_output = await adapter.run_review(prompt, temp_dir, repo_config.timeout)
            result = parse_review_output(raw_output)

            await github_client.post_review(
                owner,
                repo,
                pr_number,
                commit_sha,
                result.summary,
                [comment.model_dump() for comment in result.comments],
            )
            logger.info(f"Posted review for {owner}/{repo}#{pr_number}")
        except Exception as exc:
            logger.error(f"Review orchestration failed: {exc}", exc_info=True)
        finally:
            if github_client is not None:
                try:
                    await github_client.close()
                except Exception as exc:
                    logger.error(f"Failed to close GitHub client: {exc}", exc_info=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
