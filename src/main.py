import argparse
import sys
import traceback
from typing import Dict, Optional, Any, Tuple

from src.downloader.paper_version_strategy.latest_version_strategy import \
    LatestVersionStrategy
from src.downloader.paper_version_strategy.specific_version_strategy import \
    SpecificVersionStrategy
from src.downloader.paper_version_strategy.stable_version_strategy import \
    StableVersionStrategy
from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.downloader.server_downloader import ServerDownloader
from src.exceptions import APIRequestError, APIDataError
from src.exceptions import MissingRequiredFieldError, ConfigNotFoundError, \
    ConfigParseError, NoBuildsFoundError, DownloadError, BuildDataError, \
    InvalidPaperVersionFormatError, PaperDownloadError, GeyserDownloadError, \
    FloodgateDownloadError, VersionInfoError, NoStableBuildFoundError, \
    NoPaperVersionsFoundError, InvalidVersionDataError, FileAccessError, \
    HashCalculationError
from src.manager.backup_manager import MinecraftBackupManager
from src.manager.cache_manager import CacheManager
from src.manager.config_manager import ConfigManager
from src.manager.server_manager import MinecraftServerManager
from src.utilities.paper_api import PaperApiClient

DEFAULT_DOWNLOAD_DIRECTORY = "downloads"
CONFIG_FILE = "config.yaml"


def backup_server(server_name: str,
                  servers_config: Dict[str, Dict[str, Any]]) -> None:
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
                            servers_config: Dict[str, Dict[str, Any]],
                            paper_version_strategy: VersionFetchStrategy) \
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
    downloader = ServerDownloader(download_directory, paper_version_strategy)
    return downloader.download_server_files()


def main(arguments: argparse.Namespace):
    """Orchestrates the server management tasks."""
    servers_config = ConfigManager.load_config(CONFIG_FILE)
    cache_manager = CacheManager(arguments.paper_cache_file) \
        if arguments.paper_cache_file else None
    paper_api_client = PaperApiClient(arguments.paper_base_url,
                                      arguments.paper_project,
                                      cache_manager=cache_manager)

    paper_version = arguments.paper_version
    paper_version_strategy: VersionFetchStrategy
    if paper_version == "latest":
        paper_version_strategy = LatestVersionStrategy(paper_api_client)
    elif paper_version is None or paper_version != "stable":
        paper_version_strategy = SpecificVersionStrategy(paper_api_client,
                                                         paper_version)
    else:
        paper_version_strategy = StableVersionStrategy(paper_api_client)

    if arguments.server and arguments.server in servers_config:
        new_files = download_server_updates(arguments.server, servers_config,
                                            paper_version_strategy)
        if any(new_files):
            backup_server(arguments.server, servers_config)
        return

    download_directory = DEFAULT_DOWNLOAD_DIRECTORY
    downloader = ServerDownloader(download_directory, paper_version_strategy)
    downloader.download_server_files()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Minecraft Server Management Utility")
    parser.add_argument("--server",
                        help=("The name of the server configuration to use "
                              "(as defined under 'servers' in config.yaml)"))
    parser.add_argument("--paper-version",
                        default="stable",
                        help="Specify 'stable', 'latest', or a specific Paper "
                             "version (e.g., '1.20.4'). Defaults to 'stable'.")
    parser.add_argument("--paper-base-url",
                        help="The base URL for the Paper API.")
    parser.add_argument("--paper-project",
                        help="The Paper project to use.")
    parser.add_argument("--paper-cache-file",
                        help="The path to the cache file.")
    args = parser.parse_args()

    try:
        main(args)
    except APIDataError as e:
        print(f"Error during API JSON parsing: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(18)
    except APIRequestError as e:
        print(f"Error during API request: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(17)
    except BuildDataError as e:
        print(f"Error with Paper build data: {e}")
        sys.exit(6)
    except ConfigNotFoundError as e:
        print(e)
        sys.exit(3)
    except ConfigParseError as e:
        print(e)
        sys.exit(4)
    except DownloadError as e:
        print(f"Error during download: {e}")
        sys.exit(7)
    except FileAccessError as e:
        print(f"Error checking file: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(19)
    except FloodgateDownloadError as e:
        print(f"Error downloading Floodgate: {e}")
        sys.exit(12)
    except GeyserDownloadError as e:
        print(f"Error downloading Geyser: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(11)
    except HashCalculationError as e:
        print(f"Error validating hash for file: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(20)
    except InvalidPaperVersionFormatError as e:
        print(
            f"Error: Invalid Paper version format '{args.paper_version}'. "
            "Please use 'stable', 'latest', or a specific version string "
            "(e.g., '1.21.4').")
        print(e)
        sys.exit(9)
    except InvalidVersionDataError as e:
        print(e)
        sys.exit(16)
    except MissingRequiredFieldError as e:
        print(e)
        sys.exit(5)
    except NoBuildsFoundError as e:
        print(e)
        sys.exit(8)
    except NoPaperVersionsFoundError as e:
        print(e)
        sys.exit(14)
    except NoStableBuildFoundError as e:
        print(e)
        sys.exit(15)
    except PaperDownloadError as e:
        print(f"Error downloading Paper: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(10)
    except VersionInfoError as e:
        print(f"Error fetching build information: {e}")
        print(e.original_exception)
        if e.original_exception:
            traceback.print_exception(type(e.original_exception),
                                      e.original_exception, e.__traceback__)
        sys.exit(13)
    except RuntimeError as e:
        print(e)
        traceback.print_exception(type(e), e, e.__traceback__)
        sys.exit(2)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        sys.exit(1)
