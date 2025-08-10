"""
OpenTelemetry configuration and observability setup for TalentAI-2
"""
import os
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import start_http_server, Counter, Histogram, Gauge, Summary
import prometheus_client

# Custom metrics for TalentAI-2
class TalentAIMetrics:
    """Custom metrics for TalentAI-2 application"""
    
    def __init__(self):
        # API Metrics
        self.api_requests_total = Counter(
            'talentai_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'talentai_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        )
        
        # Resume Processing Metrics
        self.resume_processing_total = Counter(
            'talentai_resume_processing_total',
            'Total resume processing attempts',
            ['parsing_method', 'status']
        )
        
        self.resume_processing_duration = Histogram(
            'talentai_resume_processing_duration_seconds',
            'Resume processing duration in seconds',
            ['parsing_method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
        )
        
        self.resume_parsing_confidence = Histogram(
            'talentai_resume_parsing_confidence',
            'Resume parsing confidence scores',
            ['parsing_method'],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        # Search Metrics
        self.search_requests_total = Counter(
            'talentai_search_requests_total',
            'Total candidate search requests',
            ['blind_screening', 'status']
        )
        
        self.search_duration = Histogram(
            'talentai_search_duration_seconds',
            'Search request duration in seconds',
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.search_results_count = Histogram(
            'talentai_search_results_count',
            'Number of search results returned',
            buckets=[1, 5, 10, 25, 50, 100, 200, 500]
        )
        
        # ML Model Metrics
        self.ml_model_predictions = Counter(
            'talentai_ml_model_predictions_total',
            'Total ML model predictions',
            ['model_type', 'status']
        )
        
        self.ml_model_confidence = Histogram(
            'talentai_ml_model_confidence',
            'ML model confidence scores',
            ['model_type'],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        # Learning-to-Rank Metrics
        self.ltr_interactions_total = Counter(
            'talentai_ltr_interactions_total',
            'Total Learning-to-Rank interactions',
            ['interaction_type', 'recruiter_id']
        )
        
        self.ltr_weight_updates = Counter(
            'talentai_ltr_weight_updates_total',
            'Total weight updates in Learning-to-Rank'
        )
        
        # Authentication Metrics
        self.auth_attempts_total = Counter(
            'talentai_auth_attempts_total',
            'Total authentication attempts',
            ['auth_type', 'status']
        )
        
        # Database Metrics
        self.db_operations_total = Counter(
            'talentai_db_operations_total',
            'Total database operations',
            ['collection', 'operation', 'status']
        )
        
        self.db_operation_duration = Histogram(
            'talentai_db_operation_duration_seconds',
            'Database operation duration in seconds',
            ['collection', 'operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        # System Metrics
        self.active_users = Gauge(
            'talentai_active_users',
            'Currently active users',
            ['role']
        )
        
        self.system_health = Gauge(
            'talentai_system_health',
            'System health status (0=unhealthy, 1=healthy)',
            ['component']
        )
        
        # SLO Metrics
        self.slo_api_response_time = Histogram(
            'talentai_slo_api_response_time_seconds',
            'API response time for SLO monitoring',
            ['endpoint', 'method'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 2.0, 5.0]
        )
        
        self.slo_resume_processing_success = Counter(
            'talentai_slo_resume_processing_success_total',
            'Resume processing success for SLO monitoring',
            ['status']  # success, failure
        )
        
        self.slo_search_accuracy = Histogram(
            'talentai_slo_search_accuracy',
            'Search accuracy metrics for SLO monitoring',
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )

# Global metrics instance
metrics_instance = TalentAIMetrics()

def setup_observability(app_name: str = "talentai-2", enable_console: bool = False):
    """Set up OpenTelemetry observability for the application"""
    
    # Create resource
    resource = Resource.create({
        "service.name": app_name,
        "service.version": "1.0.0",
        "service.namespace": "talentai",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Set up tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # Set up metrics with Prometheus exporter
    prometheus_reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(
        resource=resource,
        metric_readers=[prometheus_reader]
    ))
    
    # Set up logging instrumentation
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    # Configure logging format for structured logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if enable_console:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/app/backend/logs/telemetry.log')
            ]
        )
    
    logger = logging.getLogger(__name__)
    logger.info(f"OpenTelemetry observability setup complete for {app_name}")
    
    return tracer, logger

def instrument_app(app):
    """Instrument FastAPI app with OpenTelemetry"""
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        excluded_urls="metrics,health"
    )
    
    # Instrument requests
    RequestsInstrumentor().instrument()
    
    # Instrument PyMongo
    PymongoInstrumentor().instrument()
    
    logger = logging.getLogger(__name__)
    logger.info("FastAPI app instrumented with OpenTelemetry")

def monitor_endpoint(endpoint_name: str, method: str = "POST"):
    """Decorator to monitor API endpoints with custom metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                
                metrics_instance.api_requests_total.labels(
                    method=method,
                    endpoint=endpoint_name,
                    status_code=str(status_code)
                ).inc()
                
                metrics_instance.api_request_duration.labels(
                    method=method,
                    endpoint=endpoint_name
                ).observe(duration)
                
                metrics_instance.slo_api_response_time.labels(
                    endpoint=endpoint_name,
                    method=method
                ).observe(duration)
        
        return wrapper
    return decorator

def monitor_resume_processing():
    """Decorator to monitor resume processing operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            parsing_method = "unknown"
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract parsing method from result if available
                if isinstance(result, dict):
                    parsing_method = result.get('parsing_method', 'basic')
                    if result.get('parsing_confidence') is not None:
                        metrics_instance.resume_parsing_confidence.labels(
                            parsing_method=parsing_method
                        ).observe(result['parsing_confidence'])
                
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                duration = time.time() - start_time
                
                metrics_instance.resume_processing_total.labels(
                    parsing_method=parsing_method,
                    status=status
                ).inc()
                
                metrics_instance.resume_processing_duration.labels(
                    parsing_method=parsing_method
                ).observe(duration)
                
                # SLO tracking
                metrics_instance.slo_resume_processing_success.labels(
                    status=status
                ).inc()
        
        return wrapper
    return decorator

def monitor_search_operation():
    """Decorator to monitor search operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            blind_screening = kwargs.get('blind_screening', False)
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Track result count
                if isinstance(result, list):
                    metrics_instance.search_results_count.observe(len(result))
                    
                    # Calculate search accuracy (simplified - based on result confidence)
                    if result:
                        avg_score = sum(getattr(r, 'total_score', 0) for r in result) / len(result)
                        metrics_instance.slo_search_accuracy.observe(avg_score)
                
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                duration = time.time() - start_time
                
                metrics_instance.search_requests_total.labels(
                    blind_screening=str(blind_screening),
                    status=status
                ).inc()
                
                metrics_instance.search_duration.observe(duration)
        
        return wrapper
    return decorator

def monitor_ml_model(model_type: str):
    """Decorator to monitor ML model operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract confidence if available
                if hasattr(result, 'confidence_score'):
                    metrics_instance.ml_model_confidence.labels(
                        model_type=model_type
                    ).observe(result.confidence_score)
                
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                metrics_instance.ml_model_predictions.labels(
                    model_type=model_type,
                    status=status
                ).inc()
        
        return wrapper
    return decorator

def monitor_database_operation(collection: str, operation: str):
    """Decorator to monitor database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failure"
                raise
            finally:
                duration = time.time() - start_time
                
                metrics_instance.db_operations_total.labels(
                    collection=collection,
                    operation=operation,
                    status=status
                ).inc()
                
                metrics_instance.db_operation_duration.labels(
                    collection=collection,
                    operation=operation
                ).observe(duration)
        
        return wrapper
    return decorator

# Health check functions
def update_system_health(component: str, healthy: bool):
    """Update system health status"""
    metrics_instance.system_health.labels(component=component).set(1 if healthy else 0)

def update_active_users(role: str, count: int):
    """Update active users count"""
    metrics_instance.active_users.labels(role=role).set(count)

# SLO tracking functions
class SLOTracker:
    """Track Service Level Objectives"""
    
    @staticmethod
    def track_api_response_time(endpoint: str, method: str, duration: float):
        """Track API response time for SLO monitoring"""
        metrics_instance.slo_api_response_time.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)
    
    @staticmethod
    def track_resume_processing_success(success: bool):
        """Track resume processing success for SLO monitoring"""
        status = "success" if success else "failure"
        metrics_instance.slo_resume_processing_success.labels(status=status).inc()
    
    @staticmethod
    def track_search_accuracy(accuracy: float):
        """Track search accuracy for SLO monitoring"""
        metrics_instance.slo_search_accuracy.observe(accuracy)

# Export the SLO tracker
slo_tracker = SLOTracker()

def start_prometheus_server(port: int = 8000):
    """Start Prometheus metrics server"""
    try:
        start_http_server(port)
        logger = logging.getLogger(__name__)
        logger.info(f"Prometheus metrics server started on port {port}")
        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to start Prometheus server: {e}")
        return False