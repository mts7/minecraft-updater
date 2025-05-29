import argparse
import sys

import pytest
from unittest.mock import patch, MagicMock

from src.exceptions import (
    MissingRequiredFieldError, APIDataError, APIRequestError, BuildDataError,
    ConfigNotFoundError, ConfigParseError, DownloadError, FileAccessError,
    FloodgateDownloadError, GeyserDownloadError, HashCalculationError,
    InvalidPaperVersionFormatError, InvalidVersionDataError,
    NoBuildsFoundError, NoPaperVersionsFoundError, NoStableBuildFoundError,
    PaperDownloadError, VersionInfoError)
from src.main import backup_server, download_server_updates, main, \
    handle_command_line

PAPER_URL = "https://example.com"

GEYSER_URL = "https://geyser.example.com"


class VersionFetchStrategy:
    pass


DEFAULT_DOWNLOAD_DIRECTORY = "downloads"
CONFIG_FILE = "config.yaml"


@patch('src.main.MinecraftBackupManager')
@patch('src.main.MinecraftServerManager')
def test_backup_server_success(mock_server_cls, mock_backup_cls):
    server_name = 'alpha'
    config = {
        'alpha': {
            'server_directory': '/srv/mc',
            'backup_directory': '/data/backups',
            'screen_name': 'mc_alpha',
            'backup_exclude': ['logs/', '*.tmp']
        }
    }

    mock_server_instance = MagicMock()
    mock_server_cls.return_value = mock_server_instance

    mock_backup_instance = MagicMock()
    mock_backup_cls.return_value = mock_backup_instance

    backup_server(server_name, config)

    mock_server_cls.assert_called_once_with('mc_alpha')
    mock_backup_cls.assert_called_once_with(
        mock_server_instance,
        '/srv/mc',
        '/data/backups'
    )
    mock_backup_instance.backup_files.assert_called_once_with(['logs/',
                                                               '*.tmp'])


@patch('src.main.MinecraftBackupManager')
@patch('src.main.MinecraftServerManager')
def test_backup_server_uses_default_screen_name(mock_server_cls,
                                                mock_backup_cls):
    server_name = 'beta'
    config = {
        'beta': {
            'server_directory': '/srv/beta',
            'backup_directory': '/backups/beta'
        }
    }

    mock_server = MagicMock()
    mock_server_cls.return_value = mock_server

    mock_backup = MagicMock()
    mock_backup_cls.return_value = mock_backup

    backup_server(server_name, config)

    mock_server_cls.assert_called_once_with('minecraft')
    mock_backup_cls.assert_called_once_with(
        mock_server,
        '/srv/beta',
        '/backups/beta'
    )
    mock_backup.backup_files.assert_called_once_with([])


@pytest.mark.parametrize("missing_field", ['server_directory',
                                           'backup_directory'])
def test_backup_server_missing_required_fields(missing_field):
    server_name = 'omega'
    config = {
        'omega': {
            'server_directory': '/srv/omega',
            'backup_directory': '/data/omega'
        }
    }
    del config['omega'][missing_field]

    with pytest.raises(MissingRequiredFieldError) as exc_info:
        backup_server(server_name, config)

    assert missing_field in str(exc_info.value)


@patch('src.main.ServerDownloader')
def test_download_server_updates_success(mock_downloader_cls):
    server_name = 'gamma'
    config = {
        'gamma': {
            'download_directory': '/downloads/gamma'
        }
    }
    strategy = MagicMock()

    mock_downloader = MagicMock()
    mock_downloader.download_server_files.return_value = (
        '1.20.1', 'build-456', PAPER_URL + '/download.jar')
    mock_downloader_cls.return_value = mock_downloader

    result = download_server_updates(server_name, config, strategy)

    mock_downloader_cls.assert_called_once_with('/downloads/gamma', strategy)
    mock_downloader.download_server_files.assert_called_once_with()
    assert result == ('1.20.1', 'build-456', PAPER_URL + '/download.jar')


