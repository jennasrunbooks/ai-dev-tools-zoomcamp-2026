import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogRecordExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

SERVICE_NAME = "order-tracker"


def _otlp_endpoint(signal: str) -> str:
    base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    return f"{base.rstrip('/')}/v1/{signal}"


def setup_telemetry():
    resource = Resource.create({"service.name": SERVICE_NAME})
    use_otlp = os.getenv("TELEMETRY_EXPORTER", "console") == "otlp"

    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=_otlp_endpoint("traces")) if use_otlp else ConsoleSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    if use_otlp:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=_otlp_endpoint("metrics")), export_interval_millis=5000
        )
    else:
        metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=5000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    log_exporter = OTLPLogExporter(endpoint=_otlp_endpoint("logs")) if use_otlp else ConsoleLogRecordExporter()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)
    logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))
    logging.getLogger().setLevel(logging.INFO)

    return trace.get_tracer(SERVICE_NAME), metrics.get_meter(SERVICE_NAME)
