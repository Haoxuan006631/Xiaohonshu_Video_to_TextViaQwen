from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audio import ensure_under_limit, extract_audio
from .config import load_local_secrets
from .fun_asr import FunAsrClient
from .plugin_base import DownloadRequest
from .plugin_loader import load_plugins
from .qwen_asr import QwenAsrClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download a video via plugins and transcribe speech with Qwen ASR.")
    parser.add_argument("url", help="Xiaohongshu link, direct video URL, file:// URL, or local video path.")
    parser.add_argument("--plugin", help="Force a plugin name, e.g. xiaohongshu-ytdlp.")
    parser.add_argument("--plugin-dir", type=Path, default=Path("plugins"), help="Directory for custom plugin .py files.")
    parser.add_argument("--workdir", type=Path, default=Path("runs"), help="Directory for downloads, audio, and output.")
    parser.add_argument("--secrets-file", type=Path, default=Path("local.secrets.json"), help="Local secrets JSON file.")
    parser.add_argument("--cookies", type=Path, help="Cookie file for yt-dlp, if the video requires authorization.")
    parser.add_argument("--cookie-header", help="Raw Cookie header string for platforms like Xiaohongshu.")
    parser.add_argument("--api-key", help="DashScope API key. Defaults to DASHSCOPE_API_KEY.")
    parser.add_argument("--asr-backend", choices=["auto", "fun-asr", "qwen"], default="auto", help="ASR backend selection.")
    parser.add_argument("--asr-model", help="Override ASR model name for the selected backend.")
    parser.add_argument("--region", choices=["intl", "cn"], default="cn", help="DashScope endpoint region.")
    parser.add_argument("--base-url", help="Override OpenAI-compatible base URL.")
    parser.add_argument("--language", default="zh", help="ASR language code. Use empty string for auto/multilingual.")
    parser.add_argument("--no-itn", action="store_true", help="Disable inverse text normalization.")
    parser.add_argument("--context", help="Domain words or background text to bias recognition.")
    parser.add_argument("--audio-limit-mb", type=float, default=9.5, help="Safety limit for sync Qwen ASR payload.")
    parser.add_argument("--keep-raw", action="store_true", help="Save raw Qwen response JSON.")
    return parser


def resolve_asr_backend(requested_backend: str, public_media_url: str | None) -> str:
    if requested_backend != "auto":
        return requested_backend
    if public_media_url:
        return "fun-asr"
    return "qwen"


def main() -> None:
    args = build_parser().parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    local_secrets = load_local_secrets(args.secrets_file)
    cookie_header = args.cookie_header or local_secrets.cookie_header
    api_key = args.api_key or local_secrets.api_key

    registry = load_plugins(args.plugin_dir)
    plugin = registry.resolve(args.url, args.plugin)
    print(f"Using plugin: {plugin.name}")

    download = plugin.download(
        DownloadRequest(
            url=args.url,
            workdir=args.workdir,
            cookies_file=args.cookies,
            cookie_header=cookie_header,
        )
    )
    print(f"Downloaded: {download.video_path}")

    language = args.language.strip() or None
    backend = resolve_asr_backend(args.asr_backend, download.public_media_url)
    print(f"ASR backend: {backend}")

    if backend == "fun-asr":
        if not download.public_media_url:
            raise RuntimeError("Fun-ASR requires a public media URL. Use a direct/public URL source or switch to --asr-backend qwen.")
        client = FunAsrClient(api_key=api_key, region=args.region, base_url=args.base_url)
        result = client.transcribe(
            file_url=download.public_media_url,
            model=args.asr_model or "fun-asr",
            language=language,
        )
    else:
        audio_path = args.workdir / "audio" / f"{download.video_path.stem}.mp3"
        extract_audio(download.video_path, audio_path)
        ensure_under_limit(audio_path, args.audio_limit_mb)
        print(f"Audio: {audio_path}")
        client = QwenAsrClient(api_key=api_key, base_url=args.base_url, region=args.region)
        result = client.transcribe(
            audio_path,
            model=args.asr_model or "qwen3-asr-flash",
            language=language,
            enable_itn=not args.no_itn,
            context=args.context,
        )

    output_path = args.workdir / "transcript.txt"
    output_path.write_text(result.text, encoding="utf-8")
    print(f"Transcript: {output_path}")
    print(result.text)

    if args.keep_raw:
        raw_path = args.workdir / "qwen_response.json"
        raw_path.write_text(json.dumps(result.raw, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Raw response: {raw_path}")


if __name__ == "__main__":
    main()
