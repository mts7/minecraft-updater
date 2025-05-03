import fnmatch
import glob
import shutil
import subprocess  # nosec B404
import os
import tarfile
from datetime import datetime, timedelta
from typing import List, Optional

from src.exceptions import ScreenNotInstalled


class FileManager:
    def __init__(self, server_directory: str, backup_directory: str,
                 screen_name: str = "minecraft") -> None:
        """
        Initializes the FileManager with server and backup directories.

        Args:
            server_directory:
                The absolute path to the Minecraft server directory.
            backup_directory:
                The absolute path to the directory where backups will be
                stored.
            screen_name:
                The name of the screen session running the Minecraft server.
        """
        self.server_directory: str = server_directory
        self.backup_directory: str = backup_directory
        self.screen_name: str = screen_name
        os.makedirs(self.backup_directory, exist_ok=True)
        self.original_cwd = ""

    def create_server_backup(self,
                             exclude_patterns: Optional[
                                 List[str]] = None,
                             days_to_keep: int = 30) -> None:
        """Executes a backup of the Minecraft server files using tarfile."""
        self.original_cwd = os.getcwd()
        timestamp_format: str = "%Y-%m-%d %H:%M:%S"
        start_time: str = datetime.now().strftime(timestamp_format)
        server_dirname: str = os.path.basename(self.server_directory)
        backup_filename: str = (f"mcbackup_{server_dirname}_"
                                f"{datetime.now().strftime('%Y-%m-%d-%H')}"
                                ".tar.gz")
        backup_path: str = os.path.join(self.backup_directory, backup_filename)

        screen_running: bool = False
        screen_path = shutil.which('screen')
        if screen_path is None:
            raise ScreenNotInstalled

        try:
            subprocess.run([screen_path, '-list'], check=True,
                           capture_output=True, text=True,
                           shell=False)  # nosec B603
            self._send_screen_command(self.screen_name,
                                      "say Backup starting at "
                                      f"{start_time}. "
                                      "World no longer saving!...")
            self._send_screen_command(self.screen_name, "save-off")
            self._send_screen_command(self.screen_name, "save-all")
            screen_running = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(
                "Warning: 'screen' is not running or not found. "
                "Skipping server save management.")

        try:
            os.chdir(self.server_directory)
            with tarfile.open(backup_path, "w:gz") as tar:
                for item in glob.glob('*'):
                    exclude = False
                    if exclude_patterns:
                        for pattern in exclude_patterns:
                            if fnmatch.fnmatch(item, pattern):
                                exclude = True
                                break
                    if not exclude:
                        tar.add(item, arcname=item)

            if screen_running:
                self._send_screen_command(self.screen_name, "save-on")
                end_time: str = datetime.now().strftime(timestamp_format)
                self._send_screen_command(
                    self.screen_name,
                    (f"say Backup complete at {end_time}! "
                     "World now saving."))

            self._remove_old_backups(days_to_keep,
                                     server_dirname=server_dirname)
        except Exception as e:
            print(f"Error creating backup using tarfile: {e}")
            # Optionally, you might want to re-raise the exception
            # raise
        finally:
            # It's good practice to change back to the original directory
            os.chdir(self.original_cwd)

    def _send_screen_command(self, screen_name: str, command: str) -> None:
        """Sends a command to a running screen session."""
        screen_path = shutil.which('screen')
        if screen_path is None:
            raise ScreenNotInstalled

        try:
            subprocess.run(
                [
                    screen_path,
                    '-r', screen_name, '-X', 'stuff', f"{command}\n"
                ],
                check=True, shell=False)  # nosec B603
        except FileNotFoundError:
            print("Error: 'screen' command not found. Ensure it's installed.")
        except subprocess.CalledProcessError as e:
            print(
                f"Warning: Could not send command to screen '{screen_name}'. "
                f"Is the session running? Error: {e}"
            )

    def _remove_old_backups(self, days: int,
                            server_dirname: Optional[str] = None) -> None:
        """
        Removes backup files older than the specified number of days,
        optionally filtering by server directory name.
        """
        cutoff: datetime = datetime.now() - timedelta(days=days)
        for filename in os.listdir(self.backup_directory):
            filepath: str = os.path.join(self.backup_directory, filename)
            if os.path.isfile(filepath):
                try:
                    modified_time: datetime = datetime.fromtimestamp(
                        os.path.getmtime(filepath))
                    if modified_time < cutoff and filename.startswith(
                            "mcbackup_") and filename.endswith(".tar.gz"):
                        if server_dirname:
                            if f"mcbackup_{server_dirname}_" in filename:
                                os.remove(filepath)
                        else:
                            os.remove(filepath)
                except Exception as e:
                    print(f"Error checking or deleting {filepath}: {e}")
