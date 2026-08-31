#!/usr/bin/env python3
"""Run the representative Apple Silicon evidence campaign with diagnostics."""

from __future__ import annotations

import sys
import time
from typing import Any, Callable, Mapping

from local_llm_server.device_evidence_campaign import (
    DeviceEvidenceCampaign,
    _FAIL,
    _INCONCLUSIVE,
    _PASS,
    _build_parser,
    _phase,
    _safe_exception_text,
)
from local_llm_server.device_evidence_diagnostics import print_campaign_diagnostics
from local_llm_server.llama_server_compat import (
    LLAMA_CPP_VALIDATED_MIN_BUILD,
    LLAMA_CPP_VALIDATED_RELEASE,
    resolve_llama_server_binary,
)


class ProgressDeviceEvidenceCampaign(DeviceEvidenceCampaign):
    """Device evidence campaign with bounded, privacy-safe live phase output."""

    def _record(self, name: str, result: Mapping[str, Any]) -> None:
        super()._record(name, result)
        status = str(result.get("status", "?"))
        reason = str(result.get("reason", ""))
        duration = result.get("duration_seconds")
        elapsed = (
            f" ({float(duration):.1f}s)"
            if isinstance(duration, (int, float)) and not isinstance(duration, bool)
            else ""
        )
        print(f"{status:>12}  {name}{elapsed}: {reason}", flush=True)

    def _run_phase(
        self,
        name: str,
        fn: Callable[[], Mapping[str, Any]],
        *,
        exception_status: str = _FAIL,
    ) -> dict[str, Any]:
        print(f"{'START':>12}  {name}", flush=True)
        return super()._run_phase(name, fn, exception_status=exception_status)


def _rrg5_backend_preflight(args):
    """Bounded dependency check for the explicit full-scope llama_server path."""
    if args.scope != "full" or args.multi_model_backend != "llama_server":
        return None
    checks = {
        "backend": "llama_server",
        "required_release": LLAMA_CPP_VALIDATED_RELEASE,
        "minimum_build": LLAMA_CPP_VALIDATED_MIN_BUILD,
        "ready": False,
        "backend_version": None,
        "profile": None,
    }
    try:
        _binary, compatibility = resolve_llama_server_binary(
            {"llama_server_allow_unvalidated": False}
        )
    except (OSError, ValueError, RuntimeError):
        return _phase(
            _INCONCLUSIVE,
            reason=(
                "full-scope RRG-5 requires an attributable llama-server that satisfies "
                "the validated runtime floor"
            ),
            checks=checks,
        )
    checks.update(
        {
            "ready": True,
            "backend_version": compatibility.backend_version,
            "profile": compatibility.profile,
        }
    )
    return _phase(
        _PASS,
        reason="RRG-5 external llama-server dependency satisfies the validated runtime floor",
        checks=checks,
    )


def main() -> int:
    args = _build_parser().parse_args()
    campaign = ProgressDeviceEvidenceCampaign(args)
    print("\nDevice evidence campaign live progress", flush=True)
    print("=" * 38, flush=True)
    if args.scope == "full" and args.multi_model_backend == "llama_server":
        print(f"{'START':>12}  rrg5_backend_preflight", flush=True)
    dependency = _rrg5_backend_preflight(args)
    if dependency is not None:
        campaign._record("rrg5_backend_preflight", dependency)
        if dependency["status"] != _PASS:
            exit_code = campaign._finalize()
            print_campaign_diagnostics(campaign.output_dir)
            return exit_code
    try:
        exit_code = campaign.run()
    except KeyboardInterrupt:
        print(
            "Campaign interrupted; inspect campaign-summary.json for retained phase state.",
            file=sys.stderr,
        )
        exit_code = 130
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Campaign failed: {_safe_exception_text(exc)}", file=sys.stderr)
        exit_code = 1
    print_campaign_diagnostics(campaign.output_dir)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
