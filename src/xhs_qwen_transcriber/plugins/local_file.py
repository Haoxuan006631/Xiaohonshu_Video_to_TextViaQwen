from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse

from ..downloaders import safe_filename
from ..plugin_base import DownloadRequest, DownloadResult


class LocalFilePlugin:
    name = "local-file"

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return True
        return Path(url).exists()

    def download(self, request: DownloadRequest) -> DownloadResult:
        parsed = urlparse(request.url)
        source = Path(parsed.path if parsed.scheme == "file" else request.url).expanduser()
        if not source.exists():
            raise FileNotFoundError(source)
        destination = request.workdir / "downloads" / safe_filename(source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return DownloadResult(source_url=request.url, video_path=destination, title=source.stem, public_media_url=None)
