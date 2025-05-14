import argparse
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
import yaml

from src.downloader.geyser_downloader import GeyserDownloader
from src.downloader.geyser_floodgate_downloader import FloodgateDownloader
from src.downloader.paper_downloader import PaperDownloader
from src.main import MissingRequiredFieldError, CONFIG_FILE, \
        ConfigParseError, ConfigNotFoundError, main, DEFAULT_DOWNLOAD_DIRECTORY
from src.manager.file_manager import FileManager


def test_backup_files_calls_create_server_backup():
    """
    Tests that backup_files instantiates FileManager and calls
    create_server_backup with the correct exclude patterns.
    """
    server_dir = "test_server"
    backup_dir = "test_backup"
    screen_name = "mc_server"
    exclude_patterns = ["*.log", "cache/*"]

    mock_create_backup = patch.object(FileManager, 'create_server_backup')

    with mock_create_backup as mocked_method:
        backup_files(server_dir, backup_dir, screen_name, exclude_patterns)

        mocked_method.assert_called_once_with(
            exclude_patterns=exclude_patterns)


def test_download_and_backup_successful_run(tmp_path):
    """
    Tests a successful run of download_and_backup, ensuring
    download_server_files and perform_backup_if_needed are called.
    """
    server_name = "test_server"
    servers_config = {
        server_name: {
            "download_directory": str(tmp_path / "dl"),
            "server_directory": str(tmp_path / "srv"),
            "backup_directory": str(tmp_path / "bak"),
        }
    }
    mock_download = patch("main.download_server_files",
                          return_value=("paper.jar", "geyser.jar",
                                        "floodgate.jar"))
    mock_backup = patch("main.perform_backup_if_needed")
    mock_print = patch("builtins.print")

    with mock_download as mocked_download, \
            mock_backup as mocked_backup, \
            mock_print as mocked_print:
        download_and_backup(server_name, servers_config)

        mocked_download.assert_called_once_with(str(tmp_path / "dl"))

        mocked_backup.assert_called_once_with(
            servers_config[server_name], "paper.jar", "geyser.jar",
            "floodgate.jar"
        )


def test_download_and_backup_server_not_found(capsys):
    """
    Tests the case where the specified server name is not found in the config.
    """
    server_name = "nonexistent_server"
    servers_config = {"test_server": {}}

    with pytest.raises(ServerConfigNotFoundError) as excinfo:
        download_and_backup(server_name, servers_config)
        captured = capsys.readouterr()
        assert str(excinfo.value) == (
            f"Error: Server configuration '{server_name}' not found "
            f"in {CONFIG_FILE} under the 'servers' section."
        )
        assert (
                f"Error: Server configuration '{server_name}' not found "
                f"in {CONFIG_FILE} under the 'servers' section.\n" == captured.err
        )


def test_download_and_backup_missing_required_field(tmp_path, capsys):
    """
    Tests the case where a required field is missing in the server config.
    """
    server_name = "test_server"
    servers_config = {
        server_name: {
            "download_directory": str(tmp_path / "dl"),
            "backup_directory": str(tmp_path / "bak"),
        }
    }

    with pytest.raises(MissingRequiredFieldError) as excinfo:
        download_and_backup(server_name, servers_config)
        captured = capsys.readouterr()
        assert str(excinfo.value) == (
            f"Error: 'server_directory' is a required field for server '{server_name}' in {CONFIG_FILE}."
        )
        assert (
                f"Error: 'server_directory' is a required field for server '{server_name}' in {CONFIG_FILE}.\n" == captured.err
        )


def test_download_floodgate_calls_downloader(tmp_path):
    """
    Tests that download_floodgate instantiates FloodgateDownloader
    and calls download_latest.
    """
    download_directory = str(tmp_path / "floodgate_downloads")

    mock_floodgate_downloader = MagicMock(spec=FloodgateDownloader)

    with patch('main.FloodgateDownloader',
               return_value=mock_floodgate_downloader) as MockedFloodgateClass:
        download_floodgate(download_directory)

        MockedFloodgateClass.assert_called_once_with(download_directory)

        mock_floodgate_downloader.download_latest.assert_called_once()


def test_download_floodgate_handles_downloader_errors(tmp_path):
    """
    Tests that download_floodgate handles potential exceptions raised
    by the FloodgateDownloader.download_latest method.
    """
    download_directory = str(tmp_path / "floodgate_downloads")

    mock_floodgate_downloader = MagicMock(spec=FloodgateDownloader)
    mock_floodgate_downloader.download_latest.side_effect = Exception(
        "Download failed")

    with patch('main.FloodgateDownloader',
               return_value=mock_floodgate_downloader) as MockedFloodgateClass:
        try:
            download_floodgate(download_directory)
        except Exception as e:
            assert str(e) == "Download failed"

        MockedFloodgateClass.assert_called_once_with(download_directory)

        mock_floodgate_downloader.download_latest.assert_called_once()


def test_download_geyser_calls_downloader(tmp_path):
    """
    Tests that download_geyser instantiates GeyserDownloader
    and calls download_latest.
    """
    download_directory = str(tmp_path / "geyser_downloads")

    mock_geyser_downloader = MagicMock(spec=GeyserDownloader)

    with patch('main.GeyserDownloader',
               return_value=mock_geyser_downloader) as MockedGeyserClass:
        download_geyser(download_directory)

        MockedGeyserClass.assert_called_once_with(download_directory)

        mock_geyser_downloader.download_latest.assert_called_once()


def test_download_geyser_handles_downloader_errors(tmp_path):
    """
    Tests that download_geyser handles potential exceptions raised
    by the GeyserDownloader.download_latest method.
    """
    download_directory = str(tmp_path / "geyser_downloads")

    mock_geyser_downloader = MagicMock(spec=GeyserDownloader)
    mock_geyser_downloader.download_latest.side_effect = Exception(
        "Download failed")

    with patch('main.GeyserDownloader',
               return_value=mock_geyser_downloader) as MockedGeyserClass:
        try:
            download_geyser(download_directory)
        except Exception as e:
            assert str(e) == "Download failed"

        MockedGeyserClass.assert_called_once_with(download_directory)

        mock_geyser_downloader.download_latest.assert_called_once()


def test_download_paper_calls_downloader(tmp_path):
    """
    Tests that download_paper instantiates PaperDownloader
    and calls download.
    """
    download_directory = str(tmp_path / "paper_downloads")

    mock_paper_downloader = MagicMock(spec=PaperDownloader)

    with patch('main.PaperDownloader',
               return_value=mock_paper_downloader) as MockedPaperClass:
        download_paper(download_directory)

        MockedPaperClass.assert_called_once_with(download_directory)

        mock_paper_downloader.download.assert_called_once()


def test_download_paper_handles_downloader_errors(tmp_path):
    """
    Tests that download_paper handles potential exceptions raised
    by the PaperDownloader.download method.
    """
    download_directory = str(tmp_path / "paper_downloads")

    mock_paper_downloader = MagicMock(spec=PaperDownloader)
    mock_paper_downloader.download.side_effect = Exception("Download failed")

    with patch('main.PaperDownloader',
               return_value=mock_paper_downloader) as MockedPaperClass:
        try:
            download_paper(download_directory)
        except Exception as e:
            assert str(e) == "Download failed"

        MockedPaperClass.assert_called_once_with(download_directory)

        mock_paper_downloader.download.assert_called_once()


def test_download_server_files_calls_downloaders(tmp_path):
    """
    Tests that download_server_files instantiates PaperDownloader,
    GeyserDownloader, and FloodgateDownloader and calls their
    respective download methods.
    """
    download_directory = str(tmp_path / "server_downloads")

    mock_paper_downloader = MagicMock(spec=PaperDownloader)
    mock_geyser_downloader = MagicMock(spec=GeyserDownloader)
    mock_floodgate_downloader = MagicMock(spec=FloodgateDownloader)

    with patch('main.PaperDownloader',
               return_value=mock_paper_downloader) as MockedPaperClass, \
            patch('main.GeyserDownloader',
                  return_value=mock_geyser_downloader) as MockedGeyserClass, \
            patch('main.FloodgateDownloader',
                  return_value=mock_floodgate_downloader) as MockedFloodgateClass:
        download_server_files(download_directory)

        MockedPaperClass.assert_called_once_with(download_directory)
        MockedGeyserClass.assert_called_once_with(download_directory)
        MockedFloodgateClass.assert_called_once_with(download_directory)

        mock_paper_downloader.download.assert_called_once()
        mock_geyser_downloader.download_latest.assert_called_once()
        mock_floodgate_downloader.download_latest.assert_called_once()


def test_download_server_files_returns_downloaded_filenames(tmp_path):
    """
    Tests that download_server_files returns the filenames returned
    by the downloader instances.
    """
    download_directory = str(tmp_path / "server_downloads")

    mock_paper_downloader = MagicMock(spec=PaperDownloader)
    mock_paper_downloader.download.return_value = "paper-1.20.jar"
    mock_geyser_downloader = MagicMock(spec=GeyserDownloader)
    mock_geyser_downloader.download_latest.return_value = "Geyser-2.2.0.jar"
    mock_floodgate_downloader = MagicMock(spec=FloodgateDownloader)
    mock_floodgate_downloader.download_latest.return_value = "Floodgate-latest.jar"

    with patch('main.PaperDownloader', return_value=mock_paper_downloader), \
            patch('main.GeyserDownloader',
                  return_value=mock_geyser_downloader), \
            patch('main.FloodgateDownloader',
                  return_value=mock_floodgate_downloader):
        paper_file, geyser_file, floodgate_file = download_server_files(
            download_directory)

        assert paper_file == "paper-1.20.jar"
        assert geyser_file == "Geyser-2.2.0.jar"
        assert floodgate_file == "Floodgate-latest.jar"


def test_download_server_files_handles_downloader_errors(tmp_path):
    """
    Tests that download_server_files handles potential exceptions raised
    by the downloader methods. It should not raise these exceptions itself.
    """
    download_directory = str(tmp_path / "server_downloads")

    mock_paper_downloader = MagicMock(spec=PaperDownloader)
    mock_paper_downloader.download.side_effect = Exception(
        "Paper download failed")
    mock_geyser_downloader = MagicMock(spec=GeyserDownloader)
    mock_geyser_downloader.download_latest.side_effect = Exception(
        "Geyser download failed")
    mock_floodgate_downloader = MagicMock(spec=FloodgateDownloader)
    mock_floodgate_downloader.download_latest.side_effect = Exception(
        "Floodgate download failed")

    with patch('main.PaperDownloader', return_value=mock_paper_downloader), \
            patch('main.GeyserDownloader',
                  return_value=mock_geyser_downloader), \
            patch('main.FloodgateDownloader',
                  return_value=mock_floodgate_downloader):
        paper_file, geyser_file, floodgate_file = download_server_files(
            download_directory)

        assert paper_file is None
        assert geyser_file is None
        assert floodgate_file is None

        mock_paper_downloader.download.assert_called_once()
        mock_geyser_downloader.download_latest.assert_called_once()
        mock_floodgate_downloader.download_latest.assert_called_once()


def test_get_backup_path_constructs_filepath(tmp_path):
    """
    Tests that get_backup_path constructs the backup filepath correctly.
    """
    server_directory = str(tmp_path / "server")
    backup_directory = str(tmp_path / "backup")
    os.makedirs(server_directory, exist_ok=True)
    os.makedirs(backup_directory, exist_ok=True)

    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 5, 3, 10, 0, 0)
        expected_filename = "mcbackup_server_2025-05-03-10.tar.gz"
        expected_filepath = os.path.join(backup_directory, expected_filename)
        backup_path = get_backup_path(server_directory, backup_directory)
        assert backup_path == expected_filepath


def test_get_backup_path_constructs_filepath_with_trailing_slash(tmp_path):
    """
    Tests that get_backup_path handles server directories with trailing slashes.
    """
    server_directory = str(tmp_path / "server/")
    backup_directory = str(tmp_path / "backup")
    os.makedirs(server_directory, exist_ok=True)
    os.makedirs(backup_directory, exist_ok=True)

    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 5, 3, 10, 0, 0)
        expected_filename = "mcbackup_server_2025-05-03-10.tar.gz"
        expected_filepath = os.path.join(backup_directory, expected_filename)
        backup_path = get_backup_path(server_directory, backup_directory)
        assert backup_path == expected_filepath


def test_get_backup_path_returns_none_if_file_exists(tmp_path):
    """
    Tests that get_backup_path returns None if a backup file with the
    generated name already exists.
    """
    server_directory = str(tmp_path / "server")
    backup_directory = str(tmp_path / "backup")
    os.makedirs(server_directory, exist_ok=True)
    os.makedirs(backup_directory, exist_ok=True)

    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 5, 3, 10, 0, 0)
        backup_filename = "mcbackup_server_2025-05-03-10.tar.gz"
        existing_filepath = os.path.join(backup_directory, backup_filename)
        with open(existing_filepath, "w") as f:
            f.write("This is an existing backup file.")

        backup_path = get_backup_path(server_directory, backup_directory)
        assert backup_path is None


