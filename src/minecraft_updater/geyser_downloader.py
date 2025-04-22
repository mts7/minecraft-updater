from minecraft_updater.geysermc_downloader import GeyserMcDownloader

class GeyserDownloader(GeyserMcDownloader):
    API_BASE_URL_V2_LATEST = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest"
    PROJECT = "geyser"
    DOWNLOAD_SUBPATH = "spigot"
    DEFAULT_DOWNLOAD_DIR = "geyser_downloads"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        super().__init__(download_directory)
