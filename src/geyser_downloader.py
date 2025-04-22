# src/geyser_downloader.py
import requests
import os
from tqdm import tqdm
import json
import hashlib

class GeyserDownloader:
    GEYSER_API_BASE_URL_V2 = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest"
    GEYSER_DOWNLOAD_BASE_URL_V2 = "https://download.geysermc.org/v2/projects/geyser/versions/{version}/builds/{build}/downloads/{download}"
    GEYSER_PROJECT = "geyser"
    GEYSER_DOWNLOAD_SUBPATH = "spigot"
    DEFAULT_DOWNLOAD_DIR = "downloads"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        self.download_directory = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self._latest_info = None

    def _fetch_latest_info(self):
        if self._latest_info:
            return self._latest_info

        try:
            response = requests.get(self.GEYSER_API_BASE_URL_V2)
            response.raise_for_status()
            self._latest_info = response.json()
            return self._latest_info
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest Geyser info from API: {e}")
            return None
        except json.JSONDecodeError:
            print("Error decoding Geyser API response.")
            return None

    def get_latest_version(self):
        info = self._fetch_latest_info()
        return info.get("version") if info else None

    def get_latest_build(self):
        info = self._fetch_latest_info()
        return info.get("build") if info else None

    def _get_expected_filename(self, version, build):
        info = self._fetch_latest_info()
        if info:
            base_name = info['downloads'].get(self.GEYSER_DOWNLOAD_SUBPATH, {}).get('name', 'Geyser-Spigot.jar')
            base, ext = os.path.splitext(base_name)
            return f"{base}-v{version}-b{build}{ext}"
        return f"Geyser-Spigot-latest.jar"

    def _check_existing_file(self, filepath, expected_hash):
        if os.path.exists(filepath):
            print(f"File '{os.path.basename(filepath)}' already exists. Checking hash...")
            try:
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                if file_hash == expected_hash:
                    print("Hash matches. Skipping download.")
                    return True
                else:
                    print("Hash mismatch. Downloading new file.")
                    return False
            except Exception as e:
                print(f"Error reading existing file: {e}")
                return False
        return False

    def download_latest(self):
        latest_info = self._fetch_latest_info()

        if not latest_info:
            print("Could not retrieve latest Geyser information. Skipping download.")
            return None

        version = latest_info.get("version")
        build = latest_info.get("build")
        download_name = self.GEYSER_DOWNLOAD_SUBPATH
        expected_hash = latest_info['downloads'].get(self.GEYSER_DOWNLOAD_SUBPATH, {}).get('sha256')

        if not version or not build or not download_name or not expected_hash:
            print("Incomplete latest Geyser information. Skipping download.")
            return None

        filename = self._get_expected_filename(version, build)
        filepath = os.path.join(self.download_directory, filename)

        if self._check_existing_file(filepath, expected_hash):
            return filepath

        download_url = self.GEYSER_DOWNLOAD_BASE_URL_V2.format(
            project=self.GEYSER_PROJECT,
            version=version,
            build=build,
            download=download_name
        )

        print(f"Downloading Geyser version {version} build {build} as {filename}...")
        return self._download_file(download_url, filename, self.download_directory)

    def _download_file(self, download_url, filename, download_directory="."):
        os.makedirs(download_directory, exist_ok=True)
        filepath = os.path.join(download_directory, filename)
        temp_file = None
        try:
            print(f"Downloading {filename} from {download_url}...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            temp_file = open(filepath, 'wb')
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                temp_file.write(data)
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
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

if __name__ == "__main__":
    downloader = GeyserDownloader()
    print("--- Checking and Downloading Latest Geyser ---")
    downloader.download_latest()
    print("--- Geyser check complete. ---")