def test_get_backup_path_returns_filepath_if_file_does_not_exist(tmp_path):
    """
    Tests that get_backup_path returns the backup filepath if a file with
    the generated name does not exist.
    """
    server_directory = str(tmp_path / "server")
    backup_directory = str(tmp_path / "backup")
    os.makedirs(server_directory, exist_ok=True)
    os.makedirs(backup_directory, exist_ok=True)

    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 5, 3, 10, 0, 0)
        expected_filename = "mcbackup_server_2025-05-03-10.tar.gz"
        expected_filepath = os.path.join(backup_directory, expected_filename)
        backup_path = get_backup_path(server_directory, backup_directory)
        assert backup_path == expected_filepath


def test_load_config_loads_servers_section(tmp_path):
    """
    Tests that load_config successfully loads the 'servers' section
    from a valid configuration file.
    """
    config_data = {
        'servers': {
            'server1': {'download_directory': 'dl1',
                        'server_directory': 'srv1',
                        'backup_directory': 'bak1'},
            'server2': {'download_directory': 'dl2',
                        'server_directory': 'srv2',
                        'backup_directory': 'bak2'},
        }
    }
    config_file = tmp_path / CONFIG_FILE
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    servers_config = load_config(str(config_file))
    assert servers_config == config_data['servers']


def test_load_config_returns_empty_dict_if_no_servers_section(tmp_path):
    """
    Tests that load_config returns an empty dictionary if the
    'servers' section is missing from the config file.
    """
    config_data = {'other_section': {'key': 'value'}}
    config_file = tmp_path / CONFIG_FILE
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    servers_config = load_config(str(config_file))
    assert servers_config == {}


def test_load_config_raises_confignotfounderror_if_file_missing(tmp_path,
                                                                capsys):
    """
    Tests that load_config raises ConfigNotFoundError if the specified
    configuration file does not exist.
    """
    missing_config_file = tmp_path / CONFIG_FILE
    example_config_file = tmp_path / EXAMPLE_CONFIG_FILE
    with open(example_config_file, 'w') as f:
        f.write("example config content")

    with pytest.raises(ConfigNotFoundError) as excinfo:
        load_config(str(missing_config_file))
    assert f"Error: Configuration file '{missing_config_file}' not found." in str(
        excinfo.value)

    captured = capsys.readouterr()
    assert f"An example configuration file '{EXAMPLE_CONFIG_FILE}' exists.\n" in captured.out
    assert f"You can copy or rename it to '{CONFIG_FILE}' and modify it with your settings.\n" in captured.out


def test_load_config_raises_confignotfounderror_if_file_missing_no_example(capsys):
    """
    Tests that load_config raises ConfigNotFoundError and does not print
    example info when both config and example files are mocked as missing.
    """
    with patch('os.path.exists') as mock_exists:
        def fake_exists(path):
            return path != CONFIG_FILE and path != EXAMPLE_CONFIG_FILE

        mock_exists.side_effect = fake_exists

        with pytest.raises(ConfigNotFoundError) as excinfo:
            load_config(CONFIG_FILE)
        assert f"Error: Configuration file '{CONFIG_FILE}' not found." in str(
            excinfo.value)

        captured = capsys.readouterr()
        assert "" == captured.out


def test_load_config_raises_configparseerror_if_yaml_error(tmp_path):
    """
    Tests that load_config raises ConfigParseError if there is an
    error parsing the YAML file.
    """
    invalid_yaml_content = "invalid: yaml: content"
    config_file = tmp_path / CONFIG_FILE
    with open(config_file, 'w') as f:
        f.write(invalid_yaml_content)

    with pytest.raises(ConfigParseError) as excinfo:
        load_config(str(config_file))
    assert f"Error parsing '{config_file}': " in str(excinfo.value)
    assert "error" in str(excinfo.value).lower()


def test_perform_backup_if_needed_no_new_files():
    """
    Tests that perform_backup_if_needed does nothing if no new files were downloaded.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup'}
    with patch('main.get_backup_path') as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, None, None, None)
        mock_get_backup_path.assert_not_called()
        mock_backup_files.assert_not_called()

def test_perform_backup_if_needed_new_paper_file_backup_created():
    """
    Tests that perform_backup_if_needed calls backup_files if a new paper file was downloaded
    and get_backup_path returns a filepath.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup', 'screen_name': 'mc', 'backup_exclude': ['.log']}
    mock_backup_path = '/backup/mcbackup_server_2023-10-27-10.tar.gz'
    with patch('main.get_backup_path', return_value=mock_backup_path) as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, 'paper-1.20.jar', None, None)
        mock_get_backup_path.assert_called_once_with('/server', '/backup')
        mock_backup_files.assert_called_once_with('/server', '/backup', 'mc', ['.log'])

