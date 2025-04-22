import json
import requests
import os
from tqdm import tqdm
import hashlib
from abc import ABC, abstractmethod

BASE_URL = "https://api.papermc.io/v2"
PROJECT = "paper"
CACHE_FILE = "paper_build_cache.json"
DEFAULT_DOWNLOAD_DIR = "paper_downloads"

class VersionFetchStrategy(ABC):
    @abstractmethod
    def get_version_and_build(self):
        pass

class LatestVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self):
        url = f"{BASE_URL}/projects/{PROJECT}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            latest_version = data['versions'][-1] if data['versions'] else None
            if latest_version:
                url_version = f"{BASE_URL}/projects/{PROJECT}/versions/{latest_version}"
                response_version = requests.get(url_version)
                response_version.raise_for_status()
                version_data = response_version.json()
                latest_build = version_data['builds'][-1]['build'] if version_data['builds'] else None
                return latest_version, latest_build
            return None, None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest version info: {e}")
            return None, None

class StableVersionStrategy(VersionFetchStrategy):
    def get_version_and_build(self):
        url_projects = f"{BASE_URL}/projects/{PROJECT}"
        try:
            response_projects = requests.get(url_projects)
            response_projects.raise_for_status()
            project_data = response_projects.json()
            versions = project_data['versions']

            if not versions:
                return None, None

            # Start with the latest version
            for version in reversed(versions):
                url_version = f"{BASE_URL}/projects/{PROJECT}/versions/{version}"
                response_version = requests.get(url_version)
                response_version.raise_for_status()
                version_data = response_version.json()
                builds = version_data['builds']

                if not builds:
                    continue  # No builds for this version

                # Check the latest build of this version
                latest_build_number = builds[-1]
                url_build = f"{BASE_URL}/projects/{PROJECT}/versions/{version}/builds/{latest_build_number}"
                response_build = requests.get(url_build)
                response_build.raise_for_status()
                build_data = response_build.json()
                if build_data.get('channel') == 'default':
                    return version, latest_build_number

                # Consider checking other builds in reverse chronological order
                for build_number in reversed(builds[:-1]):
                    build_data = self._get_build_data_static(version, build_number)
                    if build_data and build_data.get('channel') == 'default':
                        return version, build_number

            return None, None  # No stable version and build found
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Paper project info: {e}")
            return None, None

    @staticmethod
    def _get_build_data_static(version, build_number):
        cache = PaperDownloader._load_cache_static()
        cache_key = f"{version}-{build_number}"
        if cache_key in cache:
            return cache[cache_key]

        url_build = f"{BASE_URL}/projects/{PROJECT}/versions/{version}/builds/{build_number}"
        try:
            response_build = requests.get(url_build)
            response_build.raise_for_status()
            build_data = response_build.json()
            cache[cache_key] = build_data
            PaperDownloader._save_cache_static(cache)
            return build_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching build info for {version} build {build_number}: {e}")
            return None

class PaperDownloader:
    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR, version_strategy=StableVersionStrategy()):
        self.download_directory = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.version_strategy = version_strategy

    @staticmethod
    def _load_cache_static():
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Error decoding cache file. Starting with an empty cache.")
            return {}

    @staticmethod
    def _save_cache_static(cache):
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)

    def _get_build_data(self, version, build_number):
        cache = self._load_cache_static()
        cache_key = f"{version}-{build_number}"
        if cache_key in cache:
            return cache[cache_key]

        url_build = f"{BASE_URL}/projects/{PROJECT}/versions/{version}/builds/{build_number}"
        try:
            response_build = requests.get(url_build)
            response_build.raise_for_status()
            build_data = response_build.json()
            cache[cache_key] = build_data
            self._save_cache_static(cache)
            return build_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching build info for {version} build {build_number}: {e}")
            return None

    def _check_existing_file(self, filepath, expected_hash):
        if os.path.exists(filepath):
            print(f"File '{os.path.basename(filepath)}' already exists. Checking hash...")
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash == expected_hash:
                print("Hash matches. Skipping download.")
                return True
            else:
                print("Hash mismatch. Downloading new file.")
                return False
        return False

    def download(self):
        version, build = self.version_strategy.get_version_and_build()
        if version:
            print(f"Downloading Paper version: {version}, build: {build}")
            build_data = self._get_build_data(version, build)
            if build_data and 'downloads' in build_data and 'application' in build_data['downloads']:
                filename = build_data['downloads']['application']['name']
                expected_hash = build_data['downloads']['application']['sha256']
                filepath = os.path.join(self.download_directory, filename)

                if not self._check_existing_file(filepath, expected_hash):
                    download_url = f"{BASE_URL}/projects/{PROJECT}/versions/{version}/builds/{build}/downloads/{filename}"
                    self._download_file(download_url, filename, self.download_directory)
            else:
                print("Could not retrieve Paper download information.")
        else:
            print("Could not determine the Paper version and build to download.")

    def _download_file(self, download_url, filename, download_directory="."):
        os.makedirs(download_directory, exist_ok=True)
        filepath = os.path.join(download_directory, filename)
        try:
            print(f"Downloading {filename} from {download_url}...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            with open(filepath, 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print("ERROR, something went wrong")
            print(f"Successfully downloaded to {filepath}")
            return filepath
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return None

if __name__ == "__main__":
    downloader_stable = PaperDownloader()
    print("\n--- Downloading Latest Stable Paper ---")
    downloader_stable.download()

    downloader_latest = PaperDownloader(version_strategy=LatestVersionStrategy())
    print("\n--- Downloading Latest Paper ---")
    downloader_latest.download()