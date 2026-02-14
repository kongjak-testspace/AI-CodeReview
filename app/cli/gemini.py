import json
from app.cli.base import CLIAdapter


class GeminiAdapter(CLIAdapter):
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        return [
            "gemini",
            "-p",
            prompt,
            "-o",
            "json",
            "--approval-mode",
            "plan",
        ]

    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        cmd = self.build_command(prompt, cwd)
        raw_output = await self._execute(cmd, cwd, timeout)

        try:
            data = json.loads(raw_output)
            return data.get("response", raw_output)
        except json.JSONDecodeError:
            return raw_output
