from typing import Optional, Tuple

from src.downloader.geyser_downloader import GeyserDownloader
from src.downloader.geyser_floodgate_downloader import FloodgateDownloader
from src.downloader.paper_downloader import PaperDownloader
from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.exceptions import PaperDownloadError, GeyserDownloadError, \
    FloodgateDownloadError
from src.utilities.paper_api import PaperApiClient


class ServerDownloader:
    def __init__(self, download_directory: str,
                 paper_version_strategy: VersionFetchStrategy):
        paper_api_client = PaperApiClient()
        self.download_directory = download_directory
        self.paper_downloader = PaperDownloader(paper_version_strategy,
                                                paper_api_client,
                                                download_directory)
        self.geyser_downloader = GeyserDownloader(download_directory)
        self.floodgate_downloader = FloodgateDownloader(download_directory)

    def download_paper(self):
        version_info = (self.paper_downloader.version_strategy
                        .get_version_and_build())
        if not version_info:
            return None

        version, build = version_info

        if build is not None:
            try:
                return self.paper_downloader.download_build(version, build)
            except Exception as e:
                raise PaperDownloadError(
                    f"Error downloading Paper version {version}, "
                    f"build {build}",
                    original_exception=e) from e
        else:
            try:
                return self.paper_downloader.download_specific_version(version)
            except Exception as e:
                raise PaperDownloadError(
                    f"Error downloading specific Paper version {version}",
                    original_exception=e) from e

    def download_geyser(self):
        try:
            return self.geyser_downloader.download_latest()
        except Exception as e:
            raise GeyserDownloadError(
                f"Error downloading Geyser in {self.download_directory}",
                original_exception=e) from e

    def download_floodgate(self):
        try:
            return self.floodgate_downloader.download_latest()
        except Exception as e:
            raise FloodgateDownloadError(
                f"Error downloading Floodgate in {self.download_directory}",
                original_exception=e) from e

    def download_server_files(self)\
            -> Tuple[Optional[str], Optional[str], Optional[str]]:
        paper_file = self.download_paper()
        geyser_file = self.download_geyser()
        floodgate_file = self.download_floodgate()
        return paper_file, geyser_file, floodgate_file
