import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CLIAdapter(ABC):
    @abstractmethod
    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        """Execute CLI with prompt and return raw output"""
        ...

    @abstractmethod
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        """Build CLI command arguments"""
        ...

    async def _execute(
        self, cmd: list[str], cwd: str, timeout: int, stdin: str | None = None
    ) -> str:
        """Common executor for subprocess with timeout and capture"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=stdin.encode() if stdin else None),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"CLI timeout after {timeout}s: {cmd[0]}")
                proc.kill()
                await proc.wait()
                raise

            if proc.returncode != 0:
                logger.error(f"CLI failed: {cmd[0]}, stderr: {stderr.decode()}")

            return stdout.decode() + stderr.decode()

        except Exception as e:
            logger.error(f"CLI execution error: {cmd[0]}, {e}")
            raise


def get_adapter(cli_name: str) -> CLIAdapter:
    """Factory function to get CLI adapter by name"""
    from app.cli.claude import ClaudeAdapter
    from app.cli.codex import CodexAdapter
    from app.cli.gemini import GeminiAdapter
    from app.cli.opencode import OpenCodeAdapter
    from app.cli.copilot import CopilotAdapter

    adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "gemini": GeminiAdapter,
        "opencode": OpenCodeAdapter,
        "copilot": CopilotAdapter,
    }

    if cli_name not in adapters:
        raise ValueError(f"Unknown CLI: {cli_name}")

    return adapters[cli_name]()
