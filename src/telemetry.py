"""
Basic telemetry module for ai-proxy-core
Provides minimal observability with OpenTelemetry
"""
import os
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class NoOpCounter:
    """No-op counter implementation"""
    def add(self, amount: int, attributes: Dict[str, Any] = None):
        pass


class NoOpTelemetry:
    """No-op implementation when OpenTelemetry is not available"""
    def __init__(self):
        self.request_counter = NoOpCounter()
    
    def create_counter(self, name: str, description: str = ""):
        return NoOpCounter()
    
    def add(self, amount: int, attributes: Dict[str, Any] = None):
        pass
    
    def record(self, value: float, attributes: Dict[str, Any] = None):
        """No-op record for histogram compatibility"""
        pass
    
    @contextmanager
    def track_duration(self, name: str, attributes: Dict[str, Any] = None):
        yield
    
    def record_duration(self, name: str, duration: float, attributes: Dict[str, Any] = None):
        pass


class TelemetryManager:
    """Minimal telemetry manager for basic observability"""
    
    def __init__(self, service_name: str = "ai-proxy-core", enabled: bool = True):
        self.enabled = enabled and OTEL_AVAILABLE
        self.service_name = service_name
        
        if not self.enabled:
            self._no_op = NoOpTelemetry()
            # Make all the same attributes available when disabled
            self.request_counter = self._no_op.request_counter
            self.duration_histogram = self._no_op
            return
            
        # Setup resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "0.1.8"
        })
        
        # Setup tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(service_name)
        
        # Setup metrics
        metrics.set_meter_provider(MeterProvider(resource=resource))
        self.meter = metrics.get_meter(service_name)
        
        # Configure exporters based on environment
        self._setup_exporters()
        
        # Create reusable instruments
        self.request_counter = self.meter.create_counter(
            name="ai_proxy.requests",
            description="Total API requests",
            unit="request"
        )
        
        self.duration_histogram = self.meter.create_histogram(
            name="ai_proxy.duration",
            description="Operation duration",
            unit="ms"
        )
    
    def _setup_exporters(self):
        """Setup exporters based on OTEL_EXPORTER_TYPE env var"""
        exporter_type = os.getenv("OTEL_EXPORTER_TYPE", "none")
        
        if exporter_type == "console":
            # Console exporters for development
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            metrics.get_meter_provider().add_metric_reader(reader)
            
        elif exporter_type == "otlp":
            # OTLP exporters for production
            endpoint = os.getenv("OTEL_ENDPOINT", "localhost:4317")
            
            # Traces
            span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(span_exporter)
            )
            
            # Metrics
            metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
            reader = PeriodicExportingMetricReader(metric_exporter)
            metrics.get_meter_provider().add_metric_reader(reader)
    
    def create_counter(self, name: str, description: str = ""):
        """Create a counter instrument"""
        if not self.enabled:
            return self._no_op
        return self.meter.create_counter(name=name, description=description)
    
    @contextmanager
    def track_duration(self, name: str, attributes: Dict[str, Any] = None):
        """Context manager to track operation duration"""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.duration_histogram.record(duration_ms, attributes or {})
    
    def record_duration(self, name: str, duration: float, attributes: Dict[str, Any] = None):
        """Record a duration measurement"""
        if not self.enabled:
            return
        attrs = {"operation": name}
        if attributes:
            attrs.update(attributes)
        self.duration_histogram.record(duration, attrs)


# Global instance (lazy initialization)
_telemetry_instance: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """Get or create the global telemetry instance"""
    global _telemetry_instance
    if _telemetry_instance is None:
        enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
        _telemetry_instance = TelemetryManager(enabled=enabled)
    return _telemetry_instance