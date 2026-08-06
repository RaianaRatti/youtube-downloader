import pytest

from ytdl.presets import DEFAULT_PRESET, PRESETS, get_preset, list_presets


def test_default_preset_exists():
    assert DEFAULT_PRESET in PRESETS


def test_get_preset_returns_known_preset():
    preset = get_preset("video-best")
    assert preset.name == "video-best"


def test_get_preset_unknown_raises_with_available_list():
    with pytest.raises(ValueError, match="Unknown preset 'nope'"):
        get_preset("nope")


def test_list_presets_matches_dict():
    assert {p.name for p in list_presets()} == set(PRESETS)


def test_video_preset_sets_merge_output_format():
    opts = get_preset("video-best").to_ydl_opts()
    assert opts["format"] == "bestvideo+bestaudio/best"
    assert opts["merge_output_format"] == "mp4"
    assert "postprocessors" not in opts


def test_audio_mp3_preset_sets_extract_audio_postprocessor():
    opts = get_preset("audio-mp3").to_ydl_opts()
    assert opts["format"] == "bestaudio/best"
    assert opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"
    assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
    assert "merge_output_format" not in opts


def test_audio_best_preset_has_no_postprocessors_or_merge():
    opts = get_preset("audio-best").to_ydl_opts()
    assert "postprocessors" not in opts
    assert "merge_output_format" not in opts
