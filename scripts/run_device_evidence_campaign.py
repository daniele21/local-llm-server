#!/usr/bin/env python3
"""Run the representative Apple Silicon evidence campaign with diagnostics."""

from __future__ import annotations

import sys

from local_llm_server.device_evidence_campaign import (
    DeviceEvidenceCampaign,
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
    campaign = DeviceEvidenceCampaign(args)
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
