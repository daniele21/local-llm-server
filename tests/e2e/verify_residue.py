#!/usr/bin/env python3
"""Fail when deterministic E2E leaves listener/temp residue after bounded shutdown."""

import time

from lifecycle import listener_open, stale_owned_roots

HOST = "127.0.0.1"
PORT = 8765
SHUTDOWN_WAIT_SECONDS = 6.0
POLL_SECONDS = 0.1


def current_residue() -> tuple[bool, list]:
    return listener_open(HOST, PORT), stale_owned_roots()


def wait_for_zero_residue(timeout: float = SHUTDOWN_WAIT_SECONDS) -> tuple[bool, list]:
    deadline = time.monotonic() + timeout
    while True:
        listener, roots = current_residue()
        if not listener and not roots:
            return listener, roots
        if time.monotonic() >= deadline:
            return listener, roots
        time.sleep(POLL_SECONDS)


def main() -> int:
    listener, stale = wait_for_zero_residue()
    errors: list[str] = []
    if listener:
        errors.append(f"listener remains open on {HOST}:{PORT}")
    if stale:
        errors.append("owned E2E temp roots remain: " + ", ".join(str(path) for path in stale))

    print("E2E residue check")
    print(f"bounded shutdown wait: {SHUTDOWN_WAIT_SECONDS:.1f}s")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
