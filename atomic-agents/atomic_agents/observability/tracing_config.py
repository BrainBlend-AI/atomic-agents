"""Tracing configuration and payload visibility."""

import os
from dataclasses import dataclass
from typing import Protocol


class PayloadVisibility(Protocol):
    hide_inputs: bool
    hide_outputs: bool


@dataclass(frozen=True)
class TracingConfig:
    hide_inputs: bool = False
    hide_outputs: bool = False
    max_attribute_length: int = 4096
    openinference_attributes: bool | None = None
    llm_spans: bool = True

    @classmethod
    def from_environment(cls) -> "TracingConfig":
        return cls(
            hide_inputs=_visibility_environment("INPUTS").lower() in ("true", "1"),
            hide_outputs=_visibility_environment("OUTPUTS").lower() in ("true", "1"),
            max_attribute_length=int(os.environ.get("ATOMIC_AGENTS_TRACE_MAX_ATTRIBUTE_LENGTH", "4096")),
        )

    @classmethod
    def coerce(cls, config: "TracingConfig | PayloadVisibility | None") -> "TracingConfig":
        if config is None:
            return cls.from_environment()
        if isinstance(config, cls):
            return config
        return cls(hide_inputs=config.hide_inputs, hide_outputs=config.hide_outputs)


def _visibility_environment(direction: str) -> str:
    return os.environ.get(f"ATOMIC_AGENTS_TRACE_HIDE_{direction}", os.environ.get(f"OPENINFERENCE_HIDE_{direction}", ""))
