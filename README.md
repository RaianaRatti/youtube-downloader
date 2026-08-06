# ytdl

A personal, local CLI for downloading audio and video from YouTube. Wraps
[yt-dlp](https://github.com/yt-dlp/yt-dlp) with presets, a config file, and a
small Typer-based CLI. Runs only on your own machine — see [PLAN.md](PLAN.md)
for the reasoning behind that (and why this intentionally isn't a hosted
service).

## Prerequisites

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) — required to merge video+audio streams and
  transcode audio (e.g. to mp3).
  ```
  brew install ffmpeg        # macOS
  sudo apt install ffmpeg    # Debian/Ubuntu
  ```

## Install

Recommended: install as an isolated global command with
[pipx](https://pipx.pypa.io/):

```
pipx install .
```

This makes `ytdl` available anywhere on your system without touching your
global Python packages. If `pipx` warns that `~/.local/bin` isn't on your
`PATH`, run `pipx ensurepath` and restart your shell (or open a new terminal
tab) before `ytdl` will be found.

### Development install

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```
# Download the best available video+audio (default) to ~/Downloads/ytdl
ytdl download https://www.youtube.com/watch?v=VIDEO_ID

# Download audio only, transcoded to mp3
ytdl download https://www.youtube.com/watch?v=VIDEO_ID --preset audio-mp3

# Choose a specific quality cap and output directory
ytdl download https://www.youtube.com/watch?v=VIDEO_ID --preset video-720p -o ~/Movies

# Download an entire playlist
ytdl download https://www.youtube.com/playlist?list=PLAYLIST_ID --playlist

# List available formats/qualities for a video without downloading
ytdl formats https://www.youtube.com/watch?v=VIDEO_ID
```

Available presets: `video-best` (default), `video-1080p`, `video-720p`,
`audio-best` (native format), `audio-mp3`.

## Configuration

Optional config file at `~/.config/ytdl/config.toml`:

```toml
output_dir = "~/Movies/ytdl"
default_preset = "audio-mp3"

# Only needed for age-gated or rate-limited videos:
cookies_from_browser = "chrome"
# or:
cookies_file = "~/cookies.txt"
```

CLI flags (`--preset`, `--output-dir`) always take precedence over the config
file.

## Troubleshooting

**Downloads suddenly start failing / "unable to extract" errors.** YouTube
changes its site frequently, which regularly breaks extraction until yt-dlp
is updated. Upgrade it:

```
pipx inject ytdl --force yt-dlp   # if installed via pipx
# or, in a dev install:
pip install -U yt-dlp
```

**Age-gated, members-only, or rate-limited videos fail.** Set
`cookies_from_browser` in the config file to a browser you're logged into
YouTube with (e.g. `"chrome"`, `"firefox"`, `"safari"`).

## Development

```
pip install -e ".[dev]"
pytest
ruff check .
```

Tests mock `yt_dlp.YoutubeDL` entirely — no real network calls are made
during the test suite.

## Project plan

See [PLAN.md](PLAN.md) for the full architecture, step-by-step build plan,
and the deployment decision (local-only tool, not a hosted service).
