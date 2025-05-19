import os
from typing import Optional, Dict, Any, List

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import BuildDataError, NoBuildsFoundError
from src.utilities.api_client import download_build
from src.utilities.paper_api import PaperApiClient, validate_build_data

DEFAULT_DOWNLOAD_DIR: str = "paper_downloads"


class PaperDownloader:
    def __init__(
            self,
            version_strategy: VersionFetchStrategy,
            paper_api_client: PaperApiClient,
            download_directory: str = DEFAULT_DOWNLOAD_DIR,
    ) -> None:
        if version_strategy is None:
            raise ValueError(
                "A version_strategy must be provided during instantiation.")
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.paper_api_client = paper_api_client
        self.version_strategy: VersionFetchStrategy = version_strategy

    def download(self) -> Optional[str]:
        version, build = self.version_strategy.get_version_and_build()

        if build is not None:
            return self.download_artifact(version, build)

        return self.download_specific_version(version)

    def download_artifact(self, version: str, build: int) -> Optional[str]:
        build_data: Dict[str, Any] = (
            self.paper_api_client.get_build_for_version(version, build))
        validate_build_data(build_data)

        filename: str = build_data['downloads']['application']['name']
        expected_hash: str = build_data['downloads']['application']['sha256']
        filepath: str = os.path.join(self.download_directory, filename)
        download_url = self.paper_api_client.build_url(
            f"versions/{version}/builds/{build}/downloads/{filename}")

        return download_build(
            filepath,
            expected_hash,
            download_url,
            self.download_directory,
            f"Downloading Paper version {version}, build {build}"
        )

    def download_specific_version(self, version: Optional[str]) \
            -> Optional[str]:
        if version is None:
            raise BuildDataError("Version is required.")

        builds: Optional[List[Dict[str, Any]]] = (
            self.paper_api_client.get_builds_for_version(version))
        if not builds:
            raise NoBuildsFoundError(
                f"No builds found for Paper version {version}.")

        latest_build_info: Optional[Dict[str, Any]] = builds[-1]
        if not latest_build_info or 'build' not in latest_build_info:
            raise NoBuildsFoundError(
                "Could not determine latest build for "
                f"Paper version {version}.")

        latest_build: int = latest_build_info['build']
        return self.download_artifact(version, latest_build)
