import json
from app.cli.base import CLIAdapter


class ClaudeAdapter(CLIAdapter):
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        return [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--max-budget-usd",
            "1.0",
            "--dangerously-skip-permissions",
        ]

    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        cmd = self.build_command(prompt, cwd)
        raw_output = await self._execute(cmd, cwd, timeout)

        try:
            data = json.loads(raw_output)
            return data.get("result", raw_output)
        except json.JSONDecodeError:
            return raw_output
