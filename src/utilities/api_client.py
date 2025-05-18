from typing import Dict, Any, Optional, Callable
import requests
import json

from src.exceptions import APIDataError, APIRequestError
from src.manager.cache_manager import CacheManager
from src.manager.file_manager import does_file_exist, does_file_hash_match
from src.utilities.download_utils import download_file


class ApiClient:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def _get_cached_data(self, cache_key: str, fetch_function: Callable,
                         expiry: Optional[int] = None):
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        else:
            fetched_data = fetch_function()
            if fetched_data:
                self.cache.set(cache_key, fetched_data, expiry=expiry)
            return fetched_data


def download_build(filepath: str, expected_hash: str, url: str,
                   directory: str, description: str) -> str:
    if (does_file_exist(filepath)
            and does_file_hash_match(filepath, expected_hash)):
        return filepath

    return download_file(url, filepath, directory, description)


def fetch_response(url: str) -> requests.Response:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise APIRequestError(f"Error during request to {url}",
                              original_exception=e, url=url) from e


def get_json(url: str) -> Dict[str, Any]:
    response: requests.Response = fetch_response(url)
    return parse_json(response)


def parse_json(response: requests.Response) -> Dict[str, Any]:
    try:
        if response.headers.get('Content-Type') != 'application/json':
            raise APIDataError(
                "Expected JSON but got "
                f"{response.headers.get('Content-Type')}")
        return response.json()
    except json.JSONDecodeError as e:
        raise APIDataError("Failed to decode JSON",
                           original_exception=e) from e
