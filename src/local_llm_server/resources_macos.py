"""macOS resource observation adapter.

Apple Silicon uses unified memory, so this adapter never invents a separate GPU
VRAM pool. Total/available host memory and current-process RSS are derived from
public OS counters; unsupported measurements remain explicitly unavailable.
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from collections.abc import Callable

from .resources import ResourceValue, ResourceValueSource, SystemResourceSnapshot

CommandRunner = Callable[[tuple[str, ...]], str]


class MacOSResourceObserver:
    def __init__(
        self,
        *,
        run_command: CommandRunner | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._run_command = run_command or _default_run_command
        self._clock = clock

    def snapshot(self) -> SystemResourceSnapshot:
        total = _read_total_memory(self._run_command)
        available = _read_available_memory(self._run_command)
        rss = _read_current_process_rss(self._run_command)
        return SystemResourceSnapshot(
            captured_at_monotonic=self._clock(),
            platform="darwin",
            total_memory_bytes=total,
            available_memory_bytes=available,
            # Apple Silicon shares system/unified memory. Reporting a separate
            # accelerator pool would double-count capacity and mislead B2.
            accelerator_memory_bytes=ResourceValue.unavailable("bytes"),
            process_rss_bytes=rss,
            thermal_pressure=ResourceValue.unavailable("level"),
        )


def _read_total_memory(run_command: CommandRunner) -> ResourceValue:
    try:
        raw = run_command(("sysctl", "-n", "hw.memsize")).strip()
        value = int(raw)
    except (OSError, ValueError, subprocess.SubprocessError):
        return ResourceValue.unavailable("bytes")
    if value <= 0:
        return ResourceValue.unavailable("bytes")
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _read_available_memory(run_command: CommandRunner) -> ResourceValue:
    """Estimate reclaimable host memory from vm_stat page counters.

    ``Pages free``, ``Pages inactive`` and ``Pages speculative`` are OS-measured
    counters. Their sum is an operational approximation for immediately free or
    reclaimable memory, not a claim about a separate GPU memory budget.
    """
    try:
        raw = run_command(("vm_stat",))
    except (OSError, subprocess.SubprocessError):
        return ResourceValue.unavailable("bytes")

    page_size = _parse_page_size(raw)
    if page_size is None:
        return ResourceValue.unavailable("bytes")

    counters = _parse_vm_stat_counters(raw)
    required = ("Pages free", "Pages inactive", "Pages speculative")
    if not all(key in counters for key in required):
        return ResourceValue.unavailable("bytes")
    pages = sum(counters[key] for key in required)
    return ResourceValue(pages * page_size, ResourceValueSource.MEASURED, "bytes")


def _read_current_process_rss(run_command: CommandRunner) -> ResourceValue:
    """Read RSS for this Local LLM Server process without treating failure as zero."""
    try:
        raw = run_command(("ps", "-o", "rss=", "-p", str(os.getpid()))).strip()
        value = int(raw) * 1024
    except (OSError, ValueError, subprocess.SubprocessError):
        return ResourceValue.unavailable("bytes")
    if value < 0:
        return ResourceValue.unavailable("bytes")
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _parse_page_size(raw: str) -> int | None:
    match = re.search(r"page size of\s+(\d+)\s+bytes", raw, flags=re.IGNORECASE)
    if not match:
        return None
    value = int(match.group(1))
    return value if value > 0 else None


def _parse_vm_stat_counters(raw: str) -> dict[str, int]:
    counters: dict[str, int] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        digits = value.strip().rstrip(".")
        try:
            counters[key.strip()] = int(digits)
        except ValueError:
            continue
    return counters


def _default_run_command(command: tuple[str, ...]) -> str:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    return result.stdout
