"""Integration tests for security validation."""

from io import BytesIO

import pytest
from fastapi import status
from httpx import AsyncClient


class TestFileValidation:
    """Test file validation security functions."""

    @pytest.mark.asyncio()
    async def test_validate_pdf_magic_bytes(self, client: AsyncClient, auth_headers: dict):
        """Test PDF magic byte validation."""
        # Valid PDF magic bytes
        file_content = b"%PDF-1.4\n%Test content"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio()
    async def test_reject_pdf_with_wrong_magic_bytes(self, client: AsyncClient, auth_headers: dict):
        """Test rejection of file with .pdf extension but wrong magic bytes."""
        # Text file pretending to be PDF
        file_content = b"This is not a PDF file"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio()
    async def test_validate_docx_magic_bytes(self, client: AsyncClient, auth_headers: dict):
        """Test DOCX (ZIP-based) magic byte validation."""
        # DOCX is a ZIP file with specific structure
        file_content = b"PK\x03\x04" + b"\x00" * 50 + b"[Content_Types].xml"
        files = {
            "file": (
                "test.docx",
                BytesIO(file_content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio()
    async def test_reject_docx_with_wrong_magic_bytes(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test rejection of file with .docx extension but wrong magic bytes."""
        file_content = b"This is not a DOCX file"
        files = {
            "file": (
                "test.docx",
                BytesIO(file_content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio()
    async def test_validate_png_magic_bytes(self, client: AsyncClient, auth_headers: dict):
        """Test PNG magic byte validation."""
        file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        files = {"file": ("test.png", BytesIO(file_content), "image/png")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio()
    async def test_validate_jpeg_magic_bytes(self, client: AsyncClient, auth_headers: dict):
        """Test JPEG magic byte validation."""
        file_content = b"\xff\xd8\xff\xe0" + b"\x00" * 50
        files = {"file": ("test.jpg", BytesIO(file_content), "image/jpeg")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio()
    async def test_reject_executable_masquerading_as_pdf(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test rejection of executable file with .pdf extension."""
        # Windows PE executable magic bytes
        file_content = b"MZ\x90\x00" + b"\x00" * 100
        files = {"file": ("malware.pdf", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio()
    async def test_filename_sanitization(self, client: AsyncClient, auth_headers: dict):
        """Test that dangerous filenames are rejected."""
        dangerous_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\cmd.exe",
            "/etc/passwd",
            "con.pdf",
            "prn.pdf",
            "aux.pdf",
            "nul.pdf",
            "com1.pdf",
            "lpt1.pdf",
        ]

        for name in dangerous_names:
            file_content = b"%PDF-1.4\n%Test"
            files = {"file": (name, BytesIO(file_content), "application/pdf")}

            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )
            assert (
                response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            ), f"Failed for {name}"

    @pytest.mark.asyncio()
    async def test_filename_length_limit(self, client: AsyncClient, auth_headers: dict):
        """Test filename length limit."""
        long_name = "a" * 300 + ".pdf"
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": (long_name, BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio()
    async def test_empty_filename_rejected(self, client: AsyncClient, auth_headers: dict):
        """Test that empty filename is rejected."""
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
