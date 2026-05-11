from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalSecrets:
    api_key: str | None = None
    cookie_header: str | None = None


def load_local_secrets(path: Path | None = None) -> LocalSecrets:
    secrets_path = path or Path("local.secrets.json")
    if not secrets_path.exists():
        return LocalSecrets()
    data = json.loads(secrets_path.read_text(encoding="utf-8"))
    return LocalSecrets(
        api_key=data.get("api_key"),
        cookie_header=data.get("cookie_header"),
    )
