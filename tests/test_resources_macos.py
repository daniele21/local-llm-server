from __future__ import annotations

from local_llm_server.resources import ResourceValueSource
from local_llm_server.resources_macos import MacOSResourceObserver


def test_macos_observer_reads_total_and_reclaimable_memory_without_fake_vram():
    outputs = {
        ("sysctl", "-n", "hw.memsize"): "17179869184\n",
        ("vm_stat",): """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               100.
Pages active:                             500.
Pages inactive:                           200.
Pages speculative:                         50.
Pages wired down:                         300.
""",
    }

    observer = MacOSResourceObserver(
        run_command=lambda command: outputs[command],
        clock=lambda: 42.0,
    )
    snapshot = observer.snapshot()

    assert snapshot.captured_at_monotonic == 42.0
    assert snapshot.total_memory_bytes.value == 17179869184
    assert snapshot.total_memory_bytes.source is ResourceValueSource.MEASURED
    assert snapshot.available_memory_bytes.value == (100 + 200 + 50) * 16384
    assert snapshot.available_memory_bytes.source is ResourceValueSource.MEASURED
    assert snapshot.accelerator_memory_bytes.value is None
    assert snapshot.accelerator_memory_bytes.source is ResourceValueSource.UNAVAILABLE


def test_macos_observer_fails_closed_when_vm_stat_is_incomplete():
    def run(command):
        if command[0] == "sysctl":
            return "8589934592\n"
        return "Mach Virtual Memory Statistics: (page size of 4096 bytes)\nPages free: 10.\n"

    snapshot = MacOSResourceObserver(run_command=run).snapshot()

    assert snapshot.total_memory_bytes.value == 8589934592
    assert snapshot.available_memory_bytes.value is None


def test_macos_observer_fails_closed_when_commands_fail():
    def run(_command):
        raise OSError("unavailable")

    snapshot = MacOSResourceObserver(run_command=run).snapshot()

    assert snapshot.total_memory_bytes.value is None
    assert snapshot.available_memory_bytes.value is None
