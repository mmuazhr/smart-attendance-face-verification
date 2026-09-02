"""Explicit liveness boundary; face matching alone is not liveness detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from presenceguard.domain import LivenessStatus


class LivenessProviderState(StrEnum):
    EXPERIMENTAL = "experimental"
    VALIDATED = "validated"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class LivenessResult:
    status: LivenessStatus
    provider: str
    state: LivenessProviderState
    message: str


class LivenessProvider:
    """Provider contract for a future validated presentation-attack detector."""

    name = "provider-interface"
    state = LivenessProviderState.UNAVAILABLE

    def check(self, _image: bytes) -> LivenessResult:
        return LivenessResult(
            status=LivenessStatus.UNAVAILABLE,
            provider=self.name,
            state=self.state,
            message="No validated liveness provider is configured",
        )


class UnavailableLivenessProvider(LivenessProvider):
    name = "none"
