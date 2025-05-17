import json
from typing import Optional, Dict, Any, List

import requests

from src.exceptions import VersionInfoError, BuildDataError

BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


def fetch_build_for_version(version: str, build_number: int) -> Dict[str, Any]:
    url_build = (f"{BASE_URL}/projects/{PROJECT}/"
                 f"versions/{version}/builds/{build_number}")
    try:
        response_build: requests.Response = requests.get(url_build,
                                                         timeout=10)
        response_build.raise_for_status()
        build_data: Dict[str, Any] = response_build.json()
        return build_data
    except requests.exceptions.RequestException as e:
        raise BuildDataError(f"Error fetching build data from {url_build}",
                             original_exception=e,
                             version=version,
                             build_number=build_number) from e
    except json.JSONDecodeError as e:
        raise BuildDataError(
            f"Error decoding build data JSON from {url_build}",
            original_exception=e,
            version=version,
            build_number=build_number) from e


def fetch_builds_for_version(version: str) \
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


def find_latest_stable_build(builds: List[Dict[str, Any]]) -> Optional[int]:
    for build_info in reversed(builds):
        if build_info.get('channel') == 'default':
            return build_info['build']
    return None


def fetch_paper_versions() -> List[str]:
    url_projects = f"{BASE_URL}/projects/{PROJECT}"
    try:
        response_projects: requests.Response = requests.get(
            url_projects, timeout=10)
        response_projects.raise_for_status()
        project_data: Dict[str, Any] = response_projects.json()
        versions = project_data.get('versions')
        if versions is None:
            raise VersionInfoError(
                f"API response for project versions from {url_projects} did"
                "not contain the 'versions' key.",
                url=url_projects
            )
        return versions
    except requests.exceptions.RequestException as e:
        raise VersionInfoError(
            f"Error fetching project versions from {url_projects}",
            original_exception=e, url=url_projects) from e
    except json.JSONDecodeError as e:
        raise VersionInfoError(
            f"Error decoding project versions JSON from {url_projects}",
            original_exception=e, url=url_projects) from e


def fetch_version_details(version: str) -> Dict[str, Any]:
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


def validate_build_data(build_data: Dict[str, Any]) -> None:
    if (not build_data
            or 'downloads' not in build_data
            or 'application' not in build_data.get('downloads', {})):
        raise BuildDataError(
            "Could not retrieve download information for Paper.")
