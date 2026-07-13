# app/telemetry.py
"""OpenTelemetry configuration for distributed tracing and metrics."""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, MetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import Status, StatusCode
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional


# Prometheus metrics (always available)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

documents_uploaded_total = Counter(
    "documents_uploaded_total",
    "Total documents uploaded",
    ["status"],
)

documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed",
    ["status"],
)

document_processing_duration_seconds = Histogram(
    "document_processing_duration_seconds",
    "Document processing duration in seconds",
)

active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)

llm_tokens_used_total = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["model", "type"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model"],
)


def setup_telemetry(
    service_name: str = "document-intelligence-api",
    sample_rate: float = 1.0,
    enable_azure_monitor: bool = False,
    azure_connection_string: Optional[str] = None,
) -> tuple[trace.Tracer, metrics.Meter]:
    """Initialize OpenTelemetry tracing and metrics."""

    resource = Resource.create({SERVICE_NAME: service_name})

    # Tracing
    tracer_provider = TracerProvider(resource=resource)

    # Add Azure Monitor exporter if configured
    if enable_azure_monitor and azure_connection_string:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        azure_exporter = AzureMonitorTraceExporter(
            connection_string=azure_connection_string
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(azure_exporter))

    # Always add console exporter for development
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)

    # Metrics
    prometheus_reader = PrometheusMetricReader()
    metric_readers: list[MetricReader] = [prometheus_reader]

    if enable_azure_monitor and azure_connection_string:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
        azure_metric_exporter = AzureMonitorMetricExporter(
            connection_string=azure_connection_string
        )
        metric_readers.append(
            PeriodicExportingMetricReader(azure_metric_exporter)
        )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
    )
    metrics.set_meter_provider(meter_provider)

    # Auto-instrumentation
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()

    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    return tracer, meter


def record_span_error(span: trace.Span, error: Exception) -> None:
    """Record an error on the current span."""
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)