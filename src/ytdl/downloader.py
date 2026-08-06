"""Core download logic wrapping yt_dlp."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from ytdl.presets import get_preset

DEFAULT_FILENAME_TEMPLATE = "%(title)s [%(id)s].%(ext)s"

ProgressCallback = Callable[[str, "float | None", "str | None"], None]


class DownloadError(Exception):
    """Base error for failures the caller should be able to handle explicitly."""


class InvalidURLError(DownloadError):
    """The given URL isn't a resolvable/supported YouTube URL."""


class NoFormatsAvailableError(DownloadError):
    """yt-dlp couldn't find a format matching the requested preset."""


class NetworkError(DownloadError):
    """The download failed due to a network-level problem."""


@dataclass(frozen=True)
class FormatInfo:
    format_id: str
    ext: str
    resolution: str | None
    fps: float | None
    vcodec: str | None
    acodec: str | None
    filesize_approx: int | None
    note: str | None

    @classmethod
    def from_yt_dlp(cls, fmt: dict) -> FormatInfo:
        return cls(
            format_id=fmt.get("format_id", "?"),
            ext=fmt.get("ext", "?"),
            resolution=fmt.get("resolution"),
            fps=fmt.get("fps"),
            vcodec=fmt.get("vcodec"),
            acodec=fmt.get("acodec"),
            filesize_approx=fmt.get("filesize") or fmt.get("filesize_approx"),
            note=fmt.get("format_note"),
        )


class _SilentLogger:
    """Suppresses yt-dlp's own console output; we report errors via our own exceptions."""

    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass


def _default_progress_callback(status: str, percent: float | None, filename: str | None) -> None:
    if status == "downloading":
        pct = f"{percent:5.1f}%" if percent is not None else "  ?  %"
        print(f"\rDownloading... {pct}", end="", flush=True)
    elif status == "finished":
        print(f"\rDownload finished: {filename}")


def _build_ydl_opts(
    output_dir: Path,
    preset_name: str,
    filename_template: str,
    progress_callback: ProgressCallback | None,
) -> dict:
    preset = get_preset(preset_name)
    opts = preset.to_ydl_opts()
    opts["outtmpl"] = str(output_dir / filename_template)
    opts["quiet"] = True
    opts["no_warnings"] = True
    opts["logger"] = _SilentLogger()

    if progress_callback is not None:

        def hook(status: dict) -> None:
            if status["status"] == "downloading":
                total = status.get("total_bytes") or status.get("total_bytes_estimate")
                downloaded = status.get("downloaded_bytes", 0)
                percent = (downloaded / total * 100) if total else None
                progress_callback("downloading", percent, status.get("filename"))
            elif status["status"] == "finished":
                progress_callback("finished", 100.0, status.get("filename"))

        opts["progress_hooks"] = [hook]

    return opts


def _wrap_error(exc: Exception, url: str) -> DownloadError:
    message = str(exc).lower()
    if "unsupported url" in message or "is not a valid url" in message:
        return InvalidURLError(f"'{url}' is not a valid/supported YouTube URL")
    if "requested format is not available" in message:
        return NoFormatsAvailableError(
            f"No matching format found for '{url}' with the requested preset"
        )
    if any(term in message for term in ("urlopen error", "timed out", "connection", "network")):
        return NetworkError(f"Network error while downloading '{url}': {exc}")
    return DownloadError(str(exc))


def download(
    url: str,
    output_dir: Path,
    preset: str = "video-best",
    filename_template: str = DEFAULT_FILENAME_TEMPLATE,
    progress_callback: ProgressCallback | None = _default_progress_callback,
) -> Path:
    """Download a single video/audio per the given preset.

    Returns the path to the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    opts = _build_ydl_opts(output_dir, preset, filename_template, progress_callback)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise DownloadError(f"yt-dlp returned no info for '{url}'")

            requested = info.get("requested_downloads")
            if requested:
                return Path(requested[0]["filepath"])
            return Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as exc:
        raise _wrap_error(exc, url) from exc


def list_formats(url: str) -> list[FormatInfo]:
    """List available formats/qualities for a URL without downloading."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "logger": _SilentLogger(),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise _wrap_error(exc, url) from exc

    if info is None or "formats" not in info:
        raise DownloadError(f"No formats found for '{url}'")

    return [FormatInfo.from_yt_dlp(fmt) for fmt in info["formats"]]
