from __future__ import annotations

import importlib.util
from pathlib import Path

from .plugin_base import PluginRegistry
from .plugins.direct_url import DirectUrlPlugin
from .plugins.local_file import LocalFilePlugin
from .plugins.xiaohongshu_ytdlp import XiaohongshuYtDlpPlugin


def load_plugins(plugin_dir: Path | None = None) -> PluginRegistry:
    registry = PluginRegistry()
    registry.register(LocalFilePlugin())
    registry.register(DirectUrlPlugin())
    registry.register(XiaohongshuYtDlpPlugin())

    if plugin_dir and plugin_dir.exists():
        for plugin_file in sorted(plugin_dir.glob("*.py")):
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register = getattr(module, "register", None)
            if callable(register):
                register(registry)

    return registry
