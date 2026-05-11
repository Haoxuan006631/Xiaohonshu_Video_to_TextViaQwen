from __future__ import annotations

from pathlib import Path

from .downloaders import require_command, run_command


def extract_audio(video_path: Path, output_path: Path, bitrate: str = "64k") -> Path:
    require_command("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            bitrate,
            str(output_path),
        ]
    )
    return output_path


def ensure_under_limit(path: Path, limit_mb: float) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > limit_mb:
        raise RuntimeError(
            f"Audio file is {size_mb:.2f} MB, above the {limit_mb:.2f} MB sync Qwen-ASR limit. "
            "Use a shorter clip, lower bitrate, or implement the async Qwen3-ASR-Flash-Filetrans path."
        )
