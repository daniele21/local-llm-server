#!/usr/bin/env python3
"""Fail when the deterministic E2E run leaves its listener or owned temp state."""

from lifecycle import listener_open, stale_owned_roots

HOST = "127.0.0.1"
PORT = 8765


def main() -> int:
    errors: list[str] = []
    if listener_open(HOST, PORT):
        errors.append(f"listener remains open on {HOST}:{PORT}")
    stale = stale_owned_roots()
    if stale:
        errors.append("owned E2E temp roots remain: " + ", ".join(str(path) for path in stale))

    print("E2E residue check")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
