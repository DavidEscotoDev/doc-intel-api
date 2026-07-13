# tests/test_telemetry.py
"""Tests for telemetry module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from opentelemetry import trace, metrics
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

from app.telemetry import setup_telemetry, record_span_error


class TestSetupTelemetry:
    """Test setup_telemetry function."""

    @patch("app.telemetry.trace.set_tracer_provider")
    @patch("app.telemetry.metrics.set_meter_provider")
    @patch("app.telemetry.FastAPIInstrumentor.instrument")
    @patch("app.telemetry.SQLAlchemyInstrumentor.instrument")
    @patch("app.telemetry.HTTPXClientInstrumentor.instrument")
    @patch("app.telemetry.PrometheusMetricReader")
    @patch("app.telemetry.MeterProvider")
    @patch("app.telemetry.TracerProvider")
    @patch("app.telemetry.Resource.create")
    def test_setup_telemetry_basic(
        self,
        mock_resource_create,
        mock_tracer_provider_class,
        mock_meter_provider_class,
        mock_prometheus_reader_class,
        mock_httpx_instrument,
        mock_sqlalchemy_instrument,
        mock_fastapi_instrument,
        mock_set_meter_provider,
        mock_set_tracer_provider,
    ) -> None:
        mock_resource = MagicMock()
        mock_resource_create.return_value = mock_resource

        mock_tracer_provider = MagicMock(spec=TracerProvider)
        mock_tracer_provider_class.return_value = mock_tracer_provider

        mock_meter_provider = MagicMock(spec=MeterProvider)
        mock_meter_provider_class.return_value = mock_meter_provider

        mock_prometheus_reader = MagicMock()
        mock_prometheus_reader_class.return_value = mock_prometheus_reader

        mock_tracer = MagicMock()
        mock_tracer_provider.get_tracer.return_value = mock_tracer

        mock_meter = MagicMock()
        mock_meter_provider.get_meter.return_value = mock_meter

        tracer, meter = setup_telemetry(
            service_name="test-service",
            sample_rate=1.0,
            enable_azure_monitor=False,
        )

        # The returned tracer is a ProxyTracer from the provider
        assert tracer is not None
        assert meter is not None

        mock_resource_create.assert_called_once()
        mock_tracer_provider_class.assert_called_once_with(resource=mock_resource)
        mock_set_tracer_provider.assert_called_once_with(mock_tracer_provider)
        mock_tracer_provider.add_span_processor.assert_called()
        mock_prometheus_reader_class.assert_called_once()
        mock_meter_provider_class.assert_called_once()
        mock_set_meter_provider.assert_called_once_with(mock_meter_provider)
        mock_fastapi_instrument.assert_called_once()
        mock_sqlalchemy_instrument.assert_called_once()
        mock_httpx_instrument.assert_called_once()

    @patch("app.telemetry.trace.set_tracer_provider")
    @patch("app.telemetry.metrics.set_meter_provider")
    @patch("app.telemetry.FastAPIInstrumentor.instrument")
    @patch("app.telemetry.SQLAlchemyInstrumentor.instrument")
    @patch("app.telemetry.HTTPXClientInstrumentor.instrument")
    @patch("app.telemetry.PrometheusMetricReader")
    @patch("app.telemetry.MeterProvider")
    @patch("app.telemetry.TracerProvider")
    @patch("app.telemetry.Resource.create")
    def test_setup_telemetry_with_azure_monitor(
        self,
        mock_resource_create,
        mock_tracer_provider_class,
        mock_meter_provider_class,
        mock_prometheus_reader_class,
        mock_httpx_instrument,
        mock_sqlalchemy_instrument,
        mock_fastapi_instrument,
        mock_set_meter_provider,
        mock_set_tracer_provider,
    ) -> None:
        mock_resource = MagicMock()
        mock_resource_create.return_value = mock_resource

        mock_tracer_provider = MagicMock(spec=TracerProvider)
        mock_tracer_provider_class.return_value = mock_tracer_provider

        mock_meter_provider = MagicMock(spec=MeterProvider)
        mock_meter_provider_class.return_value = mock_meter_provider

        mock_prometheus_reader = MagicMock()
        mock_prometheus_reader_class.return_value = mock_prometheus_reader

        mock_tracer = MagicMock()
        mock_tracer_provider.get_tracer.return_value = mock_tracer

        mock_meter = MagicMock()
        mock_meter_provider.get_meter.return_value = mock_meter

# Use a valid Azure connection string format with valid UUID
        tracer, meter = setup_telemetry(
            service_name="test-service",
            enable_azure_monitor=True,
            azure_connection_string="InstrumentationKey=12345678-1234-1234-1234-123456789012;IngestionEndpoint=https://test.in.applicationinsights.azure.com/",
        )

        assert tracer is not None
        assert meter is not None

        # Should add Azure Monitor trace exporter + console exporter
        assert mock_tracer_provider.add_span_processor.call_count == 2

        # Should add Azure Monitor metric reader
        mock_meter_provider_class.assert_called_once()
        call_args = mock_meter_provider_class.call_args
        metric_readers = call_args.kwargs.get("metric_readers", [])
        assert len(metric_readers) == 2  # Prometheus + Azure


class TestRecordSpanError:
    """Test record_span_error function."""

    def test_records_error(self) -> None:
        mock_span = MagicMock(spec=Span)
        error = ValueError("Test error")

        record_span_error(mock_span, error)

        mock_span.set_status.assert_called_once()
        status_arg = mock_span.set_status.call_args[0][0]
        assert isinstance(status_arg, Status)
        assert status_arg.status_code == StatusCode.ERROR
        assert str(error) in status_arg.description
        mock_span.record_exception.assert_called_once_with(error)


class TestMetricsExist:
    """Test that metrics are defined."""

    def test_http_requests_total(self) -> None:
        from app.telemetry import http_requests_total
        assert http_requests_total is not None

    def test_http_request_duration_seconds(self) -> None:
        from app.telemetry import http_request_duration_seconds
        assert http_request_duration_seconds is not None

    def test_documents_uploaded_total(self) -> None:
        from app.telemetry import documents_uploaded_total
        assert documents_uploaded_total is not None

    def test_documents_processed_total(self) -> None:
        from app.telemetry import documents_processed_total
        assert documents_processed_total is not None

    def test_document_processing_duration_seconds(self) -> None:
        from app.telemetry import document_processing_duration_seconds
        assert document_processing_duration_seconds is not None

    def test_active_connections(self) -> None:
        from app.telemetry import active_connections
        assert active_connections is not None

    def test_llm_tokens_used_total(self) -> None:
        from app.telemetry import llm_tokens_used_total
        assert llm_tokens_used_total is not None

    def test_llm_request_duration_seconds(self) -> None:
        from app.telemetry import llm_request_duration_seconds
        assert llm_request_duration_seconds is not None