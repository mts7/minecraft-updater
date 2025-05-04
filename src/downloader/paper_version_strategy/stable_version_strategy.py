import json
from typing import Tuple, Optional, Dict, Any, List

import requests

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import VersionInfoError, BuildDataError


BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


class StableVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        url_projects = f"{BASE_URL}/projects/{PROJECT}"
        try:
            response_projects: requests.Response = requests.get(url_projects,
                                                                timeout=10)
            response_projects.raise_for_status()
            project_data: Dict[str, Any] = response_projects.json()
            versions: Optional[List[str]] = project_data.get('versions')

            if not versions:
                return None, None

            for version in reversed(versions):
                url_version = (
                    f"{BASE_URL}/projects/{PROJECT}/versions/{version}"
                )
                try:
                    response_version: requests.Response = requests.get(
                        url_version, timeout=10)
                    response_version.raise_for_status()
                    version_data: Dict[str, Any] = response_version.json()
                    builds: Optional[List[int]] = version_data.get('builds')

                    if not builds:
                        continue

                    latest_build_number: int = builds[-1]
                    url_build = (
                        f"{BASE_URL}/projects/{PROJECT}/"
                        f"versions/{version}/builds/{latest_build_number}"
                    )
                    try:
                        response_build: requests.Response = requests.get(
                            url_build, timeout=10)
                        response_build.raise_for_status()
                        build_data: Optional[
                            Dict[str, Any]] = response_build.json()
                        if build_data and build_data.get(
                                'channel') == 'default':
                            return version, latest_build_number
                    except requests.exceptions.RequestException as e:
                        raise VersionInfoError(
                            "Error fetching build info for "
                            f"version {version} from {url_build}",
                            original_exception=e, url=url_build) from e
                    except json.JSONDecodeError as e:
                        raise VersionInfoError(
                            "Error decoding build info JSON for "
                            f"version {version} from {url_build}",
                            original_exception=e, url=url_build) from e

                    for build_number in reversed(builds[:-1]):
                        build_data = self._get_build_data_static(version,
                                                                 build_number)
                        if build_data and build_data.get(
                                'channel') == 'default':
                            return version, build_number
                except requests.exceptions.RequestException as e:
                    raise VersionInfoError(
                        "Error fetching version details for "
                        f"{version} from {url_version}",
                        original_exception=e, url=url_version) from e
                except json.JSONDecodeError as e:
                    raise VersionInfoError(
                        "Error decoding version details JSON for "
                        f"{version} from {url_version}",
                        original_exception=e, url=url_version) from e
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching project versions from {url_projects}",
                original_exception=e, url=url_projects) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding project versions JSON from {url_projects}",
                original_exception=e, url=url_projects) from e

        return None, None

    @staticmethod
    def _get_build_data_static(version: str,
                               build_number: int
                               ) -> Optional[Dict[str, Any]]:
        cache: Dict[str, Any] = PaperDownloader._load_cache_static()
        cache_key: str = f"{version}-{build_number}"
        if cache_key in cache:
            return cache[cache_key]

        url_build = (
            f"{BASE_URL}/projects/{PROJECT}/"
            f"versions/{version}/builds/{build_number}"
        )
        try:
            response_build: requests.Response = requests.get(url_build,
                                                             timeout=10)
            response_build.raise_for_status()
            build_data: Dict[str, Any] = response_build.json()
            cache[cache_key] = build_data
            PaperDownloader._save_cache_static(cache)
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
