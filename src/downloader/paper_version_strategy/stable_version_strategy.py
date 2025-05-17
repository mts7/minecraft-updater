from typing import Tuple

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import NoPaperVersionsFoundError, NoStableBuildFoundError
from src.utilities.paper_api import find_latest_stable_build


class StableVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[str, int]:
        versions = self._paper_api_client.fetch_paper_versions()
        if not versions:
            raise NoPaperVersionsFoundError(
                "Could not fetch any Paper versions from the API.")

        for version in reversed(versions):
            version_data = self._paper_api_client.fetch_version_details(
                version)
            if not version_data:
                continue

            builds = self._paper_api_client.fetch_builds_for_version(version)
            if not builds:
                continue

            stable_build_number = find_latest_stable_build(builds)
            if stable_build_number:
                return version, stable_build_number

        raise NoStableBuildFoundError(
            "Could not find a stable build for"
            "any of the available Paper versions.")
