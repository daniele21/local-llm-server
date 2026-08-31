#!/usr/bin/env python3
"""Run the representative Apple Silicon evidence campaign with diagnostics."""

from __future__ import annotations

import sys

from local_llm_server.device_evidence_campaign import (
    DeviceEvidenceCampaign,
    _build_parser,
    _safe_exception_text,
)
from local_llm_server.device_evidence_diagnostics import print_campaign_diagnostics


def main() -> int:
    args = _build_parser().parse_args()
    campaign = DeviceEvidenceCampaign(args)
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
