import json
from typing import Optional, Dict, Any, List

import requests

from src.exceptions import VersionInfoError

BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


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


def fetch_paper_versions() -> Optional[List[str]]:
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


def fetch_version_details(version: str) -> Optional[Dict[str, Any]]:
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
