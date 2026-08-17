"""Privacy-safe identity envelope for decision-bearing benchmark/evidence runs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

_SENSITIVE_KEYS = frozenset(
    {
        "prompt",
        "output",
        "model_path",
        "artifact_path",
        "hostname",
        "username",
        "home_directory",
        "credential",
        "secret",
    }
)


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _find_sensitive_key(value: Any, *, prefix: str = "") -> str | None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            location = f"{prefix}.{key}" if prefix else key
            if key.lower() in _SENSITIVE_KEYS:
                return location
            nested = _find_sensitive_key(child, prefix=location)
            if nested is not None:
                return nested
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            nested = _find_sensitive_key(child, prefix=f"{prefix}[{index}]")
            if nested is not None:
                return nested
    return None


@dataclass(frozen=True, slots=True)
class EvidenceIdentity:
    evidence_kind: str
    run_id: str
    generated_at: str
    source_revision: str | None
    environment_class: str
    workload_fingerprint: str
    configuration_fingerprint: str
    runtime_fingerprint: str | None
    comparison_key: str
    evidence_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "evidence_kind": self.evidence_kind,
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "source_revision": self.source_revision,
            "environment_class": self.environment_class,
            "workload_fingerprint": self.workload_fingerprint,
            "configuration_fingerprint": self.configuration_fingerprint,
            "runtime_fingerprint": self.runtime_fingerprint,
            "comparison_key": self.comparison_key,
            "evidence_id": self.evidence_id,
        }


def build_evidence_identity(
    *,
    evidence_kind: str,
    workload: Mapping[str, Any],
    configuration: Mapping[str, Any],
    environment_class: str,
    source_revision: str | None,
    runtime_identity: Mapping[str, Any] | None = None,
    run_id: str | None = None,
    generated_at: str | None = None,
) -> EvidenceIdentity:
    """Build fingerprints without retaining workload/configuration payloads.

    Callers provide only bounded identity metadata. Raw prompt/output/path/host/user
    fields are rejected so this helper cannot accidentally turn evidence identity
    into a content-retention channel.
    """
    kind = evidence_kind.strip()
    environment = environment_class.strip()
    if not kind:
        raise ValueError("evidence_kind must be non-empty")
    if not environment:
        raise ValueError("environment_class must be non-empty")
    for label, value in (("workload", workload), ("configuration", configuration), ("runtime_identity", runtime_identity or {})):
        sensitive = _find_sensitive_key(value)
        if sensitive is not None:
            raise ValueError(f"{label} contains sensitive identity key: {sensitive}")

    workload_fp = _fingerprint(workload)
    configuration_fp = _fingerprint(configuration)
    runtime_fp = _fingerprint(runtime_identity) if runtime_identity is not None else None
    stable = {
        "evidence_kind": kind,
        "environment_class": environment,
        "workload_fingerprint": workload_fp,
        "configuration_fingerprint": configuration_fp,
        "runtime_fingerprint": runtime_fp,
    }
    comparison_key = _fingerprint(stable)
    resolved_run_id = (run_id or uuid4().hex).strip()
    if not resolved_run_id:
        raise ValueError("run_id must be non-empty")
    resolved_generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    evidence_id = _fingerprint(
        {
            **stable,
            "source_revision": source_revision,
            "run_id": resolved_run_id,
        }
    )
    return EvidenceIdentity(
        evidence_kind=kind,
        run_id=resolved_run_id,
        generated_at=resolved_generated_at,
        source_revision=source_revision,
        environment_class=environment,
        workload_fingerprint=workload_fp,
        configuration_fingerprint=configuration_fp,
        runtime_fingerprint=runtime_fp,
        comparison_key=comparison_key,
        evidence_id=evidence_id,
    )
