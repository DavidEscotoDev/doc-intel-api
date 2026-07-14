# ADR 004: Background Processing with FastAPI BackgroundTasks

## Context
Document processing (text extraction + LLM analysis) takes seconds to minutes. HTTP requests must return quickly (202 Accepted) while processing continues asynchronously.

## Decision
Use **FastAPI BackgroundTasks** for MVP, with migration path to **Azure Service Bus**.

### Current: BackgroundTasks
```python
# app/routes/process.py
@router.post("/analyze")
async def analyze_document(request, background_tasks: BackgroundTasks, ...):
    background_tasks.add_task(process_document_task, str(document_id))
    return DocumentStatusResponse(status=DocumentStatus.PROCESSING)
```

```python
# app/tasks/processor.py
async def process_document_task(document_id: str):
    async with db.session() as session:
        # 1. Fetch document
        # 2. Extract text
        # 3. Call LLM
        # 4. Save analysis
        # 5. Update status
```

### Future: Azure Service Bus
```python
# app/messaging/servicebus.py
async def queue_document_processing(document_id: str):
    sender = get_servicebus_sender()
    await sender.send_message(ServiceBusMessage(json.dumps({"document_id": document_id})))
```

```python
# Worker process (separate container)
async def process_messages():
    receiver = get_servicebus_receiver()
    async for msg in receiver:
        await process_document_task(json.loads(str(msg))["document_id"])
        await receiver.complete_message(msg)
```

## Consequences

### Positive (BackgroundTasks)
- Zero infrastructure for MVP
- Simple, built into FastAPI
- Works in single-process development

### Negative (BackgroundTasks)
- **Not durable**: Lost on process crash/restart
- **No retry**: Failed tasks vanish silently
- **No scaling**: Tied to API process
- **No visibility**: No queue metrics

### Positive (Service Bus)
- **Durable**: Messages persist until processed
- **Retry + DLQ**: Automatic retry with dead-letter queue
- **Scalable**: Multiple workers, independent of API
- **Observable**: Queue depth, latency metrics

## Migration Strategy
1. Add `app/messaging/` abstraction layer
2. Implement `InMemoryMessageBus` (BackgroundTasks) for dev
3. Implement `ServiceBusMessageBus` for production
4. Switch via config: `MESSAGE_BUS=servicebus`

## Alternatives Considered
- **Celery + Redis**: Mature but adds Redis dependency
- **RQ + Redis**: Simpler than Celery but still Redis
- **Custom thread pool**: Reinvents queue poorly

## Decision
Start with BackgroundTasks for velocity. Migrate to Service Bus when:
- Production traffic > 100 req/day
- Need for retry/durability
- Horizontal scaling required