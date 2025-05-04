import json
from typing import Tuple, Optional, Any, Dict

import requests

from src.exceptions import VersionInfoError
from src.downloader.paper_version_strategies.version_fetch_strategy import \
    VersionFetchStrategy


BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"


class LatestVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        url = f"{BASE_URL}/projects/{PROJECT}"
        try:
            response: requests.Response = requests.get(url, timeout=10)
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
            latest_version: Optional[str] = None
            versions = data.get('versions')
            if isinstance(versions, list) and versions:
                latest_version = versions[-1]
            if latest_version:
                url_version = (
                    f"{BASE_URL}/projects/{PROJECT}/versions/{latest_version}"
                )
                response_version: requests.Response = requests.get(url_version,
                                                                   timeout=10)
                response_version.raise_for_status()
                version_data: Dict[str, Any] = response_version.json()
                latest_build: Optional[int] = None
                builds = version_data.get('builds')
                if isinstance(builds, list) and builds:
                    latest_build_info = builds[-1]
                    if isinstance(latest_build_info, dict):
                        latest_build = latest_build_info.get('build')

                return latest_version, latest_build

            return None, None
        except requests.exceptions.RequestException as e:
            raise VersionInfoError(
                f"Error fetching version info from {url}",
                original_exception=e, url=url) from e
        except json.JSONDecodeError as e:
            raise VersionInfoError(
                f"Error decoding JSON response from {url}",
                original_exception=e, url=url) from e
