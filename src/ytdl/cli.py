"""Typer CLI: download audio/video from YouTube for personal use."""

from __future__ import annotations

from pathlib import Path

import typer

from ytdl.config import load_config
from ytdl.downloader import DownloadError, download_playlist, list_formats
from ytdl.downloader import download as run_download
from ytdl.presets import PRESETS, get_preset

app = typer.Typer(help="Download audio/video from YouTube for personal use.", no_args_is_help=True)


@app.command()
def download(
    url: str = typer.Argument(..., help="YouTube video or playlist URL"),
    preset: str | None = typer.Option(
        None,
        "--preset",
        "-p",
        help=f"Download preset. One of: {', '.join(sorted(PRESETS))}. "
        "Defaults to config or 'video-best'.",
    ),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Directory to save the file(s) to"
    ),
    playlist: bool = typer.Option(
        False, "--playlist", help="Download every video in the playlist, not just one"
    ),
) -> None:
    """Download a video (or playlist) as audio or video."""
    config = load_config()
    resolved_preset = preset or config.default_preset
    resolved_output_dir = output_dir or config.output_dir

    try:
        get_preset(resolved_preset)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    try:
        if playlist:
            paths = download_playlist(url, resolved_output_dir, resolved_preset)
            typer.echo(f"\nDownloaded {len(paths)} file(s) to {resolved_output_dir}")
            for path in paths:
                typer.echo(f"  {path}")
        else:
            path = run_download(url, resolved_output_dir, resolved_preset)
            typer.echo(f"\nSaved to: {path}")
    except DownloadError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def formats(url: str = typer.Argument(..., help="YouTube video URL")) -> None:
    """List available formats/qualities for a video without downloading."""
    try:
        available = list_formats(url)
    except DownloadError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"{'ID':<8}{'EXT':<6}{'RESOLUTION':<12}{'VCODEC':<16}{'ACODEC':<12}{'NOTE'}")
    for fmt in available:
        typer.echo(
            f"{fmt.format_id:<8}{fmt.ext:<6}{(fmt.resolution or '-'):<12}"
            f"{(fmt.vcodec or '-'):<16}{(fmt.acodec or '-'):<12}{fmt.note or ''}"
        )


if __name__ == "__main__":
    app()
