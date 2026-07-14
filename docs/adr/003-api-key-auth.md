# ADR 003: API Key Authentication with Bcrypt

## Context
The API needs secure authentication for programmatic access. Traditional JWT tokens add complexity for a service-to-service API.

## Decision
Use **API keys with bcrypt hashing**:

- **Format**: `di_<base64url>` (prefix + 32-char random)
- **Storage**: Bcrypt hash in PostgreSQL (`key_hash` column)
- **Verification**: `passlib` bcrypt verification on each request
- **Rate limiting**: Per-key configurable limits (default 10 req/min)
- **Expiration**: Optional TTL via `expires_at` column

## Consequences

### Positive
- Simple for clients (single header: `Authorization: Bearer di_...`)
- No token refresh logic needed
- Bcrypt is slow by design (resists brute force)
- Per-key rate limits prevent abuse
- Keys can be revoked instantly (`is_active = false`)

### Negative
- Bcrypt verification adds ~100ms latency per request
- No built-in scopes/permissions (all keys have same access)
- Key rotation requires client coordination

## Implementation

### Key Generation
```python
# app/routes/auth.py
prefix = "di_"
random_part = secrets.token_urlsafe(32)
plain_key = f"{prefix}{random_part}"
key_hash = pwd_context.hash(plain_key)
```

### Verification Middleware
```python
# app/middleware/auth.py
async def verify_api_key(request, authorization, db):
    parts = authorization.split()
    api_key = parts[1]
    
    if not api_key.startswith(settings.auth.api_key_prefix):
        raise AuthenticationError("Invalid API key format")
    
    # Fetch all active keys, verify hash
    keys = await db.execute(select(APIKey).where(APIKey.is_active == True))
    for key in keys.scalars().all():
        if pwd_context.verify(api_key, key.key_hash):
            return key
    raise AuthenticationError()
```

## Alternatives Considered
- **JWT tokens**: More complex, requires token refresh, better for user-facing apps
- **OAuth 2.0**: Overkill for service-to-service
- **Plain text keys**: Security risk if DB leaked

## Future Enhancements
- Add scopes/permissions column for fine-grained access
- Implement key rotation endpoint
- Add audit logging for key usage