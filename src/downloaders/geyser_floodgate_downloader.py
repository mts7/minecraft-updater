from typing import Optional

from src.downloaders.geysermc_downloader import GeyserMcDownloader


class FloodgateDownloader(GeyserMcDownloader):
    API_BASE_URL_V2_LATEST: str = (
        "https://download.geysermc.org/v2/projects/floodgate"
        "/versions/latest/builds/latest"
    )
    PROJECT: str = "floodgate"
    DOWNLOAD_SUBPATH: str = "spigot"
    DEFAULT_DOWNLOAD_DIR: str = "floodgate_downloads"
    FILENAME_PATTERN: str = "Floodgate-Spigot-*-SNAPSHOT.jar"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        super().__init__(download_directory)

    def download_latest(self) -> Optional[str]:
        """Downloads the latest Floodgate Spigot plugin."""
        return self._download_artifact(
            project=self.PROJECT,
            download_subpath=self.DOWNLOAD_SUBPATH,
            filename_pattern=self.FILENAME_PATTERN,
        )
