import os
import argparse
import yaml
import sys

from downloaders.paper_downloader import PaperDownloader
from downloaders.geyser_downloader import GeyserDownloader
from downloaders.geyser_floodgate_downloader import FloodgateDownloader
from updater.file_manager import FileManager

DEFAULT_DOWNLOAD_DIRECTORY = "downloads"
CONFIG_FILE = "config.yaml"
EXAMPLE_CONFIG_FILE = "example.config.yaml"

def load_config(filepath=CONFIG_FILE):
    if not os.path.exists(filepath):
        print(f"Error: Configuration file '{filepath}' not found.")
        if os.path.exists(EXAMPLE_CONFIG_FILE):
            print(f"An example configuration file '{EXAMPLE_CONFIG_FILE}' exists.")
            print(f"You can copy or rename it to '{CONFIG_FILE}' and modify it with your settings.")
        sys.exit(1)

    try:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f) or {}
        return config.get('servers', {})
    except yaml.YAMLError as e:
        print(f"Error parsing '{filepath}': {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Minecraft Server Management Utility")
    parser.add_argument("--server", required=True, help="The name of the server configuration to use (as defined under 'servers' in config.yaml)")
    parser.add_argument("--download_dir", help="Override default download directory")
    args = parser.parse_args()

    servers_config = load_config()
    server_name = args.server

    if server_name in servers_config:
        server_settings = servers_config[server_name]

        download_directory = args.download_dir or server_settings.get('download_directory', DEFAULT_DOWNLOAD_DIRECTORY)
        server_directory = server_settings.get('server_directory')
        backup_directory = server_settings.get('backup_directory')
        screen_name = server_settings.get('screen_name', 'minecraft')
        exclude_backup = server_settings.get('backup_exclude', [])

        if server_directory and backup_directory:
            backup_files(server_directory, backup_directory, screen_name, exclude_backup)
        else:
            print(f"Warning: 'server_directory' or 'backup_directory' not defined for server '{server_name}' in {CONFIG_FILE}. Skipping backup.")

        download_paper(download_directory)
        download_geyser(download_directory)
        download_floodgate(download_directory)

    else:
        print(f"Error: Server configuration '{server_name}' not found in {CONFIG_FILE} under the 'servers' section.")
        sys.exit(1)

def download_floodgate(download_directory):
    print("\n--- Checking and Downloading Latest Floodgate ---")
    floodgate_downloader = FloodgateDownloader(download_directory)
    floodgate_downloader.download_latest()
    print("--- Floodgate check complete. ---")
    latest_floodgate_version = floodgate_downloader.get_latest_version()
    latest_floodgate_build = floodgate_downloader.get_latest_build()
    if latest_floodgate_version and latest_floodgate_build:
        print(f"Latest Floodgate Version: {latest_floodgate_version}")
        print(f"Latest Floodgate Build: {latest_floodgate_build}")
    else:
        print("Could not retrieve latest Floodgate version and build.")

def download_geyser(download_directory):
    geyser_downloader = GeyserDownloader(download_directory)
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

def download_paper(download_directory):
    paper_downloader = PaperDownloader(download_directory)
    print("\n--- Processing Paper Minecraft ---")
    paper_downloader.download()

def backup_files(server_dir, backup_dir, screen_name, exclude):
    print("\n--- Backing up Server Files ---")
    file_manager = FileManager(server_dir, backup_dir, screen_name)
    file_manager.create_server_backup(exclude_patterns=exclude)
    print("--- Server backup complete. ---")

if __name__ == "__main__":
    main()
