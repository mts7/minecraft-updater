from typing import Tuple, Optional, Any, Dict, List

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import NoPaperVersionsFoundError, InvalidVersionDataError


class LatestVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[str, Optional[int]]:
        versions: List[str] = self._paper_api_client.fetch_paper_versions()
        if not versions:
            raise NoPaperVersionsFoundError(
                "Could not fetch any Paper versions from the API.")

        version: str = versions[-1]
        if not version:
            raise NoPaperVersionsFoundError(
                "The list of Paper versions was empty.")

        version_data: Dict[str, Any] = (
            self._paper_api_client.fetch_version_details(version))
        if not version_data:
            raise InvalidVersionDataError(
                f"Could not fetch details for Paper version {version}.")

        builds: Optional[List[Dict[str, Any]]] = version_data.get('builds')
        if not isinstance(builds, list) or not builds:
            return version, None

        build_info: Optional[Dict[str, Any]] = builds[-1]
        if not isinstance(build_info, dict) or 'build' not in build_info:
            return version, None

        build: Optional[int] = build_info.get('build')
        return version, build
