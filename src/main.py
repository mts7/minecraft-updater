import argparse
import sys
from typing import Dict, Optional, Any, Tuple

from src.downloader.server_downloader import ServerDownloader
from src.exceptions import MissingRequiredFieldError, ConfigNotFoundError, \
    ConfigParseError
from src.manager.backup_manager import MinecraftBackupManager
from src.manager.config_manager import ConfigManager
from src.manager.server_manager import MinecraftServerManager

DEFAULT_DOWNLOAD_DIRECTORY = "downloads"
CONFIG_FILE = "config.yaml"


def backup_server(server_name: str, servers_config: Dict[str, Dict[str, Any]]) -> None:
    """Performs a backup of the specified server."""
    server_settings: Dict[str, Any] = servers_config[server_name]

    required_fields = ["server_directory", "backup_directory"]
    for field in required_fields:
        if field not in server_settings or not server_settings[field]:
            raise MissingRequiredFieldError(
                f"Error: '{field}' is required for server '{server_name}' "
                f"in {CONFIG_FILE} for backups."
            )

    server_manager = MinecraftServerManager(
        server_settings['server_directory'],
        server_settings['backup_directory'],
        server_settings.get('screen_name', 'minecraft'))
    backup_manager = MinecraftBackupManager(server_manager)

    backup_manager.backup_files(server_settings.get('backup_exclude', []))


def download_server_updates(server_name: str,
                            servers_config: Dict[str, Dict[str, Any]]) \
        -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Downloads the latest server files for the specified server."""
    server_settings: Dict[str, Any] = servers_config[server_name]

    required_fields = ["download_directory"]
    for field in required_fields:
        if field not in server_settings or not server_settings[field]:
            raise MissingRequiredFieldError(
                f"Error: '{field}' is required for server '{server_name}' "
                f"in {CONFIG_FILE}."
            )

    download_directory: str = server_settings['download_directory']
    downloader = ServerDownloader(download_directory)
    return downloader.download_server_files()


def main():
    parser = argparse.ArgumentParser(
        description="Minecraft Server Management Utility")
    parser.add_argument("--server",
                        help=("The name of the server configuration to use "
                              "(as defined under 'servers' in config.yaml)"))
    args = parser.parse_args()

    servers_config = ConfigManager.load_config(CONFIG_FILE)

    if args.server and args.server in servers_config:
        new_files = download_server_updates(args.server, servers_config)
        if any(new_files):
            backup_server(args.server, servers_config)
        return

    download_directory = DEFAULT_DOWNLOAD_DIRECTORY
    downloader = ServerDownloader(download_directory)
    downloader.download_server_files()


if __name__ == "__main__":
    try:
        main()
    except ConfigNotFoundError as e:
        print(e)
        sys.exit(2)
    except ConfigParseError as e:
        print(e)
        sys.exit(4)
    except MissingRequiredFieldError as e:
        print(e)
        sys.exit(8)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
