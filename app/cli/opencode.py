import json
from app.cli.base import CLIAdapter


class OpenCodeAdapter(CLIAdapter):
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        return [
            "opencode",
            "run",
            prompt,
            "--format",
            "json",
        ]

    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        cmd = self.build_command(prompt, cwd)
        raw_output = await self._execute(cmd, cwd, timeout)

        lines = raw_output.strip().split("\n")
        text_parts = []

        for line in lines:
            try:
                event = json.loads(line)
                if event.get("type") == "text" and "part" in event:
                    text_parts.append(event["part"].get("text", ""))
            except json.JSONDecodeError:
                continue

        return "".join(text_parts) if text_parts else raw_output
