import pytest
from unittest.mock import Mock

from src.downloader.paper_version_strategy.specific_version_strategy import (
    SpecificVersionStrategy,
)
from src.utilities.paper_api import PaperApiClient


class TestSpecificVersionStrategy:
    def test_initialization_success(self):
        """
        Tests the successful initialization of SpecificVersionStrategy
        with a valid specific version.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        specific_version = "1.20.4"
        strategy = SpecificVersionStrategy(mock_api_client, specific_version)
        assert strategy._paper_api_client is mock_api_client
        assert strategy.specific_version == specific_version

    def test_initialization_raises_error_with_none_version(self):
        """
        Tests that initialization raises ValueError when specific_version is
        None.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        with pytest.raises(ValueError) as excinfo:
            SpecificVersionStrategy(mock_api_client, None)
        assert ("Specific version must be a non-empty string." in
                str(excinfo.value))

    def test_initialization_raises_error_with_empty_version(self):
        """
        Tests that initialization raises ValueError when specific_version is an
        empty string.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        with pytest.raises(ValueError) as excinfo:
            SpecificVersionStrategy(mock_api_client, "")
        assert ("Specific version must be a non-empty string." in
                str(excinfo.value))

    def test_initialization_raises_error_with_non_string_version(self):
        """
        Tests that initialization raises ValueError when specific_version is
        not a string.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        with pytest.raises(ValueError) as excinfo:
            SpecificVersionStrategy(mock_api_client, 123)
        assert ("Specific version must be a non-empty string." in
                str(excinfo.value))

    def test_get_version_and_build_returns_specific_version_and_none_build(
            self):
        """
        Tests that get_version_and_build returns the specific version
        and None for the build.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        specific_version = "1.19.5"
        strategy = SpecificVersionStrategy(mock_api_client, specific_version)
        version, build = strategy.get_version_and_build()
        assert version == specific_version
        assert build is None
        mock_api_client.get_paper_versions.assert_not_called()
        mock_api_client.get_version_details.assert_not_called()
