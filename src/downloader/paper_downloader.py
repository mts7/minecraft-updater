import json
import os
from typing import Optional, Dict, Any

import requests

from src.downloader.file_downloader import FileDownloader
from src.downloader.paper_version_strategies.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import BuildDataError
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
            raise BuildDataError("Error fetching build data",
                                 original_exception=e,
                                 url=url_build,
                                 version=version,
                                 build_number=build_number) from e
        except json.JSONDecodeError as e:
            raise BuildDataError("Error decoding build data JSON",
                                 original_exception=e,
                                 url=url_build,
                                 version=version,
                                 build_number=build_number) from e

    def download(self) -> Optional[str]:
        version_info = self.version_strategy.get_version_and_build()
        if not version_info:
            print("Could not determine version and build.")
            return None
        version, build = version_info

        build_data: Optional[Dict[str, Any]] = self._get_build_data(version,
                                                                    build)
        if not build_data or not all(
                key in build_data.get('downloads', {}) for key in
                ['application']
        ):
            return None

        filename: str = build_data['downloads']['application']['name']
        expected_hash: str = build_data['downloads']['application']['sha256']
        filepath: str = os.path.join(self.download_directory, filename)

        if FileManager.check_existing_file(filepath, expected_hash):
            return filepath

        download_url = (f"{BASE_URL}/projects/{PROJECT}/versions/"
                        f"{version}/builds/{build}/downloads/{filename}")
        return FileDownloader.download_file(
            download_url,
            filename,
            self.download_directory,
            description=f"Downloading Paper version {version}, build {build}"
        )