@pytest.mark.parametrize("value", [None, ""])
def test_download_server_updates_missing_download_directory(value):
    server_name = 'delta'
    config = {
        'delta': {
            'download_directory': value
        }
    }
    strategy = MagicMock()

    with pytest.raises(MissingRequiredFieldError) as exc_info:
        download_server_updates(server_name, config, strategy)

    assert "download_directory" in str(exc_info.value)


def test_main_specific_server_updates_no_new_files():
    """Test when a specific server is requested and downloads no new files."""
    mock_arguments = argparse.Namespace(
        server="test_server",
        paper_cache_file=None,
        paper_base_url=PAPER_URL,
        paper_project="paper",
        paper_version="1.20.1",
        geyser_base_url=GEYSER_URL,
    )
    mock_config = {"test_server": {"path": "/path/to/server"}}
    mock_config_loader = MagicMock(return_value=mock_config)
    mock_cache_manager_cls = MagicMock()
    mock_paper_api_client_cls = MagicMock()
    mock_downloader_cls = MagicMock()
    mock_backup_func = MagicMock()
    mock_download_updates_func = MagicMock(return_value=[])
    mock_version_strategy = MagicMock(spec=VersionFetchStrategy)
    mock_create_version_strategy = MagicMock(
        return_value=mock_version_strategy)

    main(
        mock_arguments,
        config_loader=mock_config_loader,
        cache_manager_cls=mock_cache_manager_cls,
        paper_api_client_cls=mock_paper_api_client_cls,
        downloader_cls=mock_downloader_cls,
        backup_func=mock_backup_func,
        download_updates_func=mock_download_updates_func,
        version_strategy_factory=mock_create_version_strategy,
    )

    mock_config_loader.assert_called_once_with(CONFIG_FILE)
    mock_cache_manager_cls.assert_not_called()
    mock_paper_api_client_cls.assert_called_once_with(
        PAPER_URL, "paper", cache_manager=None
    )
    mock_create_version_strategy.assert_called_once_with(
        mock_arguments, mock_paper_api_client_cls.return_value
    )
    mock_download_updates_func.assert_called_once_with(
        "test_server", mock_config, mock_version_strategy
    )
    mock_backup_func.assert_not_called()
    mock_downloader_cls.assert_not_called()


def test_main_specific_server_updates_with_new_files():
    """Test when a specific server is requested and downloads new files."""
    mock_arguments = argparse.Namespace(
        server="test_server",
        paper_cache_file="cache.json",
        paper_base_url=PAPER_URL,
        paper_project="paper",
        paper_version="1.20.1",
        geyser_base_url=GEYSER_URL,
    )
    mock_config = {"test_server": {"path": "/path/to/server"}}
    mock_config_loader = MagicMock(return_value=mock_config)
    mock_cache_manager_cls = MagicMock()
    mock_paper_api_client_cls = MagicMock()
    mock_downloader_cls = MagicMock()
    mock_backup_func = MagicMock()
    mock_download_updates_func = MagicMock(return_value=["server.jar"])
    mock_version_strategy = MagicMock(spec=VersionFetchStrategy)
    mock_create_version_strategy = MagicMock(
        return_value=mock_version_strategy)

    main(
        mock_arguments,
        config_loader=mock_config_loader,
        cache_manager_cls=mock_cache_manager_cls,
        paper_api_client_cls=mock_paper_api_client_cls,
        downloader_cls=mock_downloader_cls,
        backup_func=mock_backup_func,
        download_updates_func=mock_download_updates_func,
        version_strategy_factory=mock_create_version_strategy,
    )

    mock_config_loader.assert_called_once_with(CONFIG_FILE)
    mock_cache_manager_cls.assert_called_once_with("cache.json")
    mock_paper_api_client_cls.assert_called_once_with(
        PAPER_URL, "paper", cache_manager=mock_cache_manager_cls.return_value
    )
    mock_create_version_strategy.assert_called_once_with(
        mock_arguments, mock_paper_api_client_cls.return_value
    )
    mock_download_updates_func.assert_called_once_with(
        "test_server", mock_config, mock_version_strategy
    )
    mock_backup_func.assert_called_once_with("test_server", mock_config)
    mock_downloader_cls.assert_not_called()


