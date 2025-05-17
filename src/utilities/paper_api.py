import json
from typing import Optional, Dict, Any, List

import requests

from src.exceptions import VersionInfoError, BuildDataError
from src.manager.cache_manager import CacheManager

CACHE_FILE: str = "paper_build_cache.json"


class PaperApiClient:
    def __init__(self, base_url: Optional[str] = None,
                 project: Optional[str] = None):
        self.base_url = base_url if base_url is not None \
            else "https://api.papermc.io/v2"
        self.project = project if project is not None else "paper"
        self.cache = CacheManager(CACHE_FILE)

    def build_url(self, endpoint: str = "") -> str:
        return f"{self.base_url}/projects/{self.project}/{endpoint}"

    def get_build_for_version(self, version: str, build_number: int)\
            -> Dict[str, Any]:
        cache_key = f"build_data_{version}_{build_number}"
        cached_data = self.cache.get(cache_key)

        if cached_data:
            return cached_data
        else:
            build_data = self._fetch_build_for_version(version, build_number)
            self.cache.set(cache_key, build_data, expiry=None)
            return build_data

    def get_builds_for_version(self, version: str)\
            -> Optional[List[Dict[str, Any]]]:
        cache_key = f"builds_for_version_{version}"
        cached_data = self.cache.get(cache_key)

        if cached_data:
            return cached_data
        else:
            builds_data = self._fetch_builds_for_version(version)
            if builds_data:
                self.cache.set(cache_key, builds_data, expiry=6 * 3600)
            return builds_data

    def get_paper_versions(self) -> List[str]:
        cache_key = "paper_versions"
        cached_data = self.cache.get(cache_key)

        if cached_data:
            return cached_data
        else:
            versions = self._fetch_paper_versions()
            self.cache.set(cache_key, versions, expiry=7 * 24 * 3600)
            return versions

    def get_version_details(self, version: str) -> Dict[str, Any]:
        cache_key = f"version_details_{version}"
        cached_data = self.cache.get(cache_key)

        if cached_data:
            return cached_data
        else:
            version_data = self._fetch_version_details(version)
            self.cache.set(cache_key, version_data, expiry=6 * 3600)
            return version_data

    def _fetch_build_for_version(self, version: str, build_number: int) \
            -> Dict[str, Any]:
        url_build = self.build_url(
            f"versions/{version}/builds/{build_number}")
        try:
            response_build: requests.Response = requests.get(url_build,
                                                             timeout=10)
            response_build.raise_for_status()
            build_data: Dict[str, Any] = response_build.json()
            return build_data
        except requests.exceptions.RequestException as e:
            raise BuildDataError(f"Error fetching build data from {url_build}",
                                 original_exception=e, version=version,
                                 build_number=build_number) from e
        except json.JSONDecodeError as e:
            raise BuildDataError(
                f"Error decoding build data JSON from {url_build}",
                original_exception=e, version=version,
                build_number=build_number) from e

    def _fetch_builds_for_version(self, version: str)\
            -> Optional[List[Dict[str, Any]]]:
        builds_url = self.build_url(f"versions/{version}/builds")
        try:
            response_builds: requests.Response = requests.get(builds_url,
                                                              timeout=10)
            response_builds.raise_for_status()
            builds_data: Dict[str, Any] = response_builds.json()
            return builds_data.get('builds')
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching builds for version {version} "
                f"from {builds_url}",
                original_exception=e, url=builds_url) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding builds JSON for version {version} "
                f"from {builds_url}",
                original_exception=e, url=builds_url) from e

    def _fetch_paper_versions(self) -> List[str]:
        url_projects = self.build_url()
        try:
            response_projects: requests.Response = requests.get(url_projects,
                                                                timeout=10)
            response_projects.raise_for_status()
            project_data: Dict[str, Any] = response_projects.json()
            versions = project_data.get('versions')
            if versions is None:
                raise VersionInfoError(
                    f"API response for project versions from {url_projects} "
                    "did not contain the 'versions' key.",
                    url=url_projects)
            return versions
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching project versions from {url_projects}",
                original_exception=e, url=url_projects) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding project versions JSON from {url_projects}",
                original_exception=e, url=url_projects) from e

    def _fetch_version_details(self, version: str) -> Dict[str, Any]:
        url_version = self.build_url(f"versions/{version}")
        try:
            response_version: requests.Response = requests.get(url_version,
                                                               timeout=10)
            response_version.raise_for_status()
            return response_version.json()
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching version details for version {version} "
                f"from {url_version}",
                original_exception=e, url=url_version) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding version details JSON for version {version} "
                f"from {url_version}",
                original_exception=e, url=url_version) from e


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
