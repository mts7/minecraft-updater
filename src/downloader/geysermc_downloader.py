import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from src.manager.cache_manager import CacheManager
from src.utilities.api_client import ApiClient, get_json, download_build


class GeyserMcDownloader(ABC):
    BASE_URL: str = "https://download.geysermc.org/v2/"

    def __init__(self, download_directory: str,
                 cache_manager: CacheManager,
                 project: str,
                 subpath: str,
                 download_path: str,
                 base_url: Optional[str] = None,
                 api_client: Optional[ApiClient] = None) -> None:
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.cache = cache_manager
        self.project = project
        self.subpath = subpath
        self.download_path: str = download_path
        self.base_url = base_url if base_url is not None else self.BASE_URL
        self.api_client = api_client if api_client is not None \
            else ApiClient(self.cache)
        self._latest_info: Optional[Dict[str, Any]] = self.get_latest_info()

    @abstractmethod
    def download_latest(self) -> Optional[str]:
        pass

    def get_latest_build(self) -> Optional[int]:
        return self._latest_info.get("build") if self._latest_info else None

    def get_latest_info(self) -> Optional[Dict[str, Any]]:
        cache_key = "geyser_build"
        return self.api_client.get_cached_data(
            cache_key,
            lambda: self._fetch_latest_info(),
            expiry=6 * 3600
        )

    def get_latest_version(self) -> Optional[str]:
        return self._latest_info.get("version") if self._latest_info else None

    def _build_download_url(self, version: str, build: str) -> str:
        return self.base_url + self.download_path.format(
            project=self.project,
            version=version,
            build=build,
            download=self.subpath
        )

    def _download_artifact(self, filename_pattern: Optional[str] = None
                           ) -> Optional[str]:
        if self._latest_info is None:
            return None

        version = self._latest_info.get("version")
        build = self._latest_info.get("build")
        expected_hash = (self._latest_info['downloads']
                         .get(self.subpath, {}).get('sha256'))

        if not version or build is None or not expected_hash:
            return None

        filename = self._get_expected_filename(version, build,
                                               filename_pattern)
        filepath = os.path.join(self.download_directory, filename)
        download_url = self._build_download_url(version, build)

        return download_build(
            filepath,
            expected_hash,
            download_url,
            self.download_directory,
            f"Downloading {self.project} version {version}, build {build}"
        )

    def _fetch_latest_info(self) -> Optional[Dict[str, Any]]:
        api_url = self.base_url + self.download_path
        if not api_url:
            return None

        return get_json(api_url)

    def _get_expected_filename(
            self,
            version: str,
            build: int,
            filename_pattern: Optional[str] = None
    ) -> str:
        default_filename = f"{self.project}-latest.jar"
        assert self._latest_info is not None
        base_name: str = (self._latest_info['downloads']
                          .get(self.subpath, {})
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

        return f"{self.project}-latest-v{version}-b{build}.jar"


def _construct_versioned_filename(base: str, version: str, build: int,
                                  ext: str) -> str:
    return f"{base}-v{version}-b{build}{ext}"
