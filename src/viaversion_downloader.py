from src.spigotmc_downloader import SpigotMCPluginDownloader

class ViaVersionDownloader(SpigotMCPluginDownloader):
    SPIGOTMC_URL = "https://www.spigotmc.org/resources/viaversion.19254/"
    DEFAULT_DOWNLOAD_DIR = "viaversion_downloads"
    FILENAME = "ViaVersion.jar"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        super().__init__(download_directory, self.FILENAME, self.SPIGOTMC_URL)
