import requests
import os
import hashlib
from bs4 import BeautifulSoup
from tqdm import tqdm

class ViaVersionDownloader:
    SPIGOTMC_URL = "https://www.spigotmc.org/resources/viaversion.19254/"
    DOWNLOAD_URL_FORMAT = "https://download.viaversion.com/ViaVersion/latest"
    DEFAULT_DOWNLOAD_DIR = "viaversion_downloads"
    FILENAME = "ViaVersion.jar"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        self.download_directory = download_directory
        os.makedirs(download_directory, exist_ok=True)

    def _fetch_latest_version_info(self):
        try:
            response = requests.get(self.SPIGOTMC_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            download_link_element = soup.find('a', {'class': 'inner'})
            if download_link_element and 'href' in download_link_element.attrs:
                href = download_link_element['href']
                version_param = None
                parts = href.split('?')
                if len(parts) > 1:
                    params = parts[1].split('&')
                    for param in params:
                        if param.startswith('version='):
                            version_param = param.split('=')[1]
                            break
                if version_param:
                    download_url = f"https://www.spigotmc.org/{href}"  # Use the SpigotMC download handler
                    # We don't get a direct version number here easily, so we'll mark it as 'latest-spigot'
                    return {"version": "latest-spigot", "download_url": download_url}
                else:
                    print("Could not find the 'version' parameter in the download link.")
                    return None
            else:
                print("Could not find the main download link on SpigotMC page.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching SpigotMC page: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while fetching version info: {e}")
            return None

    def _check_existing_file(self, filepath, expected_hash=None):
        if os.path.exists(filepath):
            if expected_hash:
                print(f"File '{os.path.basename(filepath)}' already exists. Checking hash (if available)...")
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
            else:
                print(f"File '{os.path.basename(filepath)}' already exists. Skipping hash check.")
                return True
        return False

    def download_latest(self):
        latest_info = self._fetch_latest_version_info()

        if not latest_info:
            print("Could not retrieve latest ViaVersion information. Skipping download.")
            return None

        filename = self.FILENAME
        filepath = os.path.join(self.download_directory, filename)

        # We don't have a direct way to get the hash of the 'latest' download
        # before downloading it. For robust checking, you might need to:
        # 1. Download the file.
        # 2. Calculate its hash.
        # 3. Potentially compare against a known good hash (if you can find one reliably).
        # For this simplified example, we'll just check if the file exists.

        if self._check_existing_file(filepath):
            return filepath

        download_url = latest_info["download_url"]
        print(f"Downloading latest ViaVersion from {download_url} as {filename}...")
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
    downloader = ViaVersionDownloader()
    print("--- Checking and Downloading Latest ViaVersion ---")
    downloader.download_latest()
    print("--- ViaVersion check complete. ---")
