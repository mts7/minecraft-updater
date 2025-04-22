from minecraft_updater.paper_downloader import PaperDownloader
from minecraft_updater.geyser_downloader import GeyserDownloader
from minecraft_updater.geyser_floodgate_downloader import FloodgateDownloader
from minecraft_updater.viaversion_downloader import ViaVersionDownloader

DOWNLOAD_DIRECTORY = "downloads"

def main():
    paper_downloader = PaperDownloader(DOWNLOAD_DIRECTORY)
    print("\n--- Processing Paper Minecraft ---")
    paper_downloader.download()

    geyser_downloader = GeyserDownloader(DOWNLOAD_DIRECTORY)
    print("--- Checking and Downloading Latest Geyser ---")
    geyser_downloader.download_latest()
    print("--- Geyser check complete. ---")

    latest_geyser_version = geyser_downloader.get_latest_version()
    latest_geyser_build = geyser_downloader.get_latest_build()

    if latest_geyser_version and latest_geyser_build:
        print(f"Latest Geyser Version: {latest_geyser_version}")
        print(f"Latest Geyser Build: {latest_geyser_build}")
    else:
        print("Could not retrieve latest Geyser version and build.")

    print("\n--- Checking and Downloading Latest Floodgate ---")
    floodgate_downloader = FloodgateDownloader(DOWNLOAD_DIRECTORY)
    floodgate_downloader.download_latest()
    print("--- Floodgate check complete. ---")

    latest_floodgate_version = floodgate_downloader.get_latest_version()
    latest_floodgate_build = floodgate_downloader.get_latest_build()

    if latest_floodgate_version and latest_floodgate_build:
        print(f"Latest Floodgate Version: {latest_floodgate_version}")
        print(f"Latest Floodgate Build: {latest_floodgate_build}")
    else:
        print("Could not retrieve latest Floodgate version and build.")

    viaversion_downloader = ViaVersionDownloader(download_directory=DOWNLOAD_DIRECTORY)
    print("\n--- Checking and Downloading Latest ViaVersion ---")
    viaversion_downloader.download_latest()
    print("--- ViaVersion check complete. ---")

if __name__ == "__main__":
    main()
