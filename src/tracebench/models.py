from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


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
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if self.started_at_ms < 0 or self.ended_at_ms < 0:
            raise ValueError("started_at_ms and ended_at_ms must be non-negative")
        if self.ended_at_ms < self.started_at_ms:
            raise ValueError("ended_at_ms must be greater than or equal to started_at_ms")
        if self.prompt_tokens < 0 or self.completion_tokens < 0:
            raise ValueError("token counts must be non-negative")
        if self.status not in {"ok", "error"}:
            raise ValueError("status must be 'ok' or 'error'")
        if not isinstance(self.attributes, Mapping):
            raise ValueError("attributes must be an object")

    @property
    def latency_ms(self) -> int:
        return self.ended_at_ms - self.started_at_ms

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "status": self.status,
            "attributes": dict(self.attributes),
        }
        if self.error_type:
            payload["error_type"] = self.error_type
        if self.trace_id:
            payload["trace_id"] = self.trace_id
        if self.span_id:
            payload["span_id"] = self.span_id
        if self.parent_span_id:
            payload["parent_span_id"] = self.parent_span_id
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> AgentStep:
        attributes = payload.get("attributes", {})
        if not isinstance(attributes, Mapping):
            raise ValueError("attributes must be an object")

        return cls(
            name=str(_required(payload, "name")),
            started_at_ms=_coerce_int(_required(payload, "started_at_ms"), "started_at_ms"),
            ended_at_ms=_coerce_int(_required(payload, "ended_at_ms"), "ended_at_ms"),
            prompt_tokens=_coerce_int(payload.get("prompt_tokens", 0), "prompt_tokens"),
            completion_tokens=_coerce_int(payload.get("completion_tokens", 0), "completion_tokens"),
            status=str(payload.get("status", "ok")),
            error_type=_optional_string(payload.get("error_type")),
            attributes=dict(attributes),
            trace_id=_optional_string(payload.get("trace_id")),
            span_id=_optional_string(payload.get("span_id")),
            parent_span_id=_optional_string(payload.get("parent_span_id")),
        )


def _required(payload: Mapping[str, object], key: str) -> object:
    if key not in payload:
        raise ValueError(f"{key} is required")
    return payload[key]


def _coerce_int(value: object, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
