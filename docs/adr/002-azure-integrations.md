# ADR 002: Azure-Native Integrations

## Context
The API targets Azure as its primary cloud platform. Using Azure-native services reduces operational overhead and leverages managed services.

## Decision
Integrate with **Azure native services** for storage, secrets, and observability:

| Service | Azure Service | Purpose |
|---------|---------------|---------|
| **File Storage** | Azure Blob Storage | Store uploaded documents |
| **Secrets Management** | Azure Key Vault | Store API keys, connection strings |
| **Observability** | Azure Monitor + Application Insights | Distributed tracing, metrics, logging |
| **Container Hosting** | Azure Container Apps / AKS | Production deployment |

## Consequences

### Positive
- Managed services reduce ops burden
- Native integration with Azure AD for auth
- Cost-effective at scale (pay-per-use)
- Enterprise-grade compliance (SOC, ISO, GDPR)

### Negative
- Vendor lock-in (mitigated by abstract interfaces)
- Additional Azure-specific configuration
- Requires Azure subscription for full testing

## Implementation

### Storage Abstraction
```python
# app/services/storage.py
class StorageBackend(ABC):
    @abstractmethod
    async def save_upload(self, file: BytesIO, filename: str, mime_type: str) -> tuple[str, int]:
        pass

class LocalStorage(StorageBackend): ...
class AzureBlobStorage(StorageBackend): ...
```

### Configuration
```yaml
# config.yaml
storage:
  provider: "local"  # or "azure_blob"
  azure:
    container: "documents"
    connection_string: "${AZURE_STORAGE_CONNECTION_STRING}"
```

### Telemetry
```python
# app/telemetry.py
setup_telemetry(
    enable_azure_monitor=bool(settings.azure.monitor_connection_string),
    azure_connection_string=settings.azure.monitor_connection_string,
)
```

## Alternatives Considered
- **AWS S3 + Secrets Manager + CloudWatch**: Multi-cloud but adds complexity
- **Self-hosted MinIO + Vault + Prometheus**: More control but higher ops burden
- **No cloud services**: Local-only limits production readiness

## Migration Path
The storage abstraction allows switching providers via config. For multi-cloud, add `S3Storage` implementing the same interface.