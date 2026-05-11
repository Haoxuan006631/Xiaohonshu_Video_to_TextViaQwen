from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def safe_filename(value: str, fallback: str = "video") -> str:
    cleaned = "".join(char if char.isalnum() or char in "._- " else "_" for char in value)
    cleaned = "_".join(cleaned.split())
    return cleaned[:120] or fallback


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; xhs-qwen-transcriber/0.1)",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    return destination


def download_with_curl(url: str, destination: Path) -> Path:
    require_command("curl")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "curl",
            "--location",
            "--fail",
            "--retry",
            "10",
            "--retry-all-errors",
            "--output",
            str(destination),
            url,
        ]
    )
    return destination


def filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    name = Path(parsed.path).name
    return safe_filename(name or "video.mp4")


def require_command(command: str) -> str:
    resolved = shutil.which(command)
    if not resolved:
        raise RuntimeError(f"Missing required command: {command}")
    return resolved


def resolve_yt_dlp_command() -> list[str]:
    binary = shutil.which("yt-dlp")
    if binary:
        return [binary]
    if importlib.util.find_spec("yt_dlp"):
        return [sys.executable, "-m", "yt_dlp"]
    raise RuntimeError("Missing required command: yt-dlp")


def run_command(args: list[str]) -> None:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{details}")


def run_command_capture(args: list[str]) -> str:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{details}")
    return completed.stdout
