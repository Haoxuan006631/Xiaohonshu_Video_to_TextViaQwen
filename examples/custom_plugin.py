from __future__ import annotations

from xhs_qwen_transcriber.plugin_base import DownloadRequest, DownloadResult, PluginRegistry


class ExamplePlugin:
    name = "example"

    def can_handle(self, url: str) -> bool:
        return url.startswith("example://")

    def download(self, request: DownloadRequest) -> DownloadResult:
        raise NotImplementedError("Replace this with your platform-specific authorized downloader.")


def register(registry: PluginRegistry) -> None:
    registry.register(ExamplePlugin())
