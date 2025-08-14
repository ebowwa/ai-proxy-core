#!/usr/bin/env python3
"""
Comprehensive tests for PDF, video, and document content type support in GoogleCompletions
"""
import os
import base64
import tempfile
import asyncio
import pytest
from typing import List, Dict, Any

from src.providers.google import GoogleCompletions


class TestContentTypeParsing:
    """Test the _parse_content method for new content types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sample_pdf_bytes = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
178
%%EOF"""
        
        self.sample_video_bytes = b"fake_video_data_for_testing_purposes"
        self.sample_doc_bytes = b"This is a test document content for testing."
        
        self.google_completions = GoogleCompletions.__new__(GoogleCompletions)
        self.google_completions.telemetry = None

    def test_pdf_base64_data_with_prefix(self):
        """Test PDF parsing with data: prefix"""
        pdf_b64 = base64.b64encode(self.sample_pdf_bytes).decode('utf-8')
        content = [
            {"type": "text", "text": "Analyze this PDF:"},
            {"type": "pdf", "pdf": {"data": f"data:application/pdf;base64,{pdf_b64}"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 2
        assert result[0] == "Analyze this PDF:"
        assert isinstance(result[1], dict)
        assert result[1]["mime_type"] == "application/pdf"
        assert result[1]["data"] == self.sample_pdf_bytes

    def test_pdf_base64_data_without_prefix(self):
        """Test PDF parsing with plain base64 data"""
        pdf_b64 = base64.b64encode(self.sample_pdf_bytes).decode('utf-8')
        content = [
            {"type": "pdf", "pdf": {"data": pdf_b64}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["mime_type"] == "application/pdf"
        assert result[0]["data"] == self.sample_pdf_bytes

    def test_pdf_file_path_existing(self):
        """Test PDF parsing from file path"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(self.sample_pdf_bytes)
            tmp_file.flush()
            
            content = [
                {"type": "pdf", "pdf": {"file_path": tmp_file.name}}
            ]
            
            result = self.google_completions._parse_content(content)
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["mime_type"] == "application/pdf"
            assert result[0]["data"] == self.sample_pdf_bytes
            
            os.unlink(tmp_file.name)

    def test_pdf_file_path_nonexistent(self):
        """Test PDF parsing with non-existent file path"""
        content = [
            {"type": "pdf", "pdf": {"file_path": "/nonexistent/file.pdf"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 0

    def test_video_base64_data_with_prefix(self):
        """Test video parsing with data: prefix"""
        video_b64 = base64.b64encode(self.sample_video_bytes).decode('utf-8')
        content = [
            {"type": "video", "video": {"data": f"data:video/mp4;base64,{video_b64}"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["mime_type"] == "video/mp4"
        assert result[0]["data"] == self.sample_video_bytes

    def test_video_base64_data_with_explicit_mime(self):
        """Test video parsing with explicit mime_type"""
        video_b64 = base64.b64encode(self.sample_video_bytes).decode('utf-8')
        content = [
            {"type": "video", "video": {"data": video_b64, "mime_type": "video/webm"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["mime_type"] == "video/webm"
        assert result[0]["data"] == self.sample_video_bytes

    def test_video_file_path_mime_detection(self):
        """Test video parsing from file path with MIME type detection"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_file.write(self.sample_video_bytes)
            tmp_file.flush()
            
            content = [
                {"type": "video", "video": {"file_path": tmp_file.name}}
            ]
            
            result = self.google_completions._parse_content(content)
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["mime_type"] == "video/mp4"
            assert result[0]["data"] == self.sample_video_bytes
            
            os.unlink(tmp_file.name)

    def test_video_file_path_unknown_extension_fallback(self):
        """Test video parsing with unknown extension falls back to video/mp4"""
        with tempfile.NamedTemporaryFile(suffix='.unknown', delete=False) as tmp_file:
            tmp_file.write(self.sample_video_bytes)
            tmp_file.flush()
            
            content = [
                {"type": "video", "video": {"file_path": tmp_file.name}}
            ]
            
            result = self.google_completions._parse_content(content)
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["mime_type"] == "video/mp4"
            assert result[0]["data"] == self.sample_video_bytes
            
            os.unlink(tmp_file.name)

    def test_document_base64_data_with_prefix(self):
        """Test document parsing with data: prefix"""
        doc_b64 = base64.b64encode(self.sample_doc_bytes).decode('utf-8')
        content = [
            {"type": "document", "document": {"data": f"data:text/plain;base64,{doc_b64}"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["mime_type"] == "text/plain"
        assert result[0]["data"] == self.sample_doc_bytes

    def test_document_base64_data_with_explicit_mime(self):
        """Test document parsing with explicit mime_type"""
        doc_b64 = base64.b64encode(self.sample_doc_bytes).decode('utf-8')
        content = [
            {"type": "document", "document": {"data": doc_b64, "mime_type": "application/rtf"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["mime_type"] == "application/rtf"
        assert result[0]["data"] == self.sample_doc_bytes

    def test_document_file_path_mime_detection(self):
        """Test document parsing from file path with MIME type detection"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_doc_bytes)
            tmp_file.flush()
            
            content = [
                {"type": "document", "document": {"file_path": tmp_file.name}}
            ]
            
            result = self.google_completions._parse_content(content)
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["mime_type"] == "text/plain"
            assert result[0]["data"] == self.sample_doc_bytes
            
            os.unlink(tmp_file.name)

    def test_document_file_path_unknown_extension_fallback(self):
        """Test document parsing with unknown extension falls back to text/plain"""
        with tempfile.NamedTemporaryFile(suffix='.unknown', delete=False) as tmp_file:
            tmp_file.write(self.sample_doc_bytes)
            tmp_file.flush()
            
            content = [
                {"type": "document", "document": {"file_path": tmp_file.name}}
            ]
            
            result = self.google_completions._parse_content(content)
            
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert result[0]["mime_type"] == "text/plain"
            assert result[0]["data"] == self.sample_doc_bytes
            
            os.unlink(tmp_file.name)

    def test_mixed_content_types(self):
        """Test parsing multiple content types in single request"""
        pdf_b64 = base64.b64encode(self.sample_pdf_bytes).decode('utf-8')
        video_b64 = base64.b64encode(self.sample_video_bytes).decode('utf-8')
        doc_b64 = base64.b64encode(self.sample_doc_bytes).decode('utf-8')
        
        content = [
            {"type": "text", "text": "Analyze these files:"},
            {"type": "pdf", "pdf": {"data": pdf_b64}},
            {"type": "video", "video": {"data": video_b64, "mime_type": "video/mp4"}},
            {"type": "document", "document": {"data": doc_b64, "mime_type": "text/plain"}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 4
        assert result[0] == "Analyze these files:"
        
        assert isinstance(result[1], dict)
        assert result[1]["mime_type"] == "application/pdf"
        assert result[1]["data"] == self.sample_pdf_bytes
        
        assert isinstance(result[2], dict)
        assert result[2]["mime_type"] == "video/mp4"
        assert result[2]["data"] == self.sample_video_bytes
        
        assert isinstance(result[3], dict)
        assert result[3]["mime_type"] == "text/plain"
        assert result[3]["data"] == self.sample_doc_bytes

    def test_string_content_input(self):
        """Test that string content is returned as-is"""
        content = "Simple text message"
        
        result = self.google_completions._parse_content(content)
        
        assert result == ["Simple text message"]

    def test_empty_content_array(self):
        """Test parsing empty content array"""
        content = []
        
        result = self.google_completions._parse_content(content)
        
        assert result == []

    def test_invalid_base64_data_handling(self):
        """Test that invalid base64 data is handled gracefully"""
        content = [
            {"type": "pdf", "pdf": {"data": "invalid_base64_data!!!"}}
        ]
        
        try:
            result = self.google_completions._parse_content(content)
            assert len(result) == 0
        except Exception:
            pass

    def test_missing_required_fields(self):
        """Test handling of content objects with missing required fields"""
        content = [
            {"type": "pdf", "pdf": {}},
            {"type": "video", "video": {}},
            {"type": "document", "document": {}}
        ]
        
        result = self.google_completions._parse_content(content)
        
        assert len(result) == 0


class TestGoogleCompletionsIntegration:
    """Test integration with GoogleCompletions class and API calls"""
    
    def test_api_key_environment_variable_handling(self):
        """Test that GoogleCompletions handles API key from environment"""
        original_key = os.environ.get("GEMINI_API_KEY")
        
        try:
            os.environ["GEMINI_API_KEY"] = "test_api_key_12345"
            
            google_completions = GoogleCompletions()
            assert google_completions.api_key == "test_api_key_12345"
            
        finally:
            if original_key:
                os.environ["GEMINI_API_KEY"] = original_key
            elif "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

    def test_api_key_missing_raises_error(self):
        """Test that missing API key raises appropriate error"""
        original_key = os.environ.get("GEMINI_API_KEY")
        original_google_key = os.environ.get("GOOGLE_API_KEY")
        
        try:
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            if "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]
            
            with pytest.raises(ValueError, match="GEMINI_API_KEY or GOOGLE_API_KEY not provided"):
                GoogleCompletions()
                
        finally:
            if original_key:
                os.environ["GEMINI_API_KEY"] = original_key
            if original_google_key:
                os.environ["GOOGLE_API_KEY"] = original_google_key

    @pytest.mark.asyncio
    async def test_content_types_with_real_api(self):
        """Test new content types with real Gemini API (requires GEMINI_API_KEY)"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set - skipping real API test")
        
        google_completions = GoogleCompletions(api_key=api_key)
        
        pdf_b64 = base64.b64encode(b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
>>
endobj
xref
0 1
0000000000 65535 f 
trailer
<<
/Size 1
/Root 1 0 R
>>
startxref
9
%%EOF""").decode('utf-8')
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What type of file is this?"},
                    {"type": "pdf", "pdf": {"data": pdf_b64}}
                ]
            }
        ]
        
        try:
            response = await google_completions.create_completion(
                messages=messages,
                model="gemini-1.5-flash",
                max_tokens=100
            )
            
            assert "choices" in response
            assert len(response["choices"]) > 0
            assert "message" in response["choices"][0]
            assert "content" in response["choices"][0]["message"]
            assert isinstance(response["choices"][0]["message"]["content"], str)
            assert len(response["choices"][0]["message"]["content"]) > 0
            
        except Exception as e:
            pytest.fail(f"Real API test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