def test_perform_backup_if_needed_new_geyser_file_backup_created():
    """
    Tests that perform_backup_if_needed calls backup_files if a new geyser file was downloaded
    and get_backup_path returns a filepath.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup'}
    mock_backup_path = '/backup/mcbackup_server_2023-10-27-10.tar.gz'
    with patch('main.get_backup_path', return_value=mock_backup_path) as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, None, 'Geyser-2.2.0.jar', None)
        mock_get_backup_path.assert_called_once_with('/server', '/backup')
        mock_backup_files.assert_called_once_with('/server', '/backup', 'minecraft', [])

def test_perform_backup_if_needed_new_floodgate_file_backup_created():
    """
    Tests that perform_backup_if_needed calls backup_files if a new floodgate file was downloaded
    and get_backup_path returns a filepath.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup'}
    mock_backup_path = '/backup/mcbackup_server_2023-10-27-10.tar.gz'
    with patch('main.get_backup_path', return_value=mock_backup_path) as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, None, None, 'Floodgate-latest.jar')
        mock_get_backup_path.assert_called_once_with('/server', '/backup')
        mock_backup_files.assert_called_once_with('/server', '/backup', 'minecraft', [])

def test_perform_backup_if_needed_new_files_backup_created():
    """
    Tests that perform_backup_if_needed calls backup_files if multiple new files were downloaded
    and get_backup_path returns a filepath.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup'}
    mock_backup_path = '/backup/mcbackup_server_2023-10-27-10.tar.gz'
    with patch('main.get_backup_path', return_value=mock_backup_path) as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, 'paper-1.20.jar', 'Geyser-2.2.0.jar', None)
        mock_get_backup_path.assert_called_once_with('/server', '/backup')
        mock_backup_files.assert_called_once_with('/server', '/backup', 'minecraft', [])

def test_perform_backup_if_needed_get_backup_path_returns_none():
    """
    Tests that perform_backup_if_needed does not call backup_files if get_backup_path returns None.
    """
    server_settings = {'server_directory': '/server', 'backup_directory': '/backup'}
    with patch('main.get_backup_path', return_value=None) as mock_get_backup_path, \
            patch('main.backup_files') as mock_backup_files:
        perform_backup_if_needed(server_settings, 'paper-1.20.jar', None, None)
        mock_get_backup_path.assert_called_once_with('/server', '/backup')
        mock_backup_files.assert_not_called()


def test_main_no_server_arg():
    """
    Tests that main calls download_server_files with the default directory
    when no --server argument is provided.
    """
    mock_load_config = MagicMock(return_value={})
    mock_download_server_files = MagicMock()
    mock_download_and_backup = MagicMock()

    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(server=None)), \
            patch('main.load_config', mock_load_config), \
            patch('main.download_server_files', mock_download_server_files):
        main()
        mock_load_config.assert_called_once()
        mock_download_server_files.assert_called_once_with(DEFAULT_DOWNLOAD_DIRECTORY)
        mock_download_and_backup.assert_not_called()

def test_main_with_server_arg_valid_config():
    """
    Tests that main calls download_and_backup with the server name and config
    when a valid --server argument is provided.
    """
    server_name = "test_server"
    mock_servers_config = {
        server_name: {"some": "config"},
        "other_server": {"other": "config"},
    }
    mock_load_config = MagicMock(return_value=mock_servers_config)
    mock_download_server_files = MagicMock()
    mock_download_and_backup = MagicMock()

    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(server=server_name)), \
            patch('main.load_config', mock_load_config), \
            patch('main.download_and_backup', mock_download_and_backup), \
            patch('main.download_server_files'):
        main()
        mock_load_config.assert_called_once()
        mock_download_and_backup.assert_called_once_with(server_name, mock_servers_config)
        mock_download_server_files.assert_not_called()

def test_main_with_server_arg_missing_config():
    """
    Tests that main calls load_config but does not call download_and_backup
    if the provided --server name is not found in the config.
    """
    server_name = "non_existent_server"
    mock_servers_config = {
        "test_server": {"some": "config"},
    }
    mock_load_config = MagicMock(return_value=mock_servers_config)
    mock_download_server_files = MagicMock()
    mock_download_and_backup = MagicMock()

    with patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(server=server_name)), \
            patch('main.load_config', mock_load_config), \
            patch('main.download_and_backup', mock_download_and_backup), \
            patch('main.download_server_files'):
        main()
        mock_load_config.assert_called_once()
        mock_download_and_backup.assert_not_called()
        mock_download_server_files.assert_not_called()
