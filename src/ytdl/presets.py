from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    format: str
    merge_output_format: str | None = None
    postprocessors: list[dict] = field(default_factory=list)

    def to_ydl_opts(self) -> dict:
        opts: dict = {"format": self.format}
        if self.merge_output_format:
            opts["merge_output_format"] = self.merge_output_format
        if self.postprocessors:
            opts["postprocessors"] = self.postprocessors
        return opts


PRESETS: dict[str, Preset] = {
    "video-best": Preset(
        name="video-best",
        description="Best available video+audio, merged into mp4",
        format="bestvideo+bestaudio/best",
        merge_output_format="mp4",
    ),
    "video-1080p": Preset(
        name="video-1080p",
        description="Best video+audio capped at 1080p, merged into mp4",
        format="bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        merge_output_format="mp4",
    ),
    "video-720p": Preset(
        name="video-720p",
        description="Best video+audio capped at 720p, merged into mp4",
        format="bestvideo[height<=720]+bestaudio/best[height<=720]",
        merge_output_format="mp4",
    ),
    "audio-best": Preset(
        name="audio-best",
        description="Best available audio, kept in its native format (e.g. m4a/opus)",
        format="bestaudio/best",
    ),
    "audio-mp3": Preset(
        name="audio-mp3",
        description="Best available audio, transcoded to mp3",
        format="bestaudio/best",
        postprocessors=[
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    ),
}

DEFAULT_PRESET = "video-best"


def get_preset(name: str) -> Preset:
    try:
        return PRESETS[name]
    except KeyError:
        available = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}") from None


def list_presets() -> list[Preset]:
    return list(PRESETS.values())
