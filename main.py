from src.paper_downloader import PaperDownloader
from src.geyser_downloader import GeyserDownloader

if __name__ == "__main__":
    paper_downloader = PaperDownloader()
    print("\n--- Processing Paper Minecraft ---")
    paper_downloader.download()

    # Later, you'll do something similar for other projects:
    # dynmap_updater = DynmapUpdater()
    # print("\n--- Processing Dynmap ---")
    # dynmap_updater.update()

    downloader = GeyserDownloader()
    print("--- Checking and Downloading Latest Geyser ---")
    downloader.download_latest()
    print("--- Geyser check complete. ---")

    latest_version = downloader.get_latest_version()
    latest_build = downloader.get_latest_build()

    if latest_version and latest_build:
        print(f"Latest Geyser Version: {latest_version}")
        print(f"Latest Geyser Build: {latest_build}")
    else:
        print("Could not retrieve latest Geyser version and build.")
