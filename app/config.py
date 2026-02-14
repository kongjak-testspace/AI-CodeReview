import yaml
from pathlib import Path
from pydantic import BaseModel, Field


class RepoConfig(BaseModel):
    """Per-repository configuration for code review settings."""

    cli: str = "claude"  # claude, codex, gemini, opencode, copilot
    fallback_cli: list[str] = Field(
        default_factory=lambda: ["codex", "gemini", "copilot"]
    )
    review_mode: str = "single"  # "single" = fallback chain, "multi" = all CLIs in parallel + synthesis
    synthesizer_cli: str = "claude"  # CLI used to synthesize multiple reviews into one
    language: str = "en"
    timeout: int = 600  # seconds
    max_budget_usd: float = 1.0  # Claude only


class AppConfig(BaseModel):
    """Application-level configuration with per-repo overrides."""

    repos: dict[str, RepoConfig] = Field(default_factory=dict)
    default: RepoConfig = Field(default_factory=RepoConfig)

    def get_repo_config(self, full_name: str) -> RepoConfig:
        """Get repo-specific config, or default if not configured."""
        return self.repos.get(full_name, self.default)


def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Load configuration from YAML file.
    Falls back to default config if file doesn't exist or is empty.
    """
    config_path = Path(path)

    if not config_path.exists():
        # File doesn't exist → return default config
        return AppConfig()

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle empty YAML file
        if data is None:
            return AppConfig()

        return AppConfig(**data)
    except Exception:
        # On any parsing error, return default config
        return AppConfig()
