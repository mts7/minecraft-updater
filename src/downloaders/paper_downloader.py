import json
import requests
import os
from tqdm import tqdm
import hashlib
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, List

from src.exceptions import VersionInfoError, BuildDataError

BASE_URL: str = "https://api.papermc.io/v2"
PROJECT: str = "paper"
CACHE_FILE: str = "paper_build_cache.json"
DEFAULT_DOWNLOAD_DIR: str = "paper_downloads"


class VersionFetchStrategy(ABC):
    @abstractmethod
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        pass


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


class PaperDownloader:
    def __init__(
            self,
            download_directory: str = DEFAULT_DOWNLOAD_DIR,
            version_strategy: VersionFetchStrategy = StableVersionStrategy()
    ) -> None:
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.version_strategy: VersionFetchStrategy = version_strategy

    @staticmethod
    def _load_cache_static() -> Dict[str, Any]:
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _save_cache_static(cache: Dict[str, Any]) -> None:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)

    def _get_build_data(self,
                        version: str,
                        build_number: int
                        ) -> Optional[Dict[str, Any]]:
        cache: Dict[str, Any] = self._load_cache_static()
        cache_key: str = f"{version}-{build_number}"
        if cache_key in cache:
            return cache[cache_key]

        url_build = (f"{BASE_URL}/projects/{PROJECT}/"
                     f"versions/{version}/builds/{build_number}")
        try:
            response_build: requests.Response = requests.get(url_build,
                                                             timeout=10)
            response_build.raise_for_status()
            build_data: Dict[str, Any] = response_build.json()
            cache[cache_key] = build_data
            self._save_cache_static(cache)
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

    def _check_existing_file(self, filepath: str, expected_hash: str) -> bool:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                file_hash: str = hashlib.sha256(f.read()).hexdigest()
            if file_hash == expected_hash:
                return True
            else:
                return False
        return False

    def download(self) -> Optional[str]:
        version, build = self.version_strategy.get_version_and_build()
        if not version or build is None:
            return None

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

        if self._check_existing_file(filepath, expected_hash):
            return filepath

        download_url = (f"{BASE_URL}/projects/{PROJECT}/versions/"
                        f"{version}/builds/{build}/downloads/{filename}")
        return self._download_file(download_url,
                                   filename,
                                   self.download_directory)

    def _download_file(self,
                       download_url: str,
                       filename: str,
                       download_directory: str = "."
                       ) -> Optional[str]:
        os.makedirs(download_directory, exist_ok=True)
        filepath: str = os.path.join(download_directory, filename)
        try:
            response: requests.Response = requests.get(download_url,
                                                       stream=True, timeout=10)
            response.raise_for_status()
            total_size: int = int(
                response.headers.get('content-length', 0))
            block_size: int = 1024
            progress_bar = tqdm(total=total_size, unit='iB',
                                unit_scale=True)
            with open(filepath, 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()
            return filepath
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return None
