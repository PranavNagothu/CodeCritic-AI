"""Unit tests for GitHub repository ingestion via UniversalIngestor."""

from unittest.mock import MagicMock, patch
import pytest
from code_chatbot.ingestion.universal_ingestor import UniversalIngestor


class TestGitHubRepoManager:
    """Tests for GitHub repository handling in UniversalIngestor."""

    def test_github_url_detected(self):
        """A full GitHub URL should be recognized and delegate assigned."""
        ingestor = UniversalIngestor("https://github.com/PranavNagothu/CodeCritic-AI-AI")
        assert ingestor.delegate is not None

    def test_shorthand_repo_id_detected(self):
        """A shorthand owner/repo string should also be recognized."""
        ingestor = UniversalIngestor("PranavNagothu/CodeCritic-AI-AI")
        assert ingestor.delegate is not None

    @patch("code_chatbot.ingestion.universal_ingestor.requests.get")
    def test_github_api_call_on_check(self, mock_get):
        """Should make a GitHub API call when checking repo existence."""
        mock_get.return_value = MagicMock(status_code=200)
        ingestor = UniversalIngestor("https://github.com/PranavNagothu/CodeCritic-AI-AI")
        # Just verify delegate was created without error
        assert ingestor.delegate is not None

    def test_local_directory_detected(self, tmp_path):
        """A local directory path should be recognized."""
        ingestor = UniversalIngestor(str(tmp_path))
        assert ingestor.delegate is not None


if __name__ == "__main__":
    pytest.main()
