import asyncio
import logging
import shutil
import tempfile

from app.cli.base import get_adapter
from app.config import RepoConfig, load_config
from app.github_client import GitHubClient
from app.parser import parse_review_output
from app.prompt import build_review_prompt, build_synthesis_prompt


logger = logging.getLogger(__name__)
_semaphore = asyncio.Semaphore(3)


async def _run_single_cli(
    cli_name: str,
    prompt: str,
    cwd: str,
    timeout: int,
    owner: str,
    repo: str,
    pr_number: int,
) -> str | None:
    try:
        adapter = get_adapter(cli_name)
        output = await adapter.run_review(prompt, cwd, timeout)
        logger.info(f"CLI '{cli_name}' succeeded for {owner}/{repo}#{pr_number}")
        return output
    except Exception as exc:
        logger.warning(f"CLI '{cli_name}' failed for {owner}/{repo}#{pr_number}: {exc}")
        return None


async def _review_single_mode(
    repo_config: RepoConfig,
    prompt: str,
    cwd: str,
    owner: str,
    repo: str,
    pr_number: int,
) -> str:
    cli_order = [repo_config.cli] + [
        c for c in repo_config.fallback_cli if c != repo_config.cli
    ]

    for cli_name in cli_order:
        raw_output = await _run_single_cli(
            cli_name, prompt, cwd, repo_config.timeout, owner, repo, pr_number
        )
        if raw_output is not None:
            return raw_output

    raise RuntimeError(f"All CLIs failed for {owner}/{repo}#{pr_number}")


async def _review_multi_mode(
    repo_config: RepoConfig,
    prompt: str,
    diff: str,
    cwd: str,
    owner: str,
    repo: str,
    pr_number: int,
) -> str:
    all_clis = list(dict.fromkeys([repo_config.cli] + repo_config.fallback_cli))

    tasks = [
        _run_single_cli(
            cli_name, prompt, cwd, repo_config.timeout, owner, repo, pr_number
        )
        for cli_name in all_clis
    ]
    results = await asyncio.gather(*tasks)

    successful: dict[str, str] = {}
    for cli_name, output in zip(all_clis, results):
        if output is not None:
            successful[cli_name] = output

    if not successful:
        raise RuntimeError(
            f"All CLIs failed in multi-mode for {owner}/{repo}#{pr_number}"
        )

    if len(successful) == 1:
        logger.info(
            f"Only 1 CLI succeeded in multi-mode for {owner}/{repo}#{pr_number}, skipping synthesis"
        )
        return next(iter(successful.values()))

    logger.info(
        f"Synthesizing {len(successful)} reviews ({', '.join(successful.keys())}) "
        f"for {owner}/{repo}#{pr_number}"
    )
    synthesis_prompt = build_synthesis_prompt(successful, diff, repo_config.language)

    synthesizer = get_adapter(repo_config.synthesizer_cli)
    try:
        return await synthesizer.run_review(synthesis_prompt, cwd, repo_config.timeout)
    except Exception as exc:
        logger.warning(
            f"Synthesizer '{repo_config.synthesizer_cli}' failed: {exc}. "
            f"Falling back to longest individual review."
        )
        return max(successful.values(), key=len)


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

            if repo_config.review_mode == "multi":
                raw_output = await _review_multi_mode(
                    repo_config, prompt, diff, temp_dir, owner, repo, pr_number
                )
            else:
                raw_output = await _review_single_mode(
                    repo_config, prompt, temp_dir, owner, repo, pr_number
                )

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