def test_main_download_all_servers():
    """Test when no specific server is requested."""
    mock_arguments = argparse.Namespace(
        server=None,
        paper_cache_file="cache.json",
        paper_base_url=PAPER_URL,
        paper_project="paper",
        paper_version="latest",
        geyser_base_url=GEYSER_URL,
    )
    mock_config_loader = MagicMock(return_value={"server1": {}, "server2": {}})
    mock_cache_manager_cls = MagicMock()
    mock_paper_api_client_cls = MagicMock()
    mock_downloader_cls = MagicMock()
    mock_backup_func = MagicMock()
    mock_download_updates_func = MagicMock()
    mock_version_strategy = MagicMock(spec=VersionFetchStrategy)
    mock_create_version_strategy = MagicMock(
        return_value=mock_version_strategy)

    main(
        mock_arguments,
        config_loader=mock_config_loader,
        cache_manager_cls=mock_cache_manager_cls,
        paper_api_client_cls=mock_paper_api_client_cls,
        downloader_cls=mock_downloader_cls,
        backup_func=mock_backup_func,
        download_updates_func=mock_download_updates_func,
        version_strategy_factory=mock_create_version_strategy,
    )

    mock_config_loader.assert_called_once_with(CONFIG_FILE)
    mock_cache_manager_cls.assert_called_once_with("cache.json")
    mock_paper_api_client_cls.assert_called_once_with(
        PAPER_URL, "paper", cache_manager=mock_cache_manager_cls.return_value
    )
    mock_create_version_strategy.assert_called_once_with(
        mock_arguments, mock_paper_api_client_cls.return_value
    )
    mock_download_updates_func.assert_not_called()
    mock_backup_func.assert_not_called()
    mock_downloader_cls.assert_called_once_with(
        DEFAULT_DOWNLOAD_DIRECTORY, mock_version_strategy, GEYSER_URL
    )
    mock_downloader_cls.return_value.download_server_files.assert_called_once()


def test_main_specific_server_not_in_config():
    """Test when a specific server is requested but not found in the config."""
    mock_arguments = argparse.Namespace(
        server="non_existent_server",
        paper_cache_file=None,
        paper_base_url=PAPER_URL,
        paper_project="paper",
        paper_version="latest",
        geyser_base_url=GEYSER_URL,
    )
    mock_config_loader = MagicMock(return_value={"test_server": {}})
    mock_cache_manager_cls = MagicMock()
    mock_paper_api_client_cls = MagicMock()
    mock_downloader_cls = MagicMock()
    mock_backup_func = MagicMock()
    mock_download_updates_func = MagicMock()
    mock_version_strategy = MagicMock(spec=VersionFetchStrategy)
    mock_create_version_strategy = MagicMock(
        return_value=mock_version_strategy)

    main(
        mock_arguments,
        config_loader=mock_config_loader,
        cache_manager_cls=mock_cache_manager_cls,
        paper_api_client_cls=mock_paper_api_client_cls,
        downloader_cls=mock_downloader_cls,
        backup_func=mock_backup_func,
        download_updates_func=mock_download_updates_func,
        version_strategy_factory=mock_create_version_strategy,
    )

    mock_config_loader.assert_called_once_with(CONFIG_FILE)
    mock_cache_manager_cls.assert_not_called()
    mock_paper_api_client_cls.assert_called_once_with(
        PAPER_URL, "paper", cache_manager=None
    )
    mock_create_version_strategy.assert_called_once_with(
        mock_arguments, mock_paper_api_client_cls.return_value
    )
    mock_download_updates_func.assert_not_called()
    mock_backup_func.assert_not_called()
    mock_downloader_cls.assert_called_once_with(
        DEFAULT_DOWNLOAD_DIRECTORY, mock_version_strategy, GEYSER_URL
    )
    mock_downloader_cls.return_value.download_server_files.assert_called_once()


