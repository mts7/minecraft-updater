import pytest
from unittest.mock import Mock

from src.downloader.paper_version_strategy.stable_version_strategy import (
    StableVersionStrategy,
)
from src.exceptions import NoPaperVersionsFoundError, NoStableBuildFoundError
from src.utilities.paper_api import PaperApiClient


class TestStableVersionStrategy:
    def test_get_version_and_build_success(self, mocker):
        """
        Tests the successful retrieval of a stable version and build.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.20.4", "1.21.0"]
        mock_api_client.get_version_details.return_value = {"some": "data"}
        mock_api_client.get_builds_for_version.return_value = [
            {"build": 100, "changes": [{"commits": []}]},
            {"build": 101, "changes": [{"commits": ["Stable commit"]}]},
        ]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=101,
        )
        strategy = StableVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 101
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_called_with("1.21.0")
        mock_api_client.get_builds_for_version.assert_called_with("1.21.0")
        mock_find_stable.assert_called_once_with(
            [
                {"build": 100, "changes": [{"commits": []}]},
                {"build": 101, "changes": [{"commits": ["Stable commit"]}]}
            ]
        )

    def test_get_version_and_build_no_versions(self):
        """
        Tests the case where no Paper versions are found.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = []
        strategy = StableVersionStrategy(mock_api_client)
        with pytest.raises(NoPaperVersionsFoundError) as excinfo:
            strategy.get_version_and_build()
        assert ("Could not fetch any Paper versions from the API."
                in str(excinfo.value))
        mock_api_client.get_paper_versions.assert_called_once()
        mock_api_client.get_version_details.assert_not_called()
        mock_api_client.get_builds_for_version.assert_not_called()

    def test_get_version_and_build_no_version_details_for_some(self, mocker):
        """
        Tests the case where version details are not found for some versions,
        but the latest version eventually succeeds.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.20.4", "1.21.0"]
        mock_api_client.get_version_details.side_effect = [
            {"some": "data"}, {}]
        mock_api_client.get_builds_for_version.return_value = [
            {"build": 100, "changes": [{"commits": []}]},
            {"build": 101, "changes": [{"commits": ["Stable fix"]}]},
        ]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=101,
        )
        strategy = StableVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 101
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 1
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")
        mock_api_client.get_builds_for_version.assert_called_once_with(
            "1.21.0")
        mock_find_stable.assert_called_once_with(
            [
                {"build": 100, "changes": [{"commits": []}]},
                {"build": 101, "changes": [{"commits": ["Stable fix"]}]}
            ]
        )

    def test_get_version_and_build_no_builds_for_some_versions(self, mocker):
        """
        Tests the case where no builds are found for some versions,
        but the latest version eventually succeeds.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.20.4", "1.21.0"]
        mock_api_client.get_version_details.return_value = {"some": "data"}
        mock_api_client.get_builds_for_version.side_effect = [
            [{"build": 102, "changes": [{"commits": ["Stable update"]}]}],
            []
        ]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=102,
        )
        strategy = StableVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 102
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 1
        mock_api_client.get_version_details.assert_called_once_with("1.21.0")
        assert mock_api_client.get_builds_for_version.call_count == 1
        mock_api_client.get_builds_for_version.assert_called_once_with(
            "1.21.0")
        mock_find_stable.assert_called_once_with(
            [{"build": 102, "changes": [{"commits": ["Stable update"]}]}]
        )

    def test_get_version_and_build_no_stable_build_found(self, mocker):
        """
        Tests the case where no stable build is found for any version.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.20.4", "1.21.0"]
        mock_api_client.get_version_details.return_value = {"some": "data"}
        mock_api_client.get_builds_for_version.side_effect = [
            [{"build": 100, "changes": [{"commits": []}]}],
            [{"build": 101, "changes": [{"commits": []}]}],
        ]
        mock_find_stable = Mock(return_value=None)
        mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            new=mock_find_stable,
        )
        strategy = StableVersionStrategy(mock_api_client)
        with pytest.raises(NoStableBuildFoundError) as excinfo:
            strategy.get_version_and_build()
        assert ("Could not find a stable build for any of the available Paper "
                "versions.") in str(
            excinfo.value
        )
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 2
        assert mock_api_client.get_builds_for_version.call_count == 2
        assert mock_find_stable.call_count == 2
        mock_find_stable.assert_any_call(
            [{"build": 101, "changes": [{"commits": []}]}])
        mock_find_stable.assert_any_call(
            [{"build": 100, "changes": [{"commits": []}]}])

    def test_continue_on_no_version_data(self, mocker):
        """
        Tests that the loop continues to the next version when
        get_version_details returns no data.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.21.0", "1.20.4"]
        mock_api_client.get_version_details.side_effect = [
            {}, {"some": "data"}]
        mock_api_client.get_builds_for_version.return_value = [
            {"build": 100, "changes": [{"commits": ["Stable"]}]}
        ]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=100,
        )
        strategy = StableVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 100
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 2
        mock_api_client.get_builds_for_version.assert_called_once_with(
            "1.21.0")
        mock_find_stable.assert_called_once_with(
            [{"build": 100, "changes": [{"commits": ["Stable"]}]}])

    def test_continue_on_no_builds_found(self, mocker):
        """
        Tests that the loop continues to the next version when
        get_builds_for_version returns no builds.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.21.0", "1.20.4"]
        mock_api_client.get_version_details.return_value = {"some": "data"}
        mock_api_client.get_builds_for_version.side_effect = [
            [], [{"build": 101, "changes": [{"commits": ["Stable"]}]}]]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=101,
        )
        strategy = StableVersionStrategy(mock_api_client)
        version, build = strategy.get_version_and_build()
        assert version == "1.21.0"
        assert build == 101
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 2
        assert mock_api_client.get_builds_for_version.call_count == 2
        mock_api_client.get_builds_for_version.assert_any_call("1.21.0")
        mock_api_client.get_builds_for_version.assert_any_call("1.20.4")
        mock_find_stable.assert_called_once_with(
            [{"build": 101, "changes": [{"commits": ["Stable"]}]}])

    def test_no_stable_build_found_after_continues(self, mocker):
        """
        Tests that NoStableBuildFoundError is raised when the loop completes
        after encountering versions with no data or no builds.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        mock_api_client.get_paper_versions.return_value = ["1.21.0", "1.20.4"]
        mock_api_client.get_version_details.side_effect = [
            {}, {"some": "data"}]
        mock_api_client.get_builds_for_version.side_effect = [
            [{"build": 101, "changes": [{"commits": []}]}],
            [],
        ]
        mock_find_stable = mocker.patch(
            "src.downloader.paper_version_strategy.stable_version_strategy."
            "find_latest_stable_build",
            return_value=None,
        )
        strategy = StableVersionStrategy(mock_api_client)
        with pytest.raises(NoStableBuildFoundError) as excinfo:
            strategy.get_version_and_build()
        assert ("Could not find a stable build for any of the available Paper "
                "versions.") in str(
            excinfo.value
        )
        mock_api_client.get_paper_versions.assert_called_once()
        assert mock_api_client.get_version_details.call_count == 2
        assert mock_api_client.get_builds_for_version.call_count == 1
        mock_find_stable.assert_called_once_with(
            [{"build": 101, "changes": [{"commits": []}]}])
