import argparse
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Any, Tuple

import yaml

from downloaders.geyser_downloader import GeyserDownloader
from downloaders.geyser_floodgate_downloader import FloodgateDownloader
from downloaders.paper_downloader import PaperDownloader
from updater.file_manager import FileManager

DEFAULT_DOWNLOAD_DIRECTORY = "downloads"
CONFIG_FILE = "config.yaml"
EXAMPLE_CONFIG_FILE = "example.config.yaml"


def backup_files(server_dir, backup_dir, screen_name, exclude):
    print("\n--- Backing up Server Files ---")
    file_manager = FileManager(server_dir, backup_dir, screen_name)
    file_manager.create_server_backup(exclude_patterns=exclude)
    print("--- Server backup complete. ---")


def download_and_backup(server_name: str,
                        servers_config: Dict[str, Dict[str, Any]]) -> None:
    """Downloads server files and performs a backup if needed.

    Args:
        server_name: The name of the server configuration to use.
        servers_config: A dictionary containing server configurations.
    """
    if server_name not in servers_config:
        print(
            f"Error: Server configuration '{server_name}' not found "
            f"in {CONFIG_FILE} under the 'servers' section.")
        sys.exit(1)

    server_settings: Dict[str, Any] = servers_config[server_name]

    required_fields = ["download_directory", "server_directory",
                       "backup_directory"]
    for field in required_fields:
        if field not in server_settings or not server_settings[field]:
            print(
                f"Error: '{field}' is a required field for "
                f"server '{server_name}' in {CONFIG_FILE}.")
            sys.exit(1)

    download_directory: str = server_settings['download_directory']

    print(f"--- Downloading server files to: {download_directory} ---")
    new_paper_file, new_geyser_file, new_floodgate_file = (
        download_server_files(download_directory))

    perform_backup_if_needed(server_settings, new_paper_file, new_geyser_file,
                             new_floodgate_file)


def download_floodgate(download_directory) -> None:
    print("\n--- Checking and Downloading Latest Floodgate ---")
    floodgate_downloader = FloodgateDownloader(download_directory)
    floodgate_downloader.download_latest()


def download_geyser(download_directory) -> None:
    geyser_downloader = GeyserDownloader(download_directory)
    print("--- Checking and Downloading Latest Geyser ---")
    geyser_downloader.download_latest()


def download_paper(download_directory) -> None:
    paper_downloader = PaperDownloader(download_directory)
    print("\n--- Processing Paper Minecraft ---")
    paper_downloader.download()


def download_server_files(download_directory: str)\
        -> Tuple[Optional[str], Optional[str], Optional[str]]:
    print(f"--- Downloading server files to: {download_directory} ---")
    paper_downloader = PaperDownloader(download_directory)
    geyser_downloader = GeyserDownloader(download_directory)
    floodgate_downloader = FloodgateDownloader(download_directory)

    new_paper_file = paper_downloader.download()
    new_geyser_file = geyser_downloader.download_latest()
    new_floodgate_file = floodgate_downloader.download_latest()

    return new_paper_file, new_geyser_file, new_floodgate_file


def get_backup_path(server_directory: str, backup_directory: str)\
        -> Optional[str]:
    """Constructs the backup filepath and checks for existing backups."""
    server_dirname: str = os.path.basename(server_directory.rstrip('/'))
    backup_filename: str = (f"mcbackup_{server_dirname}_"
                            f"{datetime.now().strftime('%Y-%m-%d-%H')}.tar.gz")
    backup_filepath: str = os.path.join(backup_directory, backup_filename)

    if os.path.exists(backup_filepath):
        print(f"Backup already exists: {backup_filepath}. Skipping backup.")
        return None

    return backup_filepath


def load_config(filepath: str = CONFIG_FILE) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(filepath):
        print(f"Error: Configuration file '{filepath}' not found.")
        if os.path.exists(EXAMPLE_CONFIG_FILE):
            print(
                "An example configuration file "
                f"'{EXAMPLE_CONFIG_FILE}' exists.")
            print(
                f"You can copy or rename it to '{CONFIG_FILE}' "
                "and modify it with your settings.")
        sys.exit(1)

    try:
        with open(filepath, 'r') as f:
            config: Dict[str, Any] = yaml.safe_load(f) or {}
        return config.get('servers', {})
    except yaml.YAMLError as e:
        print(f"Error parsing '{filepath}': {e}")
        sys.exit(1)


def perform_backup_if_needed(
        server_settings: Dict[str, Any],
        new_paper_file: Optional[str],
        new_geyser_file: Optional[str],
        new_floodgate_file: Optional[str],
) -> None:
    if not (new_paper_file or new_geyser_file or new_floodgate_file):
        print("No new server files downloaded, skipping backup.")
        return

    server_directory: str = server_settings['server_directory']
    backup_directory: str = server_settings['backup_directory']

    backup_filepath = get_backup_path(server_directory, backup_directory)
    if not backup_filepath:
        return

    print(f"--- Performing backup to: {backup_filepath} ---")
    backup_files(
        server_directory,
        backup_directory,
        server_settings.get('screen_name', 'minecraft'),
        server_settings.get('backup_exclude', []),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Server Management Utility")
    parser.add_argument("--server",
                        help=("The name of the server configuration to use "
                              "(as defined under 'servers' in config.yaml)"))
    args = parser.parse_args()

    servers_config = load_config()
    download_directory = DEFAULT_DOWNLOAD_DIRECTORY

    if args.server:
        download_and_backup(args.server, servers_config)
    else:
        download_server_files(download_directory)


if __name__ == "__main__":
    main()
