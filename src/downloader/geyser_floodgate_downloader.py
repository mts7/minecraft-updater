from typing import Optional

from src.manager.cache_manager import CacheManager
from src.downloader.geysermc_downloader import GeyserMcDownloader
from src.utilities.api_client import ApiClient


class FloodgateDownloader(GeyserMcDownloader):
    CACHE_FILE: str = "geyser_floodgate_build_cache.json"
    DEFAULT_DOWNLOAD_DIR: str = "floodgate_downloads"
    DOWNLOAD_PATH: str = "projects/floodgate/versions/latest/builds/latest"
    DOWNLOAD_SUBPATH: str = "spigot"
    FILENAME_PATTERN: str = "Floodgate-Spigot-*-SNAPSHOT.jar"
    PROJECT: str = "floodgate"

    def __init__(self, download_directory: str = DEFAULT_DOWNLOAD_DIR,
                 cache_manager: Optional[CacheManager] = None,
                 project: Optional[str] = None,
                 subpath: Optional[str] = None,
                 download_path: Optional[str] = None,
                 base_url: Optional[str] = None,
                 api_client: Optional[ApiClient] = None) -> None:
        self.cache = cache_manager if cache_manager is not None \
            else CacheManager(self.CACHE_FILE)
        super().__init__(
            download_directory,
            self.cache,
            project if project is not None else self.PROJECT,
            subpath if subpath is not None else self.DOWNLOAD_SUBPATH,
            download_path if download_path is not None else self.DOWNLOAD_PATH,
            base_url,
            api_client
        )

    def download_latest(self) -> Optional[str]:
        """Downloads the latest Floodgate Spigot plugin."""
        return self._download_artifact(filename_pattern=self.FILENAME_PATTERN)