def test_main_no_paper_cache():
    """Test when arguments.paper_cache_file is None."""
    mock_arguments = argparse.Namespace(
        server=None,
        paper_cache_file=None,
        paper_base_url=PAPER_URL,
        paper_project="paper",
        paper_version="latest",
        geyser_base_url=GEYSER_URL,
    )
    mock_config_loader = MagicMock(return_value={})
    mock_cache_manager_cls = MagicMock()
    mock_paper_api_client_cls = MagicMock()
    mock_downloader_cls = MagicMock()
    mock_backup_func = MagicMock()
    mock_download_updates_func = MagicMock()
    mock_version_strategy = MagicMock(spec=VersionFetchStrategy)
    mock_create_version_strategy = MagicMock(
        return_value=mock_version_strategy)

    main(
        mock_arguments,
        config_loader=mock_config_loader,
        cache_manager_cls=mock_cache_manager_cls,
        paper_api_client_cls=mock_paper_api_client_cls,
        downloader_cls=mock_downloader_cls,
        backup_func=mock_backup_func,
        download_updates_func=mock_download_updates_func,
        version_strategy_factory=mock_create_version_strategy,
    )

    mock_config_loader.assert_called_once_with(CONFIG_FILE)
    mock_cache_manager_cls.assert_not_called()
    mock_paper_api_client_cls.assert_called_once_with(
        PAPER_URL, "paper", cache_manager=None
    )
    mock_create_version_strategy.assert_called_once_with(
        mock_arguments, mock_paper_api_client_cls.return_value
    )
    mock_download_updates_func.assert_not_called()
    mock_backup_func.assert_not_called()
    mock_downloader_cls.assert_called_once_with(
        DEFAULT_DOWNLOAD_DIRECTORY, mock_version_strategy, GEYSER_URL
    )
    mock_downloader_cls.return_value.download_server_files.assert_called_once()


def simulate_args(*args):
    return ["prog"] + list(args)


@pytest.mark.parametrize("exception_class,expected_exit_code", [
    (APIDataError("msg", Exception("original")), 18),
    (APIRequestError("msg", Exception("original")), 17),
    (BuildDataError("msg"), 6),
    (ConfigNotFoundError("msg"), 3),
    (ConfigParseError("msg"), 4),
    (DownloadError("msg"), 7),
    (FileAccessError("msg", Exception("original")), 19),
    (FloodgateDownloadError("msg"), 12),
    (GeyserDownloadError("msg", Exception("original")), 11),
    (HashCalculationError("msg", Exception("original")), 20),
    (InvalidPaperVersionFormatError("msg"), 9),
    (InvalidVersionDataError("msg"), 16),
    (MissingRequiredFieldError("msg"), 5),
    (NoBuildsFoundError("msg"), 8),
    (NoPaperVersionsFoundError("msg"), 14),
    (NoStableBuildFoundError("msg"), 15),
    (PaperDownloadError("msg", Exception("original")), 10),
    (VersionInfoError("msg", Exception("original")), 13),
    (RuntimeError("runtime failure"), 2),
    (Exception("unexpected failure"), 1),
])
def test_handle_command_line_exceptions(exception_class, expected_exit_code):
    with patch.object(sys, 'argv', simulate_args("--server", "test")), \
         patch("src.main.main", side_effect=exception_class), \
         patch("traceback.print_exception"), \
         patch("builtins.print") as mock_print:

        with pytest.raises(SystemExit) as e:
            handle_command_line()

        assert e.value.code == expected_exit_code
        assert mock_print.call_count > 0


def test_handle_command_line_success():
    with patch.object(sys, 'argv', simulate_args("--server", "test")), \
         patch("src.main.main") as mock_main:

        handle_command_line()
        mock_main.assert_called_once()


def test_handle_command_line_invalid_version_error_message(capsys):
    exception = InvalidPaperVersionFormatError("msg")
    with patch.object(sys, 'argv', simulate_args("--paper-version", "bad")), \
         patch("src.main.main", side_effect=exception):

        with pytest.raises(SystemExit) as e:
            handle_command_line()

        assert e.value.code == 9
        captured = capsys.readouterr()
        assert "Invalid Paper version format" in captured.out
