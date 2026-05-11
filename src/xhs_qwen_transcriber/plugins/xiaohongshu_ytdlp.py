from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from ..downloaders import (
    download_file,
    download_with_curl,
    resolve_yt_dlp_command,
    run_command_capture,
    safe_filename,
)
from ..plugin_base import DownloadRequest, DownloadResult


class XiaohongshuYtDlpPlugin:
    name = "xiaohongshu-ytdlp"

    def can_handle(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return "xiaohongshu.com" in host or "xhslink.com" in host

    def download(self, request: DownloadRequest) -> DownloadResult:
        title, media_url = self._extract_media(request)
        suffix = Path(urlparse(media_url).path).suffix or ".mp4"
        destination = request.workdir / "downloads" / f"{safe_filename(title)}{suffix}"
        try:
            download_with_curl(media_url, destination)
        except RuntimeError:
            download_file(media_url, destination)
        return DownloadResult(
            source_url=request.url,
            video_path=destination,
            title=safe_filename(title),
            public_media_url=media_url,
        )

    def _extract_media(self, request: DownloadRequest) -> tuple[str, str]:
        args = [
            *resolve_yt_dlp_command(),
            "--no-playlist",
            "--restrict-filenames",
            "--simulate",
            "--print",
            "title",
            "--print",
            "urls",
        ]
        if request.cookies_file:
            args.extend(["--cookies", str(request.cookies_file)])
        if request.cookie_header:
            args.extend(["--add-header", f"Cookie: {request.cookie_header}"])
        args.append(request.url)
        output = run_command_capture(args)
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if len(lines) < 2:
            raise RuntimeError(f"yt-dlp did not return title and media URL.\n{output}")
        title = lines[0]
        media_url = lines[-1]
        return title, media_url
