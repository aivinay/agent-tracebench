from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import replace
from statistics import median

from .models import AgentStep

_DEFAULT_REDACT_KEYS = {
    "api_key",
    "authorization",
    "completion",
    "input",
    "messages",
    "output",
    "password",
    "prompt",
    "secret",
    "token",
}

_SENSITIVE_KEY_MARKERS = {
    "apikey",
    "accesskey",
    "accesstoken",
    "authorization",
    "bearer",
    "completion",
    "credential",
    "cookie",
    "idtoken",
    "input",
    "messages",
    "output",
    "password",
    "passwd",
    "prompt",
    "refreshtoken",
    "secret",
    "session",
    "setcookie",
    "token",
}


def estimate_cost(
    steps: Iterable[AgentStep],
    *,
    input_cost_per_million: float,
    output_cost_per_million: float,
) -> dict[str, float]:
    materialized = list(steps)
    prompt_tokens = sum(step.prompt_tokens for step in materialized)
    completion_tokens = sum(step.completion_tokens for step in materialized)
    input_cost = (prompt_tokens / 1_000_000) * input_cost_per_million
    output_cost = (completion_tokens / 1_000_000) * output_cost_per_million
    return {
        "prompt_tokens": float(prompt_tokens),
        "completion_tokens": float(completion_tokens),
        "total_tokens": float(prompt_tokens + completion_tokens),
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }


def latency_outliers(
    steps: Iterable[AgentStep],
    *,
    threshold_ms: int | None = None,
    median_multiplier: float = 2.0,
) -> list[AgentStep]:
    materialized = list(steps)
    if not materialized:
        return []
    threshold = threshold_ms
    if threshold is None:
        threshold = int(median(step.latency_ms for step in materialized) * median_multiplier)
    return [step for step in materialized if step.latency_ms > threshold]


def redact_steps(
    steps: Iterable[AgentStep],
    *,
    redact_keys: set[str] | None = None,
    replacement: str = "[redacted]",
) -> list[AgentStep]:
    keys = {_normalize_key(key) for key in _DEFAULT_REDACT_KEYS}
    if redact_keys:
        keys.update(_normalize_key(key) for key in redact_keys)
    return [
        replace(step, attributes=_redact_mapping(dict(step.attributes), keys, replacement))
        for step in steps
    ]


def _redact_mapping(
    payload: dict[str, object],
    keys: set[str],
    replacement: str,
) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in payload.items():
        if _is_sensitive_key(key, keys):
            redacted[key] = replacement
        elif isinstance(value, dict):
            redacted[key] = _redact_mapping(value, keys, replacement)
        elif isinstance(value, list):
            redacted[key] = [
                _redact_mapping(item, keys, replacement) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    return redacted


def _is_sensitive_key(key: str, keys: set[str]) -> bool:
    normalized = _normalize_key(key)
    return normalized in keys or any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())
