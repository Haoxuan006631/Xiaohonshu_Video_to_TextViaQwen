from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    workdir: Path
    cookies_file: Path | None = None
    cookie_header: str | None = None


@dataclass(frozen=True)
class DownloadResult:
    source_url: str
    video_path: Path
    title: str | None = None
    public_media_url: str | None = None


class VideoSourcePlugin(Protocol):
    name: str

    def can_handle(self, url: str) -> bool:
        ...

    def download(self, request: DownloadRequest) -> DownloadResult:
        ...


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[VideoSourcePlugin] = []

    def register(self, plugin: VideoSourcePlugin) -> None:
        self._plugins.append(plugin)

    def resolve(self, url: str, preferred: str | None = None) -> VideoSourcePlugin:
        if preferred:
            for plugin in self._plugins:
                if plugin.name == preferred:
                    return plugin
            names = ", ".join(plugin.name for plugin in self._plugins)
            raise ValueError(f"Unknown plugin '{preferred}'. Available: {names}")

        for plugin in self._plugins:
            if plugin.can_handle(url):
                return plugin

        names = ", ".join(plugin.name for plugin in self._plugins)
        raise ValueError(f"No plugin can handle this URL. Available: {names}")

    @property
    def names(self) -> list[str]:
        return [plugin.name for plugin in self._plugins]
