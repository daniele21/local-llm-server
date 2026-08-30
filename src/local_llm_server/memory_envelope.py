"""Deterministic configured memory envelopes for residency and active requests.

These estimates are policy inputs, not measurements. Missing evidence remains
explicitly unavailable rather than being converted to zero. Representative
hardware evidence is responsible for calibrating configured values against real
backend and unified-memory behavior.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .core.contracts import InferenceRequest

_GIB = 1024**3
_MIB = 1024**2


@dataclass(frozen=True, slots=True)
class MemoryComponent:
    name: str
    bytes: int | None
    source: str
    required: bool = True

    @property
    def available(self) -> bool:
        return self.bytes is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "bytes": self.bytes,
            "source": self.source,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class MemoryEnvelope:
    scope: str
    components: tuple[MemoryComponent, ...]
    override_total_bytes: int | None = None

    @property
    def accounted_bytes(self) -> int | None:
        if self.override_total_bytes is not None:
            return self.override_total_bytes
        available = [component.bytes for component in self.components if component.bytes is not None]
        if not available:
            return None
        return sum(available)

    @property
    def unavailable_components(self) -> tuple[str, ...]:
        if self.override_total_bytes is not None:
            return ()
        return tuple(
            component.name
            for component in self.components
            if component.required and component.bytes is None
        )

    @property
    def complete(self) -> bool:
        if self.override_total_bytes is not None:
            return True
        return self.accounted_bytes is not None and not self.unavailable_components

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "accounted_bytes": self.accounted_bytes,
            "complete": self.complete,
            "override_total_bytes": self.override_total_bytes,
            "unavailable_components": list(self.unavailable_components),
            "components": {
                component.name: component.as_dict()
                for component in self.components
            },
        }


def resident_memory_envelope(config: Mapping[str, Any]) -> MemoryEnvelope:
    """Build the configured resident-memory estimate for one runtime."""
    override = _non_negative_int(config.get("resource_estimate_bytes"))
    weights = _model_weights_component(config)
    backend_overhead = _configured_component(
        "backend_overhead",
        config.get("resource_backend_overhead_bytes"),
    )
    context_cache = _configured_component(
        "context_cache",
        config.get("resource_context_cache_bytes"),
    )
    prompt_cache = _prompt_cache_component(config)
    projector = _projector_component(config)
    safety_margin = _configured_component(
        "safety_margin",
        config.get("resource_safety_margin_bytes"),
    )
    return MemoryEnvelope(
        scope="resident",
        components=(
            weights,
            backend_overhead,
            context_cache,
            prompt_cache,
            projector,
            safety_margin,
        ),
        override_total_bytes=override,
    )


def request_memory_envelope(
    request: InferenceRequest,
    runtime_config: Mapping[str, Any],
) -> MemoryEnvelope:
    """Build the transient peak estimate held for one active request."""
    override = _non_negative_int(runtime_config.get("resource_request_estimate_bytes"))
    base = _optional_configured_component(
        "request_base",
        runtime_config.get("resource_request_base_bytes"),
    )

    per_output_token = _non_negative_int(
        runtime_config.get("resource_request_output_token_bytes")
    )
    if per_output_token is None:
        output = MemoryComponent(
            name="request_output_tokens",
            bytes=None,
            source="not_configured",
            required=False,
        )
    elif request.generation.max_tokens is None:
        output = MemoryComponent(
            name="request_output_tokens",
            bytes=None,
            source="max_tokens_unavailable",
            required=True,
        )
    else:
        output = MemoryComponent(
            name="request_output_tokens",
            bytes=per_output_token * max(0, int(request.generation.max_tokens)),
            source="configured_per_output_token",
            required=True,
        )

    payload_bytes = _canonical_payload_bytes(request)
    input_multiplier = _non_negative_int(
        runtime_config.get("resource_request_input_byte_multiplier")
    )
    if input_multiplier is None:
        input_component = MemoryComponent(
            name="request_input",
            bytes=None,
            source="not_configured",
            required=False,
        )
    else:
        input_component = MemoryComponent(
            name="request_input",
            bytes=payload_bytes * input_multiplier,
            source="configured_input_byte_multiplier",
            required=True,
        )

    safety = _optional_configured_component(
        "request_safety_margin",
        runtime_config.get("resource_request_safety_margin_bytes"),
    )
    return MemoryEnvelope(
        scope="transient",
        components=(base, input_component, output, safety),
        override_total_bytes=override,
    )


def _model_weights_component(config: Mapping[str, Any]) -> MemoryComponent:
    explicit = _non_negative_int(config.get("resource_model_weights_bytes"))
    if explicit is not None:
        return MemoryComponent("model_weights", explicit, "configured")

    size_gb = config.get("size_gb")
    if size_gb is not None:
        try:
            size_bytes = max(0, int(float(size_gb) * _GIB))
        except (TypeError, ValueError):
            size_bytes = None
        if size_bytes is not None:
            return MemoryComponent("model_weights", size_bytes, "registry_artifact_size")

    model_path = config.get("model_path")
    if model_path:
        try:
            path = Path(str(model_path)).expanduser()
            if path.is_file():
                return MemoryComponent("model_weights", path.stat().st_size, "artifact_file_size")
        except OSError:
            pass
    return MemoryComponent("model_weights", None, "unavailable")


def _prompt_cache_component(config: Mapping[str, Any]) -> MemoryComponent:
    explicit = _non_negative_int(config.get("resource_prompt_cache_bytes"))
    if explicit is not None:
        return MemoryComponent("prompt_cache", explicit, "configured")
    cache_mib = _non_negative_int(config.get("llama_server_cache_ram_mib"))
    if cache_mib is not None:
        return MemoryComponent("prompt_cache", cache_mib * _MIB, "llama_server_cache_ram")
    return MemoryComponent("prompt_cache", None, "not_configured", required=False)


def _projector_component(config: Mapping[str, Any]) -> MemoryComponent:
    explicit = _non_negative_int(config.get("resource_projector_bytes"))
    if explicit is not None:
        return MemoryComponent("projector", explicit, "configured")
    projector_path = config.get("mmproj_path")
    if not projector_path:
        return MemoryComponent("projector", None, "not_applicable", required=False)
    try:
        path = Path(str(projector_path)).expanduser()
        if path.is_file():
            return MemoryComponent("projector", path.stat().st_size, "artifact_file_size")
    except OSError:
        pass
    return MemoryComponent("projector", None, "unavailable", required=True)


def _configured_component(name: str, value: Any) -> MemoryComponent:
    parsed = _non_negative_int(value)
    if parsed is None:
        return MemoryComponent(name, None, "unavailable", required=True)
    return MemoryComponent(name, parsed, "configured", required=True)


def _optional_configured_component(name: str, value: Any) -> MemoryComponent:
    parsed = _non_negative_int(value)
    if parsed is None:
        return MemoryComponent(name, None, "not_configured", required=False)
    return MemoryComponent(name, parsed, "configured", required=True)


def _canonical_payload_bytes(request: InferenceRequest) -> int:
    payload = {
        "task": request.task.value,
        "model": request.model,
        "messages": list(request.messages),
        "input_text": request.input_text,
        "stream": request.stream,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return len(encoded)


def _non_negative_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("memory estimate values must be non-negative integers")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("memory estimate values must be non-negative integers") from exc
    if parsed < 0:
        raise ValueError("memory estimate values must be non-negative integers")
    return parsed
