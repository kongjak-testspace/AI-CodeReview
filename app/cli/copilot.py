from app.cli.base import CLIAdapter


class CopilotAdapter(CLIAdapter):
    def build_command(self, prompt: str, cwd: str) -> list[str]:
        return [
            "gh",
            "copilot",
            "--",
            "-p",
            prompt,
            "--allow-all-tools",
        ]

    async def run_review(self, prompt: str, cwd: str, timeout: int) -> str:
        cmd = self.build_command(prompt, cwd)
        return await self._execute(cmd, cwd, timeout)
