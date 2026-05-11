from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


REGION_BASE_URLS = {
    "intl": "https://dashscope-intl.aliyuncs.com/api/v1",
    "cn": "https://dashscope.aliyuncs.com/api/v1",
}


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    raw: dict


class FunAsrClient:
    def __init__(self, api_key: str | None = None, region: str = "cn", base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set DASHSCOPE_API_KEY or pass --api-key.")
        self.base_url = (base_url or REGION_BASE_URLS[region]).rstrip("/")

    def transcribe(
        self,
        *,
        file_url: str,
        model: str = "fun-asr",
        language: str | None = "zh",
        poll_interval_seconds: float = 1.0,
        timeout_seconds: float = 300.0,
    ) -> TranscriptionResult:
        task_id = self._submit_task(file_url=file_url, model=model, language=language)
        task = self._wait_for_task(task_id, poll_interval_seconds=poll_interval_seconds, timeout_seconds=timeout_seconds)
        result_url = task["output"]["results"][0]["transcription_url"]
        raw = self._read_json(result_url)
        transcripts = raw.get("transcripts", [])
        text = "\n".join(item.get("text", "").strip() for item in transcripts if item.get("text", "").strip())
        return TranscriptionResult(text=text, raw=raw)

    def _submit_task(self, *, file_url: str, model: str, language: str | None) -> str:
        payload: dict[str, object] = {
            "model": model,
            "input": {"file_urls": [file_url]},
            "parameters": {"channel_id": [0]},
        }
        if language:
            payload["parameters"]["language_hints"] = [language]
        response = self._request_json(
            f"{self.base_url}/services/audio/asr/transcription",
            payload=payload,
            extra_headers={"X-DashScope-Async": "enable"},
        )
        return response["output"]["task_id"]

    def _wait_for_task(self, task_id: str, *, poll_interval_seconds: float, timeout_seconds: float) -> dict:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            result = self._request_json(f"{self.base_url}/tasks/{task_id}", payload=None)
            status = result["output"]["task_status"]
            if status == "SUCCEEDED":
                results = result["output"].get("results") or []
                if not results or results[0].get("subtask_status") != "SUCCEEDED":
                    raise RuntimeError(f"Fun-ASR task succeeded but subtask failed: {json.dumps(result, ensure_ascii=False)}")
                return result
            if status in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"Fun-ASR task failed: {json.dumps(result, ensure_ascii=False)}")
            time.sleep(poll_interval_seconds)
        raise TimeoutError(f"Fun-ASR task {task_id} did not finish within {timeout_seconds:.0f}s.")

    def _request_json(self, url: str, payload: dict | None, extra_headers: dict[str, str] | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        return self._open_json(request)

    def _read_json(self, url: str) -> dict:
        request = urllib.request.Request(url, method="GET")
        return self._open_json(request)

    def _open_json(self, request: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Fun-ASR request failed: HTTP {error.code}\n{body}") from error
