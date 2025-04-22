from src.paper_downloader import PaperDownloader

if __name__ == "__main__":
    paper_downloader = PaperDownloader()
    print("\n--- Processing Paper Minecraft ---")
    paper_downloader.download()

    # Later, you'll do something similar for other projects:
    # dynmap_updater = DynmapUpdater()
    # print("\n--- Processing Dynmap ---")
    # dynmap_updater.update()
