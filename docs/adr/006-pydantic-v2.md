# ADR 006: Pydantic v2 for Validation and Serialization

## Context
Data validation and serialization are critical for API correctness and documentation. Pydantic v1 was the standard but v2 brings significant improvements.

## Decision
Use **Pydantic v2** exclusively for:
- Request/response validation
- Settings management (`pydantic-settings`)
- OpenAPI schema generation
- Type-safe configuration

## Key v2 Features Used

### Strict Mode
```python
# pyproject.toml
[tool.mypy]
strict = true
```

```python
# app/schemas/document.py
class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(
        strict=True,  # Reject "123" for int field
        extra="forbid",  # Reject unknown fields
    )
    id: UUID
    filename: str
    status: DocumentStatus
    message: str
```

### Validation Decorators
```python
# app/security/validation.py
@field_validator("filename")
@classmethod
def validate_filename(cls, v: str) -> str:
    if len(v) > 255:
        raise ValueError("Filename too long")
    # Path traversal check
    if ".." in v or v.startswith("/"):
        raise ValueError("Invalid filename")
    return v
```

### Settings Management
```python
# app/config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    env: str = Field(default="development", alias="APP_ENV")
    database: DatabaseSettings = DatabaseSettings()
    anthropic: AnthropicSettings = AnthropicSettings()
```

### OpenAPI Examples
```python
class DocumentUploadResponse(BaseModel):
    id: UUID = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Human-readable message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "report.pdf",
                "status": "uploaded",
                "message": "File uploaded successfully. Use /process/analyze to analyze."
            }
        }
    )
```

## Consequences

### Positive
- **Runtime validation**: Catches bad data at boundaries
- **Documentation**: Auto-generates OpenAPI with examples
- **Type safety**: MyPy catches type errors at build time
- **Performance**: v2 is 5-50x faster than v1

### Negative
- Migration from v1 required code changes
- Strict mode rejects coercions (intentional)
- Learning curve for new features (`field_validator`, `ConfigDict`)

## Alternatives Considered
- **marshmallow**: Mature but no OpenAPI integration
- **attrs + cattrs**: Good for DTOs, no validation built-in
- **Manual validation**: Error-prone, no documentation

## Version Pin
```toml
# pyproject.toml
pydantic==2.5.3
pydantic-settings==2.1.0
pydantic-extra-types==2.4.0
```