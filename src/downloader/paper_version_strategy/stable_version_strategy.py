from typing import Tuple, Optional

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.utilities.paper_api import fetch_paper_versions, \
    fetch_version_details, fetch_builds_for_version, find_latest_stable_build


class StableVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        versions = fetch_paper_versions()
        if not versions:
            return None, None

        for version in reversed(versions):
            version_data = fetch_version_details(version)
            if not version_data:
                continue

            builds = fetch_builds_for_version(version)
            if not builds:
                continue

            stable_build_number = find_latest_stable_build(builds)
            if stable_build_number:
                return version, stable_build_number

        return None, None
