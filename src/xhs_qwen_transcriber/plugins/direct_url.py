from __future__ import annotations

from urllib.parse import urlparse

from ..downloaders import download_file, filename_from_url
from ..plugin_base import DownloadRequest, DownloadResult


class DirectUrlPlugin:
    name = "direct-url"

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.path.lower().endswith(
            (".mp4", ".mov", ".m4v", ".webm")
        )

    def download(self, request: DownloadRequest) -> DownloadResult:
        filename = filename_from_url(request.url)
        video_path = request.workdir / "downloads" / filename
        download_file(request.url, video_path)
        return DownloadResult(source_url=request.url, video_path=video_path, title=filename, public_media_url=request.url)
