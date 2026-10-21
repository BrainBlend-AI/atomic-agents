"""
Opt-in OpenTelemetry tracing for Atomic Agents.

Emits an AGENT span per ``AtomicAgent`` run and a TOOL span per ``BaseTool`` run, rendered by
Arize Phoenix and any other OpenTelemetry backend. Needs the ``observability`` extra:
``pip install "atomic-agents[observability]"``. Phoenix discovers :class:`AtomicAgentsInstrumentor`
through the ``openinference_instrumentor`` entry point, so ``phoenix.otel.register(auto_instrument=True)``
activates it without further code. See ``docs/guides/observability.md``.
"""

import importlib.util
import logging
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from atomic_agents.observability.tracing import PayloadVisibility, TracingConfig
    from opentelemetry.trace import TracerProvider

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Atomic Agents observability needs the OpenInference packages. "
    'Install them with: pip install "atomic-agents[observability]"'
)
_OPENINFERENCE_DISTRIBUTION = "openinference-instrumentation"
_MINIMUM_OPENINFERENCE_VERSION = (0, 1, 38)


def _opentelemetry_is_installed() -> bool:
    try:
        return importlib.util.find_spec("opentelemetry.trace") is not None
    except ModuleNotFoundError:
        return False


def _openinference_is_too_old() -> bool:
    try:
        installed = version(_OPENINFERENCE_DISTRIBUTION)
    except PackageNotFoundError:
        return True
    release = tuple(int(part) for part in installed.split(".")[:3] if part.isdigit())
    return release < _MINIMUM_OPENINFERENCE_VERSION


def _load_tracing_module():
    from atomic_agents.observability import tracing

    return tracing


def __getattr__(name: str) -> object:
    if name == "TracingConfig":
        return _load_tracing_module().TracingConfig
    raise AttributeError(name)


class AtomicAgentsInstrumentor:
    """
    Installs AGENT and TOOL spans around ``AtomicAgent`` and ``BaseTool`` calls.

    The public surface mirrors OpenTelemetry's ``BaseInstrumentor`` (``instrument`` / ``uninstrument``)
    without depending on it, because Arize Phoenix only guarantees ``opentelemetry-api`` and
    ``openinference-instrumentation`` in an auto-instrumented environment.
    """

    def instrument(
        self,
        *,
        tracer_provider: "TracerProvider | None" = None,
        config: "TracingConfig | PayloadVisibility | None" = None,
        **options: object,
    ) -> None:
        """
        Patch the framework classes. Safe to call more than once; a second call with different
        arguments logs a warning and keeps the first installation.

        Args:
            tracer_provider: An OpenTelemetry ``TracerProvider``. Defaults to the global provider.
            config: Payload visibility and truncation settings. OpenInference TraceConfig is also accepted.
            **options: Launcher options accepted for OpenTelemetry auto-instrumentation compatibility.

        Raises:
            ModuleNotFoundError: When the ``observability`` extra is not installed, except during
                OpenTelemetry auto-discovery, which skips unavailable optional instrumentation.
        """
        if not _opentelemetry_is_installed():
            if options.get("skip_dep_check") is True:
                logger.debug(_INSTALL_HINT)
                return
            raise ModuleNotFoundError(_INSTALL_HINT)
        _load_tracing_module().install(tracer_provider=tracer_provider, config=config)

    def uninstrument(self) -> None:
        """Restore the original framework methods. No-op when nothing is installed."""
        if not self.is_instrumented_by_opentelemetry:
            return
        _load_tracing_module().uninstall()

    @property
    def is_instrumented_by_opentelemetry(self) -> bool:
        if not _opentelemetry_is_installed():
            return False
        return _load_tracing_module().is_installed()


__all__ = ["AtomicAgentsInstrumentor", "TracingConfig"]
