from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{method} {url} did not return JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{method} {url} did not return a JSON object")
    return value


def _identity_runtime_key(identity: dict[str, Any], requested: str | None) -> str:
    models = identity.get("models")
    if not isinstance(models, dict) or not models:
        raise RuntimeError("runtime identity contains no models")
    if requested is not None:
        if requested in models:
            return requested
        matches = []
        for key, entry in models.items():
            if not isinstance(entry, dict):
                continue
            model = entry.get("model")
            if isinstance(model, dict) and model.get("id") == requested:
                matches.append(str(key))
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise RuntimeError(f"model is missing from runtime identity: {requested}")
        raise RuntimeError(f"model is ambiguous in runtime identity: {requested}")
    default_model = identity.get("default_model")
    if isinstance(default_model, str) and default_model in models:
        return default_model
    if len(models) == 1:
        return str(next(iter(models)))
    raise RuntimeError("select a model explicitly when multiple runtimes are resident")


def _model_entry(models_payload: dict[str, Any], runtime_key: str) -> dict[str, Any]:
    rows = models_payload.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("/v1/models has no data list")
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("key") == runtime_key or row.get("id") == runtime_key:
            return row
    raise RuntimeError(f"runtime is missing from /v1/models: {runtime_key}")


def _status_entry(status: dict[str, Any], runtime_key: str) -> dict[str, Any]:
    models = status.get("models")
    if isinstance(models, dict):
        entry = models.get(runtime_key)
        if isinstance(entry, dict):
            return entry
        raise RuntimeError(f"runtime is missing from /status: {runtime_key}")
    return status


def _completion_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RuntimeError("chat completion returned no choices")
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise RuntimeError("chat completion returned no text content")
    content = str(message["content"])
    if not content:
        raise RuntimeError("chat completion returned empty text content")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a bounded real-runtime smoke against an already running Local LLM Server."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:1235")
    parser.add_argument("--model", default=None, help="Runtime key or model id; optional for one/default runtime")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    health = _request_json("GET", f"{base_url}/health")
    models = _request_json("GET", f"{base_url}/v1/models")
    identity = _request_json("GET", f"{base_url}/v1/runtime/identity")
    status = _request_json("GET", f"{base_url}/status")

    if identity.get("protocol_version") != "local-llm-identity-v1":
        raise RuntimeError("unsupported or missing runtime identity protocol")
    runtime_key = _identity_runtime_key(identity, args.model)
    model_row = _model_entry(models, runtime_key)
    identity_models = identity["models"]
    identity_entry = identity_models[runtime_key]
    if not isinstance(identity_entry, dict):
        raise RuntimeError("selected runtime identity entry is invalid")
    runtime_identity = identity_entry.get("runtime")
    if not isinstance(runtime_identity, dict):
        raise RuntimeError("selected runtime identity has no runtime object")
    selected_status = _status_entry(status, runtime_key)

    completion = _request_json(
        "POST",
        f"{base_url}/v1/chat/completions",
        {
            "model": runtime_key,
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "temperature": 0,
            "max_tokens": 8,
            "stream": False,
        },
    )
    content = _completion_content(completion)
    usage = completion.get("usage")

    report = {
        "ok": True,
        "server": health.get("server"),
        "runtime_key": runtime_key,
        "model_id": model_row.get("id"),
        "identity_protocol": identity.get("protocol_version"),
        "identity_evidence_grade": runtime_identity.get("evidence_grade"),
        "runtime_name": runtime_identity.get("name"),
        "runtime_version": runtime_identity.get("version"),
        "status_phase": selected_status.get("phase"),
        "response_characters": len(content),
        "token_usage_observed": isinstance(usage, dict)
        and isinstance(usage.get("prompt_tokens"), int)
        and isinstance(usage.get("completion_tokens"), int),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
