import os
import re
from typing import Optional, Dict, Any

from src.manager.cache_manager import CacheManager
from src.manager.file_manager import FileManager
from src.utilities.api_client import ApiClient, get_json
from src.utilities.download_utils import download_file


class GeyserMcDownloader(ApiClient):
    API_BASE_URL_V2_LATEST: str = ""
    CACHE_FILE: str = "geyser_build_cache.json"
    DOWNLOAD_BASE_URL_V2: str = (
        "https://download.geysermc.org/v2/projects/{project}"
        "/versions/{version}/builds/{build}/downloads/{download}"
    )
    PROJECT: str = ""
    DOWNLOAD_SUBPATH: str = ""
    DEFAULT_DOWNLOAD_DIR: str = ""
    FILENAME_PATTERN: Optional[str] = None

    def __init__(self, download_directory: str,
                 cache_manager: Optional[CacheManager] = None) -> None:
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.cache = cache_manager if cache_manager is not None \
            else CacheManager(self.CACHE_FILE)
        super().__init__(self.cache)
        self._latest_info: Optional[Dict[str, Any]] = self.get_latest_info()

    def download_latest(self) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement download_latest")

    def get_latest_build(self) -> Optional[int]:
        return self._latest_info.get("build") if self._latest_info else None

    def get_latest_info(self) -> Optional[Dict[str, Any]]:
        cache_key = "geyser_build"
        return self._get_cached_data(
            cache_key,
            lambda: self._fetch_latest_info(),
            expiry=6 * 3600
        )

    def get_latest_version(self) -> Optional[str]:
        return self._latest_info.get("version") if self._latest_info else None

    def _build_download_url(self, project: str, version: str, build: str,
                            download_subpath: str) -> str:
        return self.DOWNLOAD_BASE_URL_V2.format(
            project=project,
            version=version,
            build=build,
            download=download_subpath
        )

    def _download_artifact(self,
                           project: str,
                           download_subpath: str,
                           filename_pattern: Optional[str] = None
                           ) -> Optional[str]:
        if self._latest_info is None:
            return None

        version = self._latest_info.get("version")
        build = self._latest_info.get("build")
        expected_hash = (self._latest_info['downloads']
                         .get(download_subpath, {}).get('sha256'))

        if not version or build is None or not expected_hash:
            return None

        filename = self._get_expected_filename(version,
                                               build,
                                               filename_pattern)
        filepath = os.path.join(self.download_directory, filename)

        if FileManager.check_existing_file(filepath, expected_hash):
            return filepath

        return download_file(
            self._build_download_url(project, version, build,
                                     download_subpath),
            filepath,
            self.download_directory,
            description=(f"Downloading {project} version {version}, "
                         f"build {build}"))

    def _fetch_latest_info(self) -> Optional[Dict[str, Any]]:
        api_url = self.API_BASE_URL_V2_LATEST
        if not api_url:
            return None

        return get_json(api_url)

    def _get_expected_filename(
            self,
            version: str,
            build: int,
            filename_pattern: Optional[str] = None
    ) -> str:
        default_filename = f"{self.PROJECT}-latest.jar"
        assert self._latest_info is not None
        base_name: str = (self._latest_info['downloads']
                          .get(self.DOWNLOAD_SUBPATH, {})
                          .get('name', default_filename))
        base, ext = os.path.splitext(base_name)
        constructed_filename: str = _construct_versioned_filename(base,
                                                                  version,
                                                                  build, ext)
        pattern = filename_pattern if filename_pattern else default_filename

        if "*" not in pattern and "-SNAPSHOT" not in pattern:
            return constructed_filename

        match = re.match(
            r"(.+?)(-SNAPSHOT)?(\.jar)?$",
            base_name
        )
        if match:
            prefix = match.group(1)
            return _construct_versioned_filename(prefix, version, build, ext)

        return f"{self.PROJECT}-latest-v{version}-b{build}.jar"


def _construct_versioned_filename(base: str, version: str, build: int,
                                  ext: str) -> str:
    return f"{base}-v{version}-b{build}{ext}"
