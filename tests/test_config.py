import textwrap
from pathlib import Path

from ytdl.config import DEFAULT_OUTPUT_DIR, DEFAULT_PRESET, Config, load_config


def test_load_config_missing_file_returns_defaults(tmp_path):
    config = load_config(tmp_path / "does-not-exist.toml")
    assert config == Config()
    assert config.output_dir == DEFAULT_OUTPUT_DIR
    assert config.default_preset == DEFAULT_PRESET
    assert config.cookies_from_browser is None
    assert config.cookies_file is None


def test_load_config_overrides_only_present_keys(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        textwrap.dedent("""\
            output_dir = "~/Movies/ytdl-test"
            default_preset = "audio-mp3"
        """)
    )
    config = load_config(config_file)
    assert config.output_dir == Path.home() / "Movies" / "ytdl-test"
    assert config.default_preset == "audio-mp3"
    assert config.cookies_from_browser is None
    assert config.cookies_file is None


def test_load_config_all_keys(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        textwrap.dedent("""\
            output_dir = "/tmp/out"
            default_preset = "video-720p"
            cookies_from_browser = "firefox"
            cookies_file = "~/cookies.txt"
        """)
    )
    config = load_config(config_file)
    assert config.output_dir == Path("/tmp/out")
    assert config.default_preset == "video-720p"
    assert config.cookies_from_browser == "firefox"
    assert config.cookies_file == Path.home() / "cookies.txt"
