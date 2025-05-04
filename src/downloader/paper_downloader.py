import json
import os
from typing import Optional, Dict, Any

import requests

from src.downloader.file_downloader import FileDownloader
from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import BuildDataError, DownloadError, NoBuildsFoundError
from src.manager.cache_manager import CacheManager
from src.manager.file_manager import FileManager

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
            raise ValueError("A version_strategy must be provided during instantiation.")
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self._cache_manager = CacheManager(CACHE_FILE)
        self.version_strategy: VersionFetchStrategy = version_strategy

    def _get_build_data(self, version: str, build_number: int) -> Optional[Dict[str, Any]]:
        cache_key: str = f"{version}-{build_number}"
        cached_data = self._cache_manager.get(cache_key)
        if cached_data:
            return cached_data

        url_build = (f"{BASE_URL}/projects/{PROJECT}/"
                     f"versions/{version}/builds/{build_number}")
        try:
            response_build: requests.Response = requests.get(url_build,
                                                             timeout=10)
            response_build.raise_for_status()
            build_data: Dict[str, Any] = response_build.json()
            self._cache_manager.set(cache_key, build_data)
            return build_data
        except requests.exceptions.RequestException as e:
            raise BuildDataError(f"Error fetching build data from {url_build}",
                                 original_exception=e,
                                 version=version,
                                 build_number=build_number) from e
        except json.JSONDecodeError as e:
            raise BuildDataError(f"Error decoding build data JSON from {url_build}",
                                 original_exception=e,
                                 version=version,
                                 build_number=build_number) from e

    def _get_builds_for_version_from_api(self, version: str) -> Dict[str, Any]:
        url_builds = f"{BASE_URL}/projects/{PROJECT}/versions/{version}/builds"
        try:
            response_builds: requests.Response = requests.get(url_builds, timeout=10)
            response_builds.raise_for_status()
            return response_builds.json()
        except requests.exceptions.RequestException as e:
            raise DownloadError(f"Error fetching builds list for version {version} from {url_builds}", original_exception=e, version=version) from e
        except json.JSONDecodeError as e:
            raise DownloadError(f"Error decoding builds list JSON for version {version} from {url_builds}", original_exception=e, version=version) from e

    def download_specific_version(self, version: str) -> Optional[str]:
        builds_data = self._get_builds_for_version_from_api(version)
        if not builds_data or 'builds' not in builds_data or not builds_data['builds']:
            raise NoBuildsFoundError(f"No builds found for Paper version {version}.")

        latest_build = builds_data['builds'][-1]['build']
        return self.download_build(version, latest_build)

    def download_build(self, version: str, build: int) -> Optional[str]:
        build_data: Optional[Dict[str, Any]] = self._get_build_data(version, build)
        if not build_data or not all(
                key in build_data.get('downloads', {}) for key in
                ['application']
        ):
            raise BuildDataError(f"Could not retrieve download information for Paper version {version}, build {build}.")

        filename: str = build_data['downloads']['application']['name']
        expected_hash: str = build_data['downloads']['application']['sha256']
        filepath: str = os.path.join(self.download_directory, filename)

        if FileManager.check_existing_file(filepath, expected_hash):
            return filepath

        download_url = (f"{BASE_URL}/projects/{PROJECT}/versions/"
                        f"{version}/builds/{build}/downloads/{filename}")
        try:
            return FileDownloader.download_file(
                download_url,
                filename,
                self.download_directory,
                description=f"Downloading Paper version {version}, build {build}"
            )
        except Exception as e:
            raise DownloadError(f"Error during download from {download_url}", original_exception=e, version=version, build=build, filename=filename) from e

    def download(self) -> Optional[str]:
        version_info = self.version_strategy.get_version_and_build()
        if not version_info:
            raise RuntimeError("Could not determine version and build using the provided strategy.")
        version, build = version_info

        if build is not None:
            return self.download_build(version, build)
        else:
            return self.download_specific_version(version)
