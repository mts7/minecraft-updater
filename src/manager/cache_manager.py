import json
import time
from typing import Dict, Any, Optional, Tuple


class CacheManager:
    DEFAULT_EXPIRY = 3600

    def __init__(self, cache_file: str):
        self.cache_file = cache_file

    def delete(self, key: str) -> None:
        cache = self.load_cache()
        if key in cache:
            del cache[key]
            self.save_cache(cache)

    def get(self, key: str) -> Optional[Any]:
        cached_data = self.load_cache().get(key)
        if not cached_data:
            return None
        timestamp, value = cached_data
        if timestamp is None or time.time() < timestamp:
            return value
        self.delete(key)
        return None

    def load_cache(self) -> Dict[str, Tuple[Optional[float], Any]]:
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_cache(self, cache: Dict[str, Tuple[Optional[float], Any]])\
            -> None:
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=4)

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        cache = self.load_cache()
        expiry_time = None
        if expiry is not None:
            expiry_time = time.time() + expiry
        cache[key] = (expiry_time, value)
        self.save_cache(cache)
