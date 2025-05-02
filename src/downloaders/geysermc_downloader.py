import requests
import os
from tqdm import tqdm
import json
import hashlib
import re
from typing import Optional, Dict, Any


class GeyserMcDownloader:
    API_BASE_URL_V2_LATEST: str = ""
    DOWNLOAD_BASE_URL_V2: str = (
        "https://download.geysermc.org/v2/projects/{project}"
        "/versions/{version}/builds/{build}/downloads/{download}"
    )
    PROJECT: str = ""
    DOWNLOAD_SUBPATH: str = ""
    DEFAULT_DOWNLOAD_DIR: str = ""
    FILENAME_PATTERN: Optional[str] = None  # Add a pattern attribute

    def __init__(self, download_directory: str) -> None:
        self.download_directory: str = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self._latest_info: Optional[Dict[str, Any]] = self._fetch_latest_info()

    def _fetch_latest_info(self) -> Optional[Dict[str, Any]]:
        api_url = self.API_BASE_URL_V2_LATEST
        if not api_url:
            print(f"API URL not defined for {self.__class__.__name__}.")
            return None
        try:
            print(f"Fetching latest info from {api_url}"
                  f"for {self.__class__.__name__}.")
            response: requests.Response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest info for {self.__class__.__name__} "
                  f"from {api_url}: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding API response from {api_url} "
                  f"for {self.__class__.__name__}.")
            return None

    def get_latest_version(self) -> Optional[str]:
        return self._latest_info.get("version") if self._latest_info else None

    def get_latest_build(self) -> Optional[int]:
        return self._latest_info.get("build") if self._latest_info else None

    def _get_expected_filename(
            self,
            version: str,
            build: int,
            filename_pattern: Optional[str] = None
    ) -> str:
        default_filename = f"{self.PROJECT}-latest.jar"
        pattern = filename_pattern if filename_pattern else default_filename
        if self._latest_info:
            base_name: str = (self._latest_info['downloads']
                              .get(self.DOWNLOAD_SUBPATH, {})
                              .get('name', f"{self.PROJECT}-latest.jar"))
            base, ext = os.path.splitext(base_name)
            # Construct the filename using base, version, build, and extension
            constructed_filename: str = f"{base}-v{version}-b{build}{ext}"

            if "*" not in pattern and "-SNAPSHOT" not in pattern:
                return constructed_filename
            else:
                match = re.match(
                    r"(.+?)(-SNAPSHOT)?(\.jar)?$",
                    base_name
                )
                if match:
                    prefix = match.group(1)
                    return f"{prefix}-v{version}-b{build}{ext}"
                return f"{self.PROJECT}-latest-v{version}-b{build}.jar"
        return default_filename

    def _check_existing_file(self,
                             filepath: str,
                             expected_hash: Optional[str]
                             ) -> bool:
        if os.path.exists(filepath):
            print(f"File '{os.path.basename(filepath)}' already exists. "
                  "Checking hash...")
            try:
                with open(filepath, 'rb') as f:
                    file_hash: str = hashlib.sha256(f.read()).hexdigest()
                if expected_hash and file_hash == expected_hash:
                    print("Hash matches. Skipping download.")
                    return True
                else:
                    print("Hash mismatch or no expected hash. "
                          "Downloading new file.")
                    return False
            except Exception as e:
                print(f"Error reading existing file: {e}")
                return False
        return False

    def _download_file(self,
                       download_url: str,
                       filename: str,
                       download_directory: str = "."
                       ) -> Optional[str]:
        os.makedirs(download_directory, exist_ok=True)
        filepath: str = os.path.join(download_directory, filename)
        temp_file: Optional[Any] = None
        try:
            print(f"Downloading {filename} from {download_url}...")
            response: requests.Response = requests.get(download_url,
                                                       stream=True)
            response.raise_for_status()
            total_size: int = int(response.headers.get(
                'content-length',
                0))
            block_size: int = 1024
            progress_bar = tqdm(total=total_size,
                                unit='iB',
                                unit_scale=True)
            temp_file = open(filepath, 'wb')
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                temp_file.write(data)
            progress_bar.close()
            if total_size != 0 and progress_bar.n != total_size:
                print("ERROR, something went wrong during download.")
                return None
            else:
                print(f"Successfully downloaded to {filepath}")
                return filepath
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during download: {e}")
            return None
        finally:
            if temp_file:
                temp_file.close()

    def _download_artifact(self,
                           project: str,
                           download_subpath: str,
                           filename_pattern: Optional[str] = None
                           ) -> Optional[str]:
        if self._latest_info is None:
            print(f"Could not retrieve latest information for {project}.")
            return None

        version = self._latest_info.get("version")
        build = self._latest_info.get("build")
        expected_hash = (self._latest_info['downloads']
                         .get(download_subpath, {}).get('sha256'))

        if not version or build is None or not expected_hash:
            print(f"Incomplete latest {project} information.")
            return None

        filename = self._get_expected_filename(version,
                                               build,
                                               filename_pattern)
        filepath = os.path.join(self.download_directory, filename)

        if self._check_existing_file(filepath, expected_hash):
            return filepath

        download_url = self.DOWNLOAD_BASE_URL_V2.format(
            project=project,
            version=version,
            build=build,
            download=download_subpath
        )
        print(f"Downloading {project} version {version} "
              f"build {build} as {filename}...")
        return self._download_file(download_url,
                                   filename,
                                   self.download_directory)

    def download_latest(self) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement download_latest")
