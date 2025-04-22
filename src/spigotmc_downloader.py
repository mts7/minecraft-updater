import requests
import os
import hashlib
from bs4 import BeautifulSoup
from tqdm import tqdm

class SpigotMCPluginDownloader:
    SPIGOTMC_URL = ""  # To be defined in subclasses
    DEFAULT_DOWNLOAD_DIR = ""  # To be defined in subclasses
    FILENAME = ""  # To be defined in subclasses

    def __init__(self, download_directory, filename, spigotmc_url):
        self.download_directory = download_directory
        os.makedirs(download_directory, exist_ok=True)
        self.FILENAME = filename
        self.SPIGOTMC_URL = spigotmc_url

    def _fetch_download_url(self):
        try:
            response = requests.get(self.SPIGOTMC_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            download_link_element = soup.find('a', {'class': 'inner'})
            if download_link_element and 'href' in download_link_element.attrs:
                href = download_link_element['href']
                return f"https://www.spigotmc.org/{href}"
            else:
                print(f"Could not find the main download link on {self.SPIGOTMC_URL}.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {self.SPIGOTMC_URL}: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while fetching download URL from {self.SPIGOTMC_URL}: {e}")
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
                print(f"File '{os.path.basename(filepath)}' already exists. Skipping download.")
                return True
        return False

    def download_latest(self):
        download_url = self._fetch_download_url()

        if not download_url:
            print(f"Could not retrieve download URL for {self.FILENAME}. Skipping download.")
            return None

        filepath = os.path.join(self.download_directory, self.FILENAME)

        if self._check_existing_file(filepath):
            return filepath

        print(f"Downloading latest {self.FILENAME} from {download_url}...")
        return self._download_file(download_url, self.FILENAME, self.download_directory)

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
