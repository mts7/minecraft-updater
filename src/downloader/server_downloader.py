from typing import Optional, Tuple
from .geyser_downloader import GeyserDownloader
from .geyser_floodgate_downloader import FloodgateDownloader
from .paper_downloader import PaperDownloader

class ServerDownloader:
    def __init__(self, download_directory: str):
        self.download_directory = download_directory
        # TODO: handle version strategy
        self.paper_downloader = PaperDownloader(download_directory)
        self.geyser_downloader = GeyserDownloader(download_directory)
        self.floodgate_downloader = FloodgateDownloader(download_directory)

    def download_paper(self):
        try:
            return self.paper_downloader.download()
        except Exception as e:
            print(f"Error downloading Paper in {self.download_directory}: {e}")
            return None

    def download_geyser(self):
        try:
            return self.geyser_downloader.download_latest()
        except Exception as e:
            print(f"Error downloading Geyser in {self.download_directory}: {e}")
            return None

    def download_floodgate(self):
        try:
            return self.floodgate_downloader.download_latest()
        except Exception as e:
            print(f"Error downloading Floodgate in {self.download_directory}: {e}")
            return None

    def download_server_files(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        new_paper_file = self.download_paper()
        new_geyser_file = self.download_geyser()
        new_floodgate_file = self.download_floodgate()
        return new_paper_file, new_geyser_file, new_floodgate_file
