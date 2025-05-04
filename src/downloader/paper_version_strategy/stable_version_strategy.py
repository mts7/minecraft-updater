import json
from typing import Tuple, Optional, Dict, Any, List

import requests

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import VersionInfoError


BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


class StableVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        versions = self._fetch_paper_versions()
        if not versions:
            return None, None

        for version in reversed(versions):
            version_data = self._fetch_version_details(version)
            if version_data:
                builds = self._fetch_builds_for_version(version)
                if builds:
                    stable_build = self._find_latest_stable_build(
                        version, builds)
                    if stable_build:
                        return stable_build
        return None, None

    def _fetch_paper_versions(self) -> Optional[List[str]]:
        url_projects = f"{BASE_URL}/projects/{PROJECT}"
        try:
            response_projects: requests.Response = requests.get(
                url_projects, timeout=10)
            response_projects.raise_for_status()
            project_data: Dict[str, Any] = response_projects.json()
            return project_data.get('versions')
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching project versions from {url_projects}",
                original_exception=e, url=url_projects) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding project versions JSON from {url_projects}",
                original_exception=e, url=url_projects) from e

    def _fetch_version_details(self, version: str) -> Optional[Dict[str, Any]]:
        url_version = f"{BASE_URL}/projects/{PROJECT}/versions/{version}"
        try:
            response_version: requests.Response = requests.get(
                url_version, timeout=10)
            response_version.raise_for_status()
            return response_version.json()
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                "Error fetching version details for "
                f"version {version} from {url_version}",
                original_exception=e, url=url_version) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                "Error decoding version details JSON for "
                f"version {version} from {url_version}",
                original_exception=e, url=url_version) from e

    def _fetch_builds_for_version(self, version: str) \
            -> Optional[List[Dict[str, Any]]]:
        url_version = f"{BASE_URL}/projects/{PROJECT}/versions/{version}"
        builds_url = f"{url_version}/builds"
        try:
            response_builds: requests.Response = requests.get(
                builds_url, timeout=10)
            response_builds.raise_for_status()
            builds_data: Dict[str, Any] = response_builds.json()
            return builds_data.get('builds')
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                "Error fetching builds for "
                f"version {version} from {builds_url}",
                original_exception=e, url=builds_url) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                "Error decoding builds JSON for "
                f"version {version} from {builds_url}",
                original_exception=e, url=builds_url) from e

    def _find_latest_stable_build(self, version: str,
                                  builds: List[Dict[str, Any]]) \
            -> Optional[Tuple[str, int]]:
        for build_info in reversed(builds):
            if build_info.get('channel') == 'default':
                return version, build_info['build']
        return None
