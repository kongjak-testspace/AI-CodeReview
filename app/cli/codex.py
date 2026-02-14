import uuid
import os
from app.cli.base import CLIAdapter


class CodexAdapter(CLIAdapter):
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        output_file = f"/tmp/codex_output_{uuid.uuid4().hex}.txt"
        return [
            "codex",
            "exec",
            prompt,
            "--sandbox",
            "read-only",
            "--output-last-message",
            output_file,
        ]

    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        cmd = self.build_command(prompt, cwd)
        output_file = cmd[-1]

        await self._execute(cmd, cwd, timeout)

        try:
            with open(output_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
