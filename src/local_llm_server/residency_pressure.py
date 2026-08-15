"""Deterministic pressure-to-eviction policy evaluation.

This module intentionally does not unload runtimes. It converts sampled resource
pressure into a bounded policy decision and delegates candidate ranking to the
existing residency selector. Real automatic eviction remains disabled until
representative hardware evidence supports it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .residency_eviction import (
    EvictionCandidate,
    EvictionMode,
    EvictionPolicySettings,
    select_eviction_candidates,
)
from .resources import ResourcePressure


_PRESSURE_RANK = {
    ResourcePressure.NORMAL: 0,
    ResourcePressure.ELEVATED: 1,
    ResourcePressure.CRITICAL: 2,
}


class PressurePolicyState(str, Enum):
    NORMAL = "normal"
    WATCHING = "watching"
    TRIGGERED = "triggered"


@dataclass(frozen=True, slots=True)
class PressurePolicySettings:
    trigger_pressure: ResourcePressure = ResourcePressure.CRITICAL
    consecutive_trigger_samples: int = 2
    clear_pressure: ResourcePressure = ResourcePressure.NORMAL
    consecutive_clear_samples: int = 2
    candidate_limit: int = 1
    protect_resident_default: bool = True

    def __post_init__(self) -> None:
        if self.trigger_pressure is ResourcePressure.UNKNOWN:
            raise ValueError("trigger_pressure cannot be unknown")
        if self.clear_pressure is ResourcePressure.UNKNOWN:
            raise ValueError("clear_pressure cannot be unknown")
        if self.consecutive_trigger_samples < 1:
            raise ValueError("consecutive_trigger_samples must be >= 1")
        if self.consecutive_clear_samples < 1:
            raise ValueError("consecutive_clear_samples must be >= 1")
        if self.candidate_limit < 1:
            raise ValueError("candidate_limit must be >= 1")
        if _PRESSURE_RANK[self.clear_pressure] >= _PRESSURE_RANK[self.trigger_pressure]:
            raise ValueError("clear_pressure must be lower than trigger_pressure")


@dataclass(frozen=True, slots=True)
class PressurePolicyEvaluation:
    pressure: ResourcePressure
    state: PressurePolicyState
    trigger_streak: int
    clear_streak: int
    transition: str | None
    candidates: tuple[EvictionCandidate, ...] = ()

    @property
    def should_attempt_eviction(self) -> bool:
        return self.transition == "triggered" and bool(self.candidates)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "pressure": self.pressure.value,
            "state": self.state.value,
            "trigger_streak": self.trigger_streak,
            "clear_streak": self.clear_streak,
            "transition": self.transition,
            "should_attempt_eviction": self.should_attempt_eviction,
            "candidates": [candidate.to_public_dict() for candidate in self.candidates],
            "automatic_eviction_enabled": False,
            "reclamation_claim": False,
        }


class PressureEvictionPolicy:
    """Hysteretic pressure evaluator with one bounded action per pressure episode.

    A pressure episode begins only after the configured number of consecutive
    samples at or above ``trigger_pressure``. Once triggered, additional high
    samples do not repeatedly emit eviction attempts. The policy re-arms only
    after enough samples at or below ``clear_pressure``. ``UNKNOWN`` samples are
    fail-conservative: they emit no action and do not clear an already-triggered
    episode.
    """

    def __init__(self, settings: PressurePolicySettings | None = None) -> None:
        self.settings = settings or PressurePolicySettings()
        self._state = PressurePolicyState.NORMAL
        self._trigger_streak = 0
        self._clear_streak = 0

    @property
    def state(self) -> PressurePolicyState:
        return self._state

    def observe(
        self,
        pressure: ResourcePressure,
        residency_snapshot: Mapping[str, Any],
    ) -> PressurePolicyEvaluation:
        transition: str | None = None
        candidates: tuple[EvictionCandidate, ...] = ()

        if pressure is ResourcePressure.UNKNOWN:
            self._trigger_streak = 0
            self._clear_streak = 0
            return self._evaluation(pressure, transition, candidates)

        rank = _PRESSURE_RANK[pressure]
        trigger_rank = _PRESSURE_RANK[self.settings.trigger_pressure]
        clear_rank = _PRESSURE_RANK[self.settings.clear_pressure]

        if self._state is PressurePolicyState.TRIGGERED:
            if rank <= clear_rank:
                self._clear_streak += 1
                if self._clear_streak >= self.settings.consecutive_clear_samples:
                    self._state = PressurePolicyState.NORMAL
                    self._trigger_streak = 0
                    self._clear_streak = 0
                    transition = "cleared"
            else:
                self._clear_streak = 0
            return self._evaluation(pressure, transition, candidates)

        self._clear_streak = 0
        if rank >= trigger_rank:
            self._trigger_streak += 1
            self._state = PressurePolicyState.WATCHING
            if self._trigger_streak >= self.settings.consecutive_trigger_samples:
                self._state = PressurePolicyState.TRIGGERED
                transition = "triggered"
                candidates = select_eviction_candidates(
                    residency_snapshot,
                    EvictionPolicySettings(
                        mode=EvictionMode.LRU,
                        limit=self.settings.candidate_limit,
                        protect_resident_default=self.settings.protect_resident_default,
                    ),
                )
        else:
            self._trigger_streak = 0
            self._state = PressurePolicyState.NORMAL

        return self._evaluation(pressure, transition, candidates)

    def _evaluation(
        self,
        pressure: ResourcePressure,
        transition: str | None,
        candidates: tuple[EvictionCandidate, ...],
    ) -> PressurePolicyEvaluation:
        return PressurePolicyEvaluation(
            pressure=pressure,
            state=self._state,
            trigger_streak=self._trigger_streak,
            clear_streak=self._clear_streak,
            transition=transition,
            candidates=candidates,
        )
