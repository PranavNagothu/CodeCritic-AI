"""Unit tests for the Indexer and vector store integration."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


class TestIndexer:

    def test_indexer_initializes_with_local_embeddings(self):
        """Indexer should initialize with local HuggingFace embeddings without API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("code_chatbot.ingestion.indexer.get_config") as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.chunking.max_chunk_tokens = 800
                mock_cfg.indexing.ignore_patterns = []
                mock_cfg.privacy.enable_path_obfuscation = False
                mock_config.return_value = mock_cfg

                from code_chatbot.ingestion.indexer import Indexer
                indexer = Indexer(
                    persist_directory=tmpdir,
                    provider="local"
                )
                assert indexer is not None
                assert indexer.persist_directory == tmpdir

    def test_indexer_requires_api_key_for_gemini(self):
        """Indexer should raise an error when Gemini provider has no API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("code_chatbot.ingestion.indexer.get_config") as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.chunking.max_chunk_tokens = 800
                mock_cfg.indexing.ignore_patterns = []
                mock_cfg.privacy.enable_path_obfuscation = False
                mock_config.return_value = mock_cfg

                with patch.dict(os.environ, {}, clear=True):
                    from code_chatbot.ingestion.indexer import Indexer
                    with pytest.raises(ValueError, match="Google API Key"):
                        Indexer(persist_directory=tmpdir, provider="gemini")


if __name__ == "__main__":
    pytest.main()
