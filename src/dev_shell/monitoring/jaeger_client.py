from __future__ import annotations

from typing import Any

from dev_shell.utils.logger import get_logger

logger = get_logger("dev_shell.jaeger")


class JaegerClient:
    """Optional OpenTelemetry/OTLP export. Monitoring does not depend on this."""

    def __init__(
        self,
        enabled: bool = False,
        otlp_endpoint: str = "",
        service_name: str = "dev-shell",
    ) -> None:
        self.enabled = enabled and bool(otlp_endpoint)
        self.otlp_endpoint = otlp_endpoint
        self.service_name = service_name
        self._tracer = None
        if self.enabled:
            self._try_init()

    def _try_init(self) -> None:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
        except ImportError:
            logger.warning("OpenTelemetry packages are not installed; tracing remains disabled")
            self.enabled = False
            return
        try:
            provider = TracerProvider(
                resource=Resource.create({"service.name": self.service_name})
            )
            exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self.service_name)
        except Exception as exc:  # noqa: BLE001 — tracing must never terminate monitoring
            logger.warning("trace export initialization failed: %s", exc)
            self.enabled = False

    def span(self, name: str, **attributes: Any):
        if not self.enabled or self._tracer is None:
            return _NullSpan()
        span = self._tracer.start_as_current_span(name)
        return _SpanWrapper(span, attributes)


class _NullSpan:
    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _SpanWrapper:
    def __init__(self, context_manager: Any, attributes: dict[str, Any]) -> None:
        self._cm = context_manager
        self._attributes = attributes
        self._span = None

    def __enter__(self):
        self._span = self._cm.__enter__()
        for key, value in self._attributes.items():
            try:
                self._span.set_attribute(key, value)
            except Exception:
                continue
        return self._span

    def __exit__(self, *args: object):
        return self._cm.__exit__(*args)
