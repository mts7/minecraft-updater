import os
import requests
from typing import Optional, Any
from tqdm import tqdm

from src.exceptions import (
    DownloadError,
    DownloadIncompleteError,
    DownloadOSError,
    DownloadRequestError,
)


def download_file(download_url: str,
                  filepath: str,
                  download_directory: str = ".",
                  description: Optional[str] = None) -> Optional[str]:
    os.makedirs(download_directory, exist_ok=True)
    temp_file: Optional[Any] = None
    try:
        response = get_http_stream(download_url, filepath)
        progress_bar = show_download_progress(response, filepath, description)
        total_size: int = int(response.headers.get('content-length', 0))
        block_size: int = 1024
        temp_file = open(filepath, 'wb')
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            temp_file.write(data)
        progress_bar.close()
        if total_size != 0 and progress_bar.n != total_size:
            raise DownloadIncompleteError(
                f"Download from {download_url} to {filepath} was incomplete",
                url=download_url, filepath=filepath)
        return filepath
    except OSError as e:
        raise DownloadOSError(
            f"OS error during download to {filepath}: {e}",
            original_exception=e, url=download_url, filepath=filepath) from e
    except DownloadIncompleteError:
        raise
    except Exception as e:
        raise DownloadError(
            "An unexpected error occurred during download "
            f"from {download_url} to {filepath}: {e}",
            original_exception=e, url=download_url, filepath=filepath) from e
    finally:
        if temp_file:
            temp_file.close()


def get_http_stream(download_url: str, filepath: str) -> requests.Response:
    try:
        response: requests.Response = requests.get(download_url,
                                                   stream=True, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise DownloadRequestError(
            f"Request error during download from {download_url}"
            f"to {filepath}: {e}",
            original_exception=e, url=download_url, filepath=filepath) from e


def show_download_progress(response: requests.Response, filepath: str,
                           description: Optional[str] = None) -> tqdm:
    total_size: int = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(
        total=total_size,
        unit='iB',
        unit_scale=True,
        desc=description if description else f"Download to {filepath}")
    return progress_bar
