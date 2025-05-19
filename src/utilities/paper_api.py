from typing import Optional, Dict, Any, List

from src.exceptions import VersionInfoError, BuildDataError
from src.manager.cache_manager import CacheManager
from src.utilities.api_client import ApiClient, get_json


class PaperApiClient:
    BASE_URL = "https://api.papermc.io/v2"
    CACHE_FILE: str = "paper_build_cache.json"
    PROJECT = "paper"

    def __init__(self, base_url: Optional[str] = None,
                 project: Optional[str] = None,
                 cache_manager: Optional[CacheManager] = None,
                 api_client: Optional[ApiClient] = None):
        self.base_url = base_url if base_url is not None else self.BASE_URL
        self.project = project if project is not None else self.PROJECT
        self.cache = cache_manager if cache_manager is not None \
            else CacheManager(self.CACHE_FILE)
        self.api_client = api_client if api_client is not None \
            else ApiClient(self.cache)

    def build_url(self, endpoint: str = "") -> str:
        return f"{self.base_url}/projects/{self.project}/{endpoint}"

    def get_build_for_version(self, version: str, build_number: int) \
            -> Dict[str, Any]:
        cache_key = f"build_data_{version}_{build_number}"
        return self.api_client.get_cached_data(
            cache_key,
            lambda: self._fetch_build_for_version(version, build_number),
            expiry=None
        )

    def get_builds_for_version(self, version: str) \
            -> Optional[List[Dict[str, Any]]]:
        cache_key = f"builds_for_version_{version}"
        return self.api_client.get_cached_data(
            cache_key,
            lambda: self._fetch_builds_for_version(version),
            expiry=6 * 3600
        )

    def get_paper_versions(self) -> List[str]:
        cache_key = "paper_versions"
        return self.api_client.get_cached_data(
            cache_key,
            lambda: self._fetch_paper_versions(),
            expiry=7 * 24 * 3600
        )

    def get_version_details(self, version: str) -> Dict[str, Any]:
        cache_key = f"version_details_{version}"
        return self.api_client.get_cached_data(
            cache_key,
            lambda: self._fetch_version_details(version),
            expiry=6 * 3600
        )

    def _fetch_build_for_version(self, version: str, build_number: int) \
            -> Dict[str, Any]:
        url = self.build_url(f"versions/{version}/builds/{build_number}")
        return get_json(url)

    def _fetch_builds_for_version(self, version: str) \
            -> Optional[List[Dict[str, Any]]]:
        url = self.build_url(f"versions/{version}/builds")
        return get_json(url).get("builds")

    def _fetch_paper_versions(self) -> List[str]:
        url = self.build_url()
        versions = get_json(url).get("versions")
        if versions is None:
            raise VersionInfoError(
                f"API response for project versions from {url} "
                "did not contain the 'versions' key.",
                url=url)
        return versions

    def _fetch_version_details(self, version: str) -> Dict[str, Any]:
        url = self.build_url(f"versions/{version}")
        return get_json(url)


def find_latest_stable_build(builds: List[Dict[str, Any]]) -> Optional[int]:
    for build_info in reversed(builds):
        if build_info.get('channel') == 'default':
            return build_info['build']
    return None


def validate_build_data(build_data: Dict[str, Any]) -> None:
    if (not build_data
            or 'downloads' not in build_data
            or 'application' not in build_data.get('downloads', {})):
        raise BuildDataError(
            "Could not retrieve download information for Paper.")
