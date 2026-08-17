import json
import logging
import os
import sys

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server


class TraceJsonFormatter(logging.Formatter):
    def format(self, record):
        ctx = trace.get_current_span().get_span_context()
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "severity": record.levelname,
            "message": record.getMessage(),
            "service.name": os.getenv("SERVICE_NAME", "unknown"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "local"),
            "trace_id": format(ctx.trace_id, "032x") if ctx.is_valid else "",
            "span_id": format(ctx.span_id, "016x") if ctx.is_valid else "",
        }
        return json.dumps(payload, ensure_ascii=False)


def configure_telemetry(app):
    service = os.getenv("SERVICE_NAME", "unknown")
    resource = Resource.create({"service.name": service, "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "local")})
    if os.getenv("OTEL_SDK_DISABLED", "false").lower() != "true":
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(insecure=True)))
        trace.set_tracer_provider(tracer_provider)
        metric_reader = PrometheusMetricReader()
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(insecure=True)))
        set_logger_provider(logger_provider)
        otlp_handler = LoggingHandler(logger_provider=logger_provider)
        # Keep the trace identifiers inside the body as well as OTLP metadata.
        # Grafana derived fields can then pivot directly from a log line.
        otlp_handler.setFormatter(TraceJsonFormatter())
        logging.getLogger().addHandler(otlp_handler)
    port = int(os.getenv("METRICS_PORT", "9464"))
    start_http_server(port)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(TraceJsonFormatter())
    root = logging.getLogger()
    root.addHandler(console)
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
