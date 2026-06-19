from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class AgentStep:
    name: str
    started_at_ms: int
    ended_at_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    status: str = "ok"
    error_type: str | None = None
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ended_at_ms < self.started_at_ms:
            raise ValueError("ended_at_ms must be greater than or equal to started_at_ms")
        if self.prompt_tokens < 0 or self.completion_tokens < 0:
            raise ValueError("token counts must be non-negative")

    @property
    def latency_ms(self) -> int:
        return self.ended_at_ms - self.started_at_ms

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AgentStep":
        return cls(
            name=str(payload["name"]),
            started_at_ms=int(payload["started_at_ms"]),
            ended_at_ms=int(payload["ended_at_ms"]),
            prompt_tokens=int(payload.get("prompt_tokens", 0)),
            completion_tokens=int(payload.get("completion_tokens", 0)),
            status=str(payload.get("status", "ok")),
            error_type=_optional_string(payload.get("error_type")),
            attributes=dict(payload.get("attributes", {})),
        )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
