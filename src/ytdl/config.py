"""Default settings and config file loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "ytdl"
DEFAULT_PRESET = "video-best"
CONFIG_DIR = Path.home() / ".config" / "ytdl"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass(frozen=True)
class Config:
    output_dir: Path = DEFAULT_OUTPUT_DIR
    default_preset: str = DEFAULT_PRESET
    cookies_from_browser: str | None = None
    cookies_file: Path | None = None


def load_config(config_path: Path = CONFIG_FILE) -> Config:
    """Load config from a TOML file, falling back to defaults for any missing keys.

    Returns plain defaults if the file doesn't exist.
    """
    config = Config()
    if not config_path.exists():
        return config

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    overrides: dict = {}
    if "output_dir" in data:
        overrides["output_dir"] = Path(data["output_dir"]).expanduser()
    if "default_preset" in data:
        overrides["default_preset"] = data["default_preset"]
    if "cookies_from_browser" in data:
        overrides["cookies_from_browser"] = data["cookies_from_browser"]
    if "cookies_file" in data:
        overrides["cookies_file"] = Path(data["cookies_file"]).expanduser()

    return replace(config, **overrides)
