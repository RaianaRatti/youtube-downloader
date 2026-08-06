from unittest.mock import patch

import pytest
import yt_dlp

from yoink.downloader import (
    DownloadError,
    InvalidURLError,
    NetworkError,
    NoFormatsAvailableError,
    download,
    download_playlist,
    list_formats,
)


def _mock_ydl(mock_cls):
    """Return the object that `with yt_dlp.YoutubeDL(opts) as ydl:` binds to."""
    return mock_cls.return_value.__enter__.return_value


def test_download_returns_path_from_requested_downloads(tmp_path):
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {
            "id": "abc123",
            "ext": "mp4",
            "requested_downloads": [{"filepath": str(tmp_path / "video.mp4")}],
        }

        result = download(
            "https://youtu.be/abc123", tmp_path, preset="video-best", progress_callback=None
        )

    assert result == tmp_path / "video.mp4"
    opts = mock_cls.call_args.args[0]
    assert opts["format"] == "bestvideo+bestaudio/best"
    assert opts["noplaylist"] is True
    assert str(tmp_path) in opts["outtmpl"]


def test_download_falls_back_to_prepare_filename(tmp_path):
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {"id": "abc123", "ext": "mp3"}
        mock_ydl.prepare_filename.return_value = str(tmp_path / "audio.mp3")

        result = download(
            "https://youtu.be/abc123", tmp_path, preset="audio-mp3", progress_callback=None
        )

    assert result == tmp_path / "audio.mp3"


def test_download_raises_if_info_is_none(tmp_path):
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = None

        with pytest.raises(DownloadError, match="no info"):
            download("https://youtu.be/abc123", tmp_path, progress_callback=None)


def test_download_unknown_preset_raises_before_touching_yt_dlp(tmp_path):
    with pytest.raises(ValueError, match="Unknown preset"):
        download("https://youtu.be/x", tmp_path, preset="nonexistent", progress_callback=None)


def test_download_creates_output_dir(tmp_path):
    out_dir = tmp_path / "nested" / "deep"
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {
            "id": "x",
            "ext": "mp4",
            "requested_downloads": [{"filepath": str(out_dir / "v.mp4")}],
        }
        download("https://youtu.be/x", out_dir, progress_callback=None)

    assert out_dir.exists()


def test_download_progress_hook_reports_percent_and_finish(tmp_path):
    events = []

    def cb(status, percent, filename):
        events.append((status, percent, filename))

    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {
            "id": "x",
            "ext": "mp4",
            "requested_downloads": [{"filepath": str(tmp_path / "v.mp4")}],
        }
        download("https://youtu.be/x", tmp_path, progress_callback=cb)

        opts = mock_cls.call_args.args[0]
        hook = opts["progress_hooks"][0]
        hook(
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 100,
                "filename": "v.mp4",
            }
        )
        hook({"status": "finished", "filename": "v.mp4"})

    assert events[-2] == ("downloading", 50.0, "v.mp4")
    assert events[-1] == ("finished", 100.0, "v.mp4")


@pytest.mark.parametrize(
    ("message", "expected_exc"),
    [
        ("ERROR: [generic] 'x' is not a valid URL", InvalidURLError),
        ("Unsupported URL: foo", InvalidURLError),
        ("Requested format is not available", NoFormatsAvailableError),
        ("<urlopen error timed out>", NetworkError),
    ],
)
def test_download_wraps_yt_dlp_errors(tmp_path, message, expected_exc):
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(message)

        with pytest.raises(expected_exc):
            download("https://youtu.be/x", tmp_path, progress_callback=None)


def test_download_playlist_returns_all_entry_paths_and_skips_failures(tmp_path):
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {
            "entries": [
                {"requested_downloads": [{"filepath": str(tmp_path / "1.mp4")}]},
                None,
                {"requested_downloads": [{"filepath": str(tmp_path / "2.mp4")}]},
            ]
        }

        result = download_playlist("https://youtu.be/x?list=y", tmp_path, progress_callback=None)

    assert result == [tmp_path / "1.mp4", tmp_path / "2.mp4"]
    opts = mock_cls.call_args.args[0]
    assert opts["noplaylist"] is False
    assert opts["ignoreerrors"] is True


def test_list_formats_returns_format_info():
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "resolution": "1920x1080",
                    "vcodec": "avc1",
                    "acodec": "none",
                },
            ]
        }
        result = list_formats("https://youtu.be/x")

    assert len(result) == 1
    assert result[0].format_id == "137"
    assert result[0].resolution == "1920x1080"


def test_list_formats_raises_if_no_formats_key():
    with patch("yoink.downloader.yt_dlp.YoutubeDL") as mock_cls:
        mock_ydl = _mock_ydl(mock_cls)
        mock_ydl.extract_info.return_value = {}

        with pytest.raises(DownloadError, match="No formats found"):
            list_formats("https://youtu.be/x")
