from src.downloader.geysermc_downloader import GeyserMcDownloader
from typing import Optional


class GeyserDownloader(GeyserMcDownloader):
    API_BASE_URL_V2_LATEST: str = (
        "https://download.geysermc.org/v2/"
        "projects/geyser/versions/latest/builds/latest"
    )
    PROJECT: str = "geyser"
    DOWNLOAD_SUBPATH: str = "spigot"
    DEFAULT_DOWNLOAD_DIR: str = "geyser_downloads"
    FILENAME_PATTERN: str = "Geyser-Spigot-*-SNAPSHOT.jar"

    def __init__(self, download_directory: str = DEFAULT_DOWNLOAD_DIR) -> None:
        super().__init__(download_directory)

    def download_latest(self) -> Optional[str]:
        """Downloads the latest Geyser Spigot plugin."""
        return self._download_artifact(
            project=self.PROJECT,
            download_subpath=self.DOWNLOAD_SUBPATH,
            filename_pattern=self.FILENAME_PATTERN,
        )
