# YouTube Audio/Video Downloader — Plan

> **Status: implemented.** All 8 steps below are done and verified (real downloads, real `pipx install .`, 30 passing tests). See [README.md](README.md) for usage.

## Goal
A local CLI tool to download audio and video from YouTube videos to your computer, for personal use.

> **Note on legality:** YouTube's Terms of Service prohibit downloading content unless YouTube provides a download button/link for it. This is built as a personal-use, locally-run tool (not a public/hosted service) — see **Deployment** below for why that distinction matters.

## Decision: Option A — Personal Local Tool
Runs only on your own machine via `pipx`/`pip`. No server, no public exposure, no auth needed. If remote access is ever wanted later, that's a follow-up (e.g. Tailscale + the optional web UI), not part of this build.

## Core Approach
Wrap **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** (actively maintained extraction engine) rather than reimplementing YouTube extraction. It handles format selection, stream muxing, retries, and YouTube's frequent changes. This repo's job is UX: CLI, presets, file organization, packaging.

**System dependency:** `ffmpeg` must be installed separately (`brew install ffmpeg` on macOS) — used to merge separate video/audio streams and transcode audio (e.g. to mp3).

## Tech Stack
| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Download engine | `yt-dlp` (used as a library) |
| Muxing/transcoding | `ffmpeg` (system dependency) |
| CLI framework | `typer` |
| Packaging | `pyproject.toml`, installable via `pipx install .` |
| Tests | `pytest` |
| Lint/format | `ruff` |

## Repo Structure
```
youtube-downloader/
├── PLAN.md
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── yoink/
│       ├── __init__.py
│       ├── cli.py            # Typer app: download, formats commands
│       ├── downloader.py     # wraps yt_dlp.YoutubeDL, builds options, runs download
│       ├── presets.py        # named quality/format presets
│       └── config.py         # default output dir, config file loading
├── tests/
│   ├── test_presets.py       # preset -> yt-dlp opts mapping
│   ├── test_config.py        # default + TOML config loading
│   ├── test_downloader.py    # option-building logic, mocked yt-dlp
│   └── test_cli.py           # CLI argument parsing, mocked downloader
└── downloads/                # default output dir (gitignored, kept via .gitkeep)
```

## Step-by-Step Execution Plan

### Step 1 — Scaffold the project
- `pyproject.toml` with project metadata, dependencies (`yt-dlp`, `typer`), dev deps (`pytest`, `ruff`).
- `.gitignore` (Python + `downloads/`).
- Empty package layout under `src/yoink/`.
- Verify `ffmpeg` is installed on the dev machine.

### Step 2 — `presets.py`: format presets
Define named presets mapping to yt-dlp `format` strings:
- `video-best` → best available video+audio, merged
- `video-1080p`, `video-720p` → capped resolution
- `audio-best` → best audio, extracted
- `audio-mp3` → best audio, extracted + transcoded to mp3 via postprocessor

### Step 3 — `downloader.py`: core download logic
- `download(url: str, output_dir: Path, preset: str, filename_template: str) -> Path`
- Builds `yt_dlp.YoutubeDL` options from the chosen preset (`format`, `outtmpl`, `postprocessors`, `merge_output_format`).
- Progress hook that prints/reports percent complete and final file path.
- `list_formats(url: str) -> list[FormatInfo]` for inspecting available streams before choosing.
- Raise clear, typed errors on failure (invalid URL, no formats available, network error) rather than letting raw yt-dlp exceptions bubble up.
- *(Implemented)* Also added `download_playlist()` for the Step 5 `--playlist` flag, with `noplaylist=True` forced on single-video downloads so a stray `&list=` in a pasted URL doesn't silently pull the whole playlist.

### Step 4 — `config.py`: defaults
- Default output directory (`~/Downloads/yoink` or configurable via `~/.config/yoink/config.toml`).
- Optional: path to a cookies file/browser for age-gated or rate-limited videos (`--cookies-from-browser`).

### Step 5 — `cli.py`: CLI commands
Using `typer`:
```
yoink download <url> [--preset audio-mp3] [--output-dir PATH]
yoink formats <url>              # list available formats/qualities for a URL
yoink download <url> --playlist  # download an entire playlist
```
- Sensible defaults so `yoink download <url>` alone "just works" (best video+audio to default dir).
- Clear progress output (percent, speed, ETA) and a final printed path to the saved file.

### Step 6 — Tests
- Mock `yt_dlp.YoutubeDL` entirely — never hit real YouTube in tests (fragile, ToS-sensitive, slow).
- Test: preset → options mapping, CLI arg parsing/defaults, error handling paths.
- *(Implemented)* 30 tests across `test_presets.py`, `test_config.py`, `test_downloader.py`, `test_cli.py` — all passing, zero real network calls.

### Step 7 — Packaging & install
- `pipx install .` (or `pip install -e .` for dev) so `yoink` is available as a global command.
- README: install steps, `ffmpeg` prerequisite, usage examples, troubleshooting (e.g. "downloads failing → `pip install -U yt-dlp`", since YouTube changes break extraction periodically).
- *(Implemented)* Verified live: `pipx install .` builds and installs correctly; the resulting global `yoink` binary was exercised against a real YouTube URL. Note: `pipx` puts binaries in `~/.local/bin`, which may need `pipx ensurepath` (or a manual `PATH` edit) to be on your shell's `PATH`.

### Step 8 — Maintenance note
Pin a minimum `yt-dlp` version but expect to bump it often — document `pipx upgrade yoink-deps`-style guidance (or just "reinstall/upgrade yt-dlp") as the standard fix when downloads start failing.

## Deployment
Personal local tool only (Option A) — installed and run on your own machine via `pipx`/`pip`, no server component, no public exposure. A public/hosted deployment was considered and intentionally ruled out: it would function as a redistribution service (YouTube ToS/DMCA exposure) and fights YouTube's blocking of cloud/datacenter IPs. If remote access from another device is wanted later, the lightweight extension is a localhost-bound web UI reachable only over a private mesh network (e.g. Tailscale) — not a publicly addressable deployment.

## Milestones
- [x] Step 1 — scaffold repo, `pyproject.toml`, verify `ffmpeg`
- [x] Step 2 — `presets.py`
- [x] Step 3 — `downloader.py`
- [x] Step 4 — `config.py`
- [x] Step 5 — `cli.py` with `download` and `formats` commands (plus `--playlist`)
- [x] Step 6 — tests (30 passing, mocked yt-dlp)
- [x] Step 7 — packaging + README (verified via real `pipx install .`)
- [x] Manual end-to-end test: downloaded a real video as both mp3 (audio-mp3 preset) and via `formats`/`list_formats` — confirmed working
