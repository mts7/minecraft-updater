from typing import Tuple, Optional, Any, Dict, List

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.utilities.paper_api import (fetch_paper_versions,
                                     fetch_version_details)

BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


class LatestVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        versions: Optional[List[str]] = fetch_paper_versions()
        if not versions:
            return None, None

        version: Optional[str] = versions[-1]
        if not version:
            return None, None

        version_data: Optional[Dict[str, Any]] = fetch_version_details(version)
        if not version_data:
            return None, None

        builds: Optional[List[Dict[str, Any]]] = version_data.get('builds')
        if not isinstance(builds, list) or not builds:
            return version, None

        build_info: Optional[Dict[str, Any]] = builds[-1]
        if not isinstance(build_info, dict):
            return version, None

        build: Optional[int] = build_info.get('build')

        return version, build
