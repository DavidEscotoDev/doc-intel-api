# ADR 005: Observability with OpenTelemetry + Prometheus + Azure Monitor

## Context
Production systems require visibility into latency, errors, and throughput. The observability stack must work locally and in Azure.

## Decision
Implement **three-layer observability**:

| Layer | Tool | Purpose |
|-------|------|---------|
| **Metrics** | Prometheus Client | Custom business metrics, latency histograms |
| **Tracing** | OpenTelemetry SDK | Distributed traces, span attributes |
| **Logging** | structlog + JSON | Structured logs with correlation IDs |

### Export Targets
| Environment | Traces | Metrics |
|-------------|--------|---------|
| **Local** | Console | Prometheus `/metrics` endpoint |
| **Azure** | Azure Monitor | Azure Monitor + Prometheus |

## Implementation

### Metrics (Prometheus)
```python
# app/telemetry.py
http_requests_total = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
http_request_duration = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])
documents_uploaded = Counter("documents_uploaded_total", "Documents uploaded", ["status"])
documents_processed = Counter("documents_processed_total", "Documents processed", ["status"])
llm_tokens_used = Counter("llm_tokens_used_total", "LLM tokens consumed", ["model", "type"])
```

### Tracing (OpenTelemetry)
```python
# app/telemetry.py
tracer = trace.get_tracer(__name__)

# In route handlers
with tracer.start_as_current_span("upload_document") as span:
    span.set_attribute("document.id", str(doc.id))
    span.set_attribute("document.size", file_size)
```

### Structured Logging
```python
# app/logging.py
logger = structlog.get_logger(__name__)

logger.info("document_uploaded", document_id=str(doc.id), size=file_size, api_key_id=str(api_key.id))
```

### Health Checks
```python
# app/routes/health.py
@router.get("/health/ready")
async def readiness_probe(db: AsyncSession):
    await db.execute(text("SELECT 1"))
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_probe():
    return {"status": "alive"}
```

## Consequences

### Positive
- **Local dev**: Console traces + Prometheus UI
- **Azure prod**: Native Azure Monitor integration
- **Vendor-neutral**: OpenTelemetry standard
- **Custom metrics**: Business KPIs (tokens, docs, latency)

### Negative
- Additional dependencies (OTel, Prometheus client)
- Configuration complexity (sampling, exporters)
- Cardinality risk (high-cardinality labels)

## Key Metrics to Monitor
| Metric | Alert Threshold |
|--------|-----------------|
| `http_request_duration_seconds` p99 | > 5s |
| `http_requests_total` 5xx rate | > 1% |
| `documents_processed_total{status="failed"}` | > 5% |
| `llm_tokens_used_total` daily | Budget alert |

## Alternatives Considered
- **Datadog / New Relic**: SaaS, expensive at scale
- **Grafana Loki only**: No tracing, metrics limited
- **Azure Monitor only**: Vendor lock-in, no local parity

## Implementation Priority
1. Prometheus metrics + `/metrics` endpoint ✓
2. OpenTelemetry tracing (console exporter) ✓
3. Structured JSON logging ✓
4. Azure Monitor exporter (prod) ✓
5. Grafana dashboards (next)
6. Alert rules (next)