"""Schema validation tests."""
import pytest
from pydantic import ValidationError
from uuid import uuid4
from app.schemas.document import DocumentUploadResponse, DocumentProcessRequest, DocumentListItem
from app.schemas.analysis import AnalysisResponse, AnalysisRequest
from app.schemas.auth import APIKeyCreate, APIKeyCreateResponse
from app.schemas.common import PaginatedResponse, ErrorResponse
from app.constants import DocumentStatus

class TestDocumentSchemas:
    def test_document_upload_response_valid(self):
        doc_id = uuid4()
        response = DocumentUploadResponse(id=doc_id, filename="test.pdf", status=DocumentStatus.UPLOADED, message="done")
        assert response.status == DocumentStatus.UPLOADED

    def test_document_process_request_invalid_callback(self):
        doc_id = uuid4()
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(document_id=doc_id, callback_url="not-a-url")
        assert "Callback URL must be a valid HTTP/HTTPS URL" in str(exc_info.value)

    def test_document_list_item(self):
        doc_id = uuid4()
        item = DocumentListItem(id=doc_id, filename="test.pdf", mime_type="application/pdf", file_size=1024,
            status=DocumentStatus.COMPLETED, created_at="2024-01-01T00:00:00Z")
        assert item.status == DocumentStatus.COMPLETED

class TestAnalysisSchemas:
    def test_analysis_response_valid(self):
        analysis_id = uuid4(); doc_id = uuid4()
        response = AnalysisResponse(id=analysis_id, document_id=doc_id, summary="Test",
            key_points=["P1", "P2"], entities=["E1"], sentiment="positive", topics=["T1"],
            tokens_used=150, model_version="claude-3-5-sonnet-20241022", processing_time_ms=1200,
            created_at="2024-01-01T00:00:00Z")
        assert response.sentiment == "positive"
        assert len(response.key_points) == 2

class TestAuthSchemas:
    def test_api_key_create_valid(self):
        create = APIKeyCreate(name="Test Key", rate_limit=50, expires_in_days=30)
        assert create.rate_limit == 50

    def test_api_key_create_rate_limit_bounds(self):
        with pytest.raises(ValidationError): APIKeyCreate(name="Test", rate_limit=0)
        with pytest.raises(ValidationError): APIKeyCreate(name="Test", rate_limit=1001)

class TestCommonSchemas:
    def test_paginated_response(self):
        response = PaginatedResponse(items=[], total=0, page=1, page_size=10, total_pages=0)
        assert response.has_next is False

    def test_error_response(self):
        from app.schemas.common import ErrorDetail
        error = ErrorResponse(error=ErrorDetail(code="TEST", message="Test"))
        assert error.error.code == "TEST"