from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ytdl.cli import app
from ytdl.config import Config
from ytdl.downloader import DownloadError, FormatInfo

runner = CliRunner()


def test_download_command_uses_config_defaults(tmp_path):
    with (
        patch(
            "ytdl.cli.load_config",
            return_value=Config(output_dir=tmp_path, default_preset="audio-mp3"),
        ),
        patch("ytdl.cli.run_download", return_value=tmp_path / "out.mp3") as mock_download,
    ):
        result = runner.invoke(app, ["download", "https://youtu.be/x"])

    assert result.exit_code == 0
    assert "Saved to" in result.output
    mock_download.assert_called_once_with("https://youtu.be/x", tmp_path, "audio-mp3")


def test_download_command_cli_flags_override_config(tmp_path):
    with (
        patch(
            "ytdl.cli.load_config",
            return_value=Config(output_dir=Path("/default"), default_preset="video-best"),
        ),
        patch("ytdl.cli.run_download", return_value=tmp_path / "out.mp4") as mock_download,
    ):
        result = runner.invoke(
            app,
            ["download", "https://youtu.be/x", "--preset", "video-720p", "--output-dir", str(tmp_path)],
        )

    assert result.exit_code == 0
    mock_download.assert_called_once_with("https://youtu.be/x", tmp_path, "video-720p")


def test_download_command_playlist_flag_calls_download_playlist(tmp_path):
    with (
        patch(
            "ytdl.cli.load_config",
            return_value=Config(output_dir=tmp_path, default_preset="video-best"),
        ),
        patch(
            "ytdl.cli.download_playlist",
            return_value=[tmp_path / "1.mp4", tmp_path / "2.mp4"],
        ) as mock_pl,
    ):
        result = runner.invoke(app, ["download", "https://youtu.be/x", "--playlist"])

    assert result.exit_code == 0
    assert "Downloaded 2 file(s)" in result.output
    mock_pl.assert_called_once_with("https://youtu.be/x", tmp_path, "video-best")


def test_download_command_unknown_preset_exits_nonzero():
    with patch("ytdl.cli.load_config", return_value=Config()):
        result = runner.invoke(app, ["download", "https://youtu.be/x", "--preset", "bogus"])

    assert result.exit_code == 1
    assert "Unknown preset" in result.output


def test_download_command_reports_download_error(tmp_path):
    with (
        patch("ytdl.cli.load_config", return_value=Config(output_dir=tmp_path)),
        patch("ytdl.cli.run_download", side_effect=DownloadError("boom")),
    ):
        result = runner.invoke(app, ["download", "https://youtu.be/x"])

    assert result.exit_code == 1
    assert "Error: boom" in result.output


def test_formats_command_lists_formats():
    fake_formats = [
        FormatInfo(
            format_id="137",
            ext="mp4",
            resolution="1920x1080",
            fps=30.0,
            vcodec="avc1",
            acodec="none",
            filesize_approx=123456,
            note="1080p",
        )
    ]
    with patch("ytdl.cli.list_formats", return_value=fake_formats):
        result = runner.invoke(app, ["formats", "https://youtu.be/x"])

    assert result.exit_code == 0
    assert "137" in result.output
    assert "1920x1080" in result.output


def test_formats_command_reports_error():
    with patch("ytdl.cli.list_formats", side_effect=DownloadError("no such video")):
        result = runner.invoke(app, ["formats", "https://youtu.be/x"])

    assert result.exit_code == 1
    assert "Error: no such video" in result.output
