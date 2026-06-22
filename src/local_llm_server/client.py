"""High-level client helpers for local-llm-server."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

TEXT_ANALYSIS_PROMPT = """Analizza la seguente trascrizione e restituisci solo JSON valido:
{{
  "title": "...",
  "summary": "...",
  "key_points": ["...", "..."],
  "action_items": ["...", "..."]
}}

Lingua: {language}
Trascrizione:
{text}
"""

AUDIO_TASK_PROMPTS = {
    "transcribe": "Trascrivi esattamente e parola per parola tutto il parlato. Rispondi solo con la trascrizione.",
    "summary": "Fornisci un riassunto strutturato in JSON con title, summary, key_points e action_items.",
    "analysis": "Analizza approfonditamente il contenuto parlato e restituisci JSON con title, summary, key_points, action_items e risks.",
    "insights": "Estrai insight principali, decisioni, azioni e domande aperte in JSON strutturato.",
    "qa": 'Rispondi alla seguente domanda basandoti sull audio. Domanda: "{question}"',
}


class LocalLLMClient:
    """High-level client for a running local-llm-server instance."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1235",
        model: str | None = None,
        auto_serve: bool = False,
        timeout: float = 1200.0,
        **serve_kwargs: Any,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._handle = None

        if auto_serve:
            from . import serve

            self._handle = serve(model=model, background=True, **serve_kwargs)
            self._wait_until_ready()

    def health(self) -> dict[str, Any]:
        return self._request_json("GET", "/health")

    def is_ready(self) -> bool:
        try:
            return bool(self.health().get("ok"))
        except Exception:
            return False

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        payload: dict[str, Any] = {
            "messages": messages,
            "stream": False,
        }
        if self.model:
            payload["model"] = self.model
        payload.update(kwargs)
        response = self._request_json("POST", "/v1/chat/completions", payload)
        return _extract_text(response)

    def analyze_text(
        self,
        text: str,
        language: str = "it",
        output_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        schema_hint = ""
        if output_schema:
            schema_hint = "\nSchema richiesto:\n" + json.dumps(output_schema, ensure_ascii=False, indent=2)
        prompt = TEXT_ANALYSIS_PROMPT.format(language=language, text=text) + schema_hint
        content = self.chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return _parse_json_object(content)

    def analyze_audio(
        self,
        audio_path: str | Path,
        task: str = "analysis",
        question: str | None = None,
        language: str = "it",
    ) -> dict[str, Any]:
        from .audio import prepare_audio_message

        if task not in AUDIO_TASK_PROMPTS:
            raise ValueError(f"Unsupported audio task: {task}. Expected one of: {', '.join(AUDIO_TASK_PROMPTS)}")
        prompt = AUDIO_TASK_PROMPTS[task].format(question=question or "")
        prompt = f"Lingua attesa: {language}.\n{prompt}"
        content = self.chat(prepare_audio_message(audio_path, prompt), temperature=0.0)
        if task == "transcribe":
            return {"transcript": content}
        return _parse_json_object(content)

    def transcribe_audio(self, audio_path: str | Path, language: str = "it") -> str:
        return str(self.analyze_audio(audio_path, task="transcribe", language=language)["transcript"])

    def shutdown(self) -> None:
        if self._handle is not None:
            self._handle.shutdown()
            self._handle = None

    def _wait_until_ready(self, timeout: float = 60.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_ready():
                return
            time.sleep(0.25)
        raise TimeoutError(f"local-llm-server did not become ready within {timeout:.0f}s")

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"local-llm-server request failed ({exc.code}): {detail}") from exc


def _extract_text(response: dict[str, Any]) -> str:
    for key in ("output", "response", "content", "final_answer"):
        value = response.get(key)
        if isinstance(value, str) and value:
            return value
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
    return ""


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError(f"Response did not contain a JSON object: {content[:500]}")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object response.")
    return parsed
