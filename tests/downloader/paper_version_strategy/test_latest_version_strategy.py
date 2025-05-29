import pytest
from unittest.mock import Mock

from src.downloader.paper_version_strategy.latest_version_strategy import (
    LatestVersionStrategy,
)
from src.exceptions import (
    NoPaperVersionsFoundError,
    InvalidVersionDataError,
)


class TestLatestVersionStrategy:
    def test_get_version_and_build_success(self):
        """
        Tests the successful retrieval of the latest version and build.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = [
            "1.20.3",
            "1.20.4",
            "1.21.0"
        ]
        mock_api_client.get_version_details.return_value = {
            "builds": [
                {"build": 100},
                {"build": 101},
                {"build": 102},
            ]
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 102
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")

    def test_get_version_and_build_no_versions(self):
        """
        Tests the case where no Paper versions are found.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = []
        strategy = LatestVersionStrategy(mock_api_client)
        with pytest.raises(NoPaperVersionsFoundError) as excinfo:
            strategy.get_version_and_build()
        assert ("Could not fetch any Paper versions from the API." in
                str(excinfo.value))
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_not_called()

    def test_get_version_and_build_empty_versions_list(self):
        """
        Tests the case where the list of Paper versions is empty.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = [""]
        strategy = LatestVersionStrategy(mock_api_client)
        with pytest.raises(NoPaperVersionsFoundError) as excinfo:
            strategy.get_version_and_build()
        assert "The list of Paper versions was empty." in str(excinfo.value)
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_not_called()

    def test_get_version_and_build_no_version_details(self):
        """
        Tests the case where version details cannot be fetched.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = ["1.21.0"]
        mock_api_client.get_version_details.return_value = {}
        strategy = LatestVersionStrategy(mock_api_client)
        with pytest.raises(InvalidVersionDataError) as excinfo:
            strategy.get_version_and_build()
        assert "Could not fetch details for Paper version 1.21.0." in str(
            excinfo.value
        )
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")

    def test_get_version_and_build_no_builds_in_version_data(self):
        """
        Tests the case where 'builds' key is missing or not a list in version
        data.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = ["1.21.0"]
        mock_api_client.get_version_details.return_value = {
            "other_data": "some_value"
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")

        mock_api_client.get_version_details.return_value = {
            "builds": "not_a_list"
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        assert mock_api_client.get_paper_versions.call_count == 2
        assert mock_api_client.get_version_details.call_count == 2

    def test_get_version_and_build_empty_builds_list(self):
        """
        Tests the case where the 'builds' list is empty.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = ["1.21.0"]
        mock_api_client.get_version_details.return_value = {"builds": []}
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")

    def test_get_version_and_build_no_build_info(self):
        """
        Tests the case where the last build info is not a dict or missing
        'build' key.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = ["1.21.0"]
        mock_api_client.get_version_details.return_value = {
            "builds": ["not_a_dict"]
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")

        mock_api_client.get_version_details.return_value = {
            "builds": [{"other": 123}]
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        assert mock_api_client.get_paper_versions.call_count == 2
        assert mock_api_client.get_version_details.call_count == 2

    def test_get_version_and_build_build_key_present_but_none(self):
        """
        Tests the case where the 'build' key is present but its value is None.
        """
        mock_api_client = Mock()
        mock_api_client.get_paper_versions.return_value = ["1.21.0"]
        mock_api_client.get_version_details.return_value = {
            "builds": [{"build": None}]
        }
        strategy = LatestVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build is None
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")
