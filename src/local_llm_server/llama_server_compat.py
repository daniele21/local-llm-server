"""Version attribution and compatibility policy for external ``llama-server``.

Local LLM Server does not download or silently replace the specialist runtime.
Instead it validates the executable it is about to own. The current validated
stable floor is llama.cpp v0.3.0 / build b10621; newer build numbers are accepted
under the same compatibility level until a future repository change raises the
validated floor.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

LLAMA_CPP_VALIDATED_RELEASE = "v0.3.0"
LLAMA_CPP_VALIDATED_MIN_BUILD = 10621
LLAMA_CPP_VALIDATED_RELEASE_COMMIT = "c1d0e7a004015f23bc0233470b747b596f29b264"

_VERSION_PATTERN = re.compile(
    r"version:\s*(?P<build>\d+)\s*\(`?(?P<commit>[0-9a-fA-F]{7,40})`?\)"
)

CommandRunner = Callable[[Path], str]


@dataclass(frozen=True, slots=True)
class LlamaServerBuildIdentity:
    build: int
    commit: str

    @property
    def backend_version(self) -> str:
        return f"build-{self.build}@{self.commit}"


@dataclass(frozen=True, slots=True)
class LlamaServerCompatibility:
    identity: LlamaServerBuildIdentity | None
    validated: bool
    validated_release: str = LLAMA_CPP_VALIDATED_RELEASE
    minimum_build: int = LLAMA_CPP_VALIDATED_MIN_BUILD

    @property
    def backend_version(self) -> str | None:
        if self.identity is None:
            return None
        return self.identity.backend_version

    @property
    def modern_runtime_options(self) -> bool:
        return bool(
            self.identity is not None
            and self.identity.build >= self.minimum_build
        )


def parse_llama_server_version(text: str) -> LlamaServerBuildIdentity | None:
    """Parse the stable ``llama-server --version`` build/commit identity."""
    match = _VERSION_PATTERN.search(text)
    if match is None:
        return None
    build = int(match.group("build"))
    if build <= 0:
        return None
    return LlamaServerBuildIdentity(
        build=build,
        commit=match.group("commit").lower(),
    )


def probe_llama_server_version(
    binary: Path | str,
    *,
    run_command: CommandRunner | None = None,
) -> LlamaServerBuildIdentity | None:
    """Return attributable build identity, or ``None`` when it cannot be proven."""
    path = Path(str(binary)).expanduser()
    runner = run_command or _default_runner
    try:
        output = runner(path)
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_llama_server_version(output)


def validate_llama_server_binary(
    binary: Path | str,
    *,
    allow_unvalidated: bool = False,
    run_command: CommandRunner | None = None,
) -> LlamaServerCompatibility:
    """Validate an external server against the repository's stable feature floor.

    ``allow_unvalidated`` is a compatibility escape hatch for deliberate legacy
    operation. Such a runtime does not receive v0.3.0-only command-line options
    and is never presented as validated against the current stable floor.
    """
    identity = probe_llama_server_version(binary, run_command=run_command)
    if identity is None:
        if allow_unvalidated:
            return LlamaServerCompatibility(identity=None, validated=False)
        raise RuntimeError(
            "Cannot verify llama-server version. Local LLM Server requires an "
            f"attributable llama.cpp {LLAMA_CPP_VALIDATED_RELEASE}+ executable "
            "for the managed llama_server backend. Set LOCAL_LLM_SERVER_BIN to "
            "that binary, or explicitly allow an unvalidated legacy runtime."
        )

    if identity.build < LLAMA_CPP_VALIDATED_MIN_BUILD:
        if allow_unvalidated:
            return LlamaServerCompatibility(identity=identity, validated=False)
        raise RuntimeError(
            "llama-server is older than the validated runtime floor: "
            f"found build {identity.build}, require build "
            f"{LLAMA_CPP_VALIDATED_MIN_BUILD}+ "
            f"({LLAMA_CPP_VALIDATED_RELEASE} or newer)."
        )

    return LlamaServerCompatibility(identity=identity, validated=True)


def _default_runner(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
        timeout=2.0,
        check=False,
    )
    return "\n".join(
        part for part in (completed.stdout, completed.stderr) if part
    )
