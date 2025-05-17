import os
from typing import Optional, Dict, Any, List

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import BuildDataError, NoBuildsFoundError
from src.manager.cache_manager import CacheManager
from src.manager.file_manager import FileManager
from src.utilities.download_utils import download_file
from src.utilities.paper_api import fetch_build_for_version, \
    fetch_builds_for_version, validate_build_data

BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"
CACHE_FILE: str = "paper_build_cache.json"
DEFAULT_DOWNLOAD_DIR: str = "paper_downloads"


class PaperDownloader:
    def __init__(
            self,
            version_strategy: VersionFetchStrategy,
            download_directory: str = DEFAULT_DOWNLOAD_DIR,
    ) -> None:
        if version_strategy is None:
            raise ValueError(
                "A version_strategy must be provided during instantiation.")
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self._cache_manager = CacheManager(CACHE_FILE)
        self.version_strategy: VersionFetchStrategy = version_strategy

    def download(self) -> Optional[str]:
        version_info = self.version_strategy.get_version_and_build()
        if not version_info or version_info == (None, None):
            raise RuntimeError(
                "Could not determine version and build "
                "using the provided strategy.")
        version, build = version_info

        if build is not None:
            return self.download_build(version, build)

        return self.download_specific_version(version)

    def download_build(self, version: Optional[str], build: int) \
            -> Optional[str]:
        if not version:
            raise BuildDataError("Version is required.")

        build_data: Dict[str, Any] = self._get_build_data(version, build)
        validate_build_data(build_data)

        filename: str = build_data['downloads']['application']['name']
        expected_hash: str = build_data['downloads']['application']['sha256']
        filepath: str = os.path.join(self.download_directory, filename)

        if FileManager.check_existing_file(filepath, expected_hash):
            return filepath

        download_url = (f"{BASE_URL}/projects/{PROJECT}/versions/"
                        f"{version}/builds/{build}/downloads/{filename}")
        return download_file(
            download_url,
            filepath,
            self.download_directory,
            description=f"Downloading Paper version {version}, "
                        f"build {build}"
        )

    def download_specific_version(self, version: Optional[str]) \
            -> Optional[str]:
        if version is None:
            raise BuildDataError("Version is required.")

        builds: Optional[List[Dict[str, Any]]] = (
            fetch_builds_for_version(version))
        if not builds:
            raise NoBuildsFoundError(
                f"No builds found for Paper version {version}.")

        latest_build_info: Optional[Dict[str, Any]] = builds[-1]
        if not latest_build_info or 'build' not in latest_build_info:
            raise NoBuildsFoundError(
                "Could not determine latest build for "
                f"Paper version {version}.")

        latest_build: int = latest_build_info['build']
        return self.download_build(version, latest_build)

    def _get_build_data(self, version: str, build_number: int) \
            -> Dict[str, Any]:
        cache_key: str = f"{version}-{build_number}"
        cached_data = self._cache_manager.get(cache_key)
        if cached_data:
            return cached_data

        build_data = fetch_build_for_version(version, build_number)
        self._cache_manager.set(cache_key, build_data)
        return build_data
