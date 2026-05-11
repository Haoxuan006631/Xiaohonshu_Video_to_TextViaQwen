from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


REGION_BASE_URLS = {
    "intl": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "cn": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    raw: dict


def audio_to_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


class QwenAsrClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, region: str = "intl") -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set DASHSCOPE_API_KEY or pass --api-key.")
        self.base_url = (base_url or REGION_BASE_URLS[region]).rstrip("/")

    def transcribe(
        self,
        audio_path: Path,
        *,
        model: str = "qwen3-asr-flash",
        language: str | None = "zh",
        enable_itn: bool = True,
        context: str | None = None,
    ) -> TranscriptionResult:
        messages: list[dict] = []
        if context:
            messages.append({"role": "system", "content": [{"text": context}]})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_to_data_url(audio_path)},
                    }
                ],
            }
        )

        asr_options: dict[str, object] = {"enable_itn": enable_itn}
        if language:
            asr_options["language"] = language

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "asr_options": asr_options,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Qwen ASR request failed: HTTP {error.code}\n{body}") from error

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError(f"Unexpected Qwen ASR response: {json.dumps(data, ensure_ascii=False)[:1000]}") from error
        return TranscriptionResult(text=text, raw=data)
