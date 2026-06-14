"""Configuration management for Lumiere."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LumiereConfig:
    """Central configuration for Lumiere."""

    # API
    api_base_url: str = "https://api.balloonerismm.workers.dev"

    # Scan defaults
    min_rating: float = 6.5
    max_pages: int = 500
    language: Optional[str] = None
    year_start: Optional[str] = None
    year_end: Optional[str] = None

    # Sort strategies
    sort_methods: list = field(default_factory=lambda: [
        "popularity.desc",
        "vote_average.desc",
        "release_date.desc",
        "vote_count.desc",
    ])

    # Output
    output_dir: str = "."

    # Rotten Tomatoes
    rt_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

    @classmethod
    def from_env(cls) -> "LumiereConfig":
        """Load config from environment / .env file."""
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

        cfg = cls()
        if os.environ.get("BALLOONERISM_API_URL"):
            cfg.api_base_url = os.environ["BALLOONERISM_API_URL"]
        if os.environ.get("DEFAULT_MIN_RATING"):
            cfg.min_rating = float(os.environ["DEFAULT_MIN_RATING"])
        if os.environ.get("DEFAULT_MAX_PAGES"):
            cfg.max_pages = int(os.environ["DEFAULT_MAX_PAGES"])
        if os.environ.get("DEFAULT_LANGUAGE"):
            cfg.language = os.environ["DEFAULT_LANGUAGE"] or None
        if os.environ.get("DEFAULT_YEAR_START"):
            cfg.year_start = os.environ["DEFAULT_YEAR_START"] or None
        if os.environ.get("RT_USER_AGENT"):
            cfg.rt_user_agent = os.environ["RT_USER_AGENT"]
        return cfg
