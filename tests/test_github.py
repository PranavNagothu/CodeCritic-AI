"""Unit tests for GitHub repo ingestion in code_chatbot/ingestion/universal_ingestor.py."""

from unittest.mock import MagicMock, patch
import pytest
from code_chatbot.ingestion.universal_ingestor import UniversalIngestor


class TestUniversalIngestor:

    def test_detects_github_url(self):
        """Should identify a GitHub URL correctly."""
        ingestor = UniversalIngestor("https://github.com/PranavNagothu/CodeCritic-AI-AI")
        assert ingestor.delegate is not None

    def test_detects_zip_source(self, tmp_path):
        """Should identify a zip file source."""
        zip_path = tmp_path / "test.zip"
        zip_path.write_bytes(b"PK\x03\x04")  # minimal zip header
        ingestor = UniversalIngestor(str(zip_path))
        assert ingestor.delegate is not None

    def test_rejects_invalid_source(self):
        """Should raise an error for an unrecognized source."""
        with pytest.raises(Exception):
            ingestor = UniversalIngestor("not_a_real_path_or_url_xyz123")
            ingestor.delegate  # trigger detection


if __name__ == "__main__":
    pytest.main()
