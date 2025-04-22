from src.geysermc_downloader import GeyserMcDownloader

class FloodgateDownloader(GeyserMcDownloader):
    API_BASE_URL_V2_LATEST = "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest"
    PROJECT = "floodgate"
    DOWNLOAD_SUBPATH = "spigot"  # Assuming Floodgate also uses 'spigot' as the key
    DEFAULT_DOWNLOAD_DIR = "floodgate_downloads"

    def __init__(self, download_directory=DEFAULT_DOWNLOAD_DIR):
        super().__init__(download_directory)
