"""
Opt-in OpenInference tracing for Atomic Agents.

Emits an AGENT span per ``AtomicAgent`` run and a TOOL span per ``BaseTool`` run, rendered by
Arize Phoenix and any other OpenTelemetry backend. Needs the ``observability`` extra:
``pip install "atomic-agents[observability]"``. Phoenix discovers :class:`AtomicAgentsInstrumentor`
through the ``openinference_instrumentor`` entry point, so ``phoenix.otel.register(auto_instrument=True)``
activates it without further code. See ``docs/guides/observability.md``.
"""

import importlib.util
import logging
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from openinference.instrumentation import TraceConfig
    from opentelemetry.trace import TracerProvider

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Atomic Agents observability needs the OpenInference packages. "
    'Install them with: pip install "atomic-agents[observability]"'
)
_OPENINFERENCE_DISTRIBUTION = "openinference-instrumentation"
_MINIMUM_OPENINFERENCE_VERSION = (0, 1, 38)


def _openinference_is_installed() -> bool:
    return importlib.util.find_spec("openinference") is not None


def _openinference_is_too_old() -> bool:
    try:
        installed = version(_OPENINFERENCE_DISTRIBUTION)
    except PackageNotFoundError:
        return True
    release = tuple(int(part) for part in installed.split(".")[:3] if part.isdigit())
    return release < _MINIMUM_OPENINFERENCE_VERSION


def _import_tracing_module() -> ModuleType:
    from atomic_agents.observability import openinference_tracing

    return openinference_tracing


def _load_tracing_module() -> ModuleType | None:
    if _openinference_is_too_old():
        logger.warning(
            "Atomic Agents tracing is disabled: %s %s or newer is required.",
            _OPENINFERENCE_DISTRIBUTION,
            ".".join(str(part) for part in _MINIMUM_OPENINFERENCE_VERSION),
        )
        return None
    return _import_tracing_module()


class AtomicAgentsInstrumentor:
    """
    Installs OpenInference AGENT and TOOL spans around ``AtomicAgent`` and ``BaseTool`` calls.

    The public surface mirrors OpenTelemetry's ``BaseInstrumentor`` (``instrument`` / ``uninstrument``)
    without depending on it, because Arize Phoenix only guarantees ``opentelemetry-api`` and
    ``openinference-instrumentation`` in an auto-instrumented environment.
    """

    def instrument(
        self,
        *,
        tracer_provider: Optional["TracerProvider"] = None,
        config: Optional["TraceConfig"] = None,
        **options: object,
    ) -> None:
        """
        Patch the framework classes. Safe to call more than once; a second call with different
        arguments logs a warning and keeps the first installation.

        Args:
            tracer_provider: An OpenTelemetry ``TracerProvider``. Defaults to the global provider.
            config: An ``openinference.instrumentation.TraceConfig`` (for example ``hide_inputs=True``).
            **options: Launcher options accepted for OpenTelemetry auto-instrumentation compatibility.

        Raises:
            ModuleNotFoundError: When the ``observability`` extra is not installed, except during
                OpenTelemetry auto-discovery, which skips unavailable optional instrumentation.
        """
        if not _openinference_is_installed():
            if options.get("skip_dep_check") is True:
                logger.debug(_INSTALL_HINT)
                return
            raise ModuleNotFoundError(_INSTALL_HINT)
        tracing = _load_tracing_module()
        if tracing is not None:
            tracing.install(tracer_provider=tracer_provider, config=config)

    def uninstrument(self) -> None:
        """Restore the original framework methods. No-op when nothing is installed."""
        if not self.is_instrumented_by_opentelemetry:
            return
        _import_tracing_module().uninstall()

    @property
    def is_instrumented_by_opentelemetry(self) -> bool:
        if not _openinference_is_installed() or _openinference_is_too_old():
            return False
        return _import_tracing_module().is_installed()


__all__ = ["AtomicAgentsInstrumentor"]
