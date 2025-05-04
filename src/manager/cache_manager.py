import json
from typing import Dict, Any, Optional

class CacheManager:
    def __init__(self, cache_file: str):
        self.cache_file = cache_file

    def load_cache(self) -> Dict[str, Any]:
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_cache(self, cache: Dict[str, Any]) -> None:
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=4)

    def get(self, key: str) -> Optional[Any]:
        cache = self.load_cache()
        return cache.get(key)

    def set(self, key: str, value: Any) -> None:
        cache = self.load_cache()
        cache[key] = value
        self.save_cache(cache)

    def delete(self, key: str) -> None:
        cache = self.load_cache()
        if key in cache:
            del cache[key]
            self.save_cache(cache)
