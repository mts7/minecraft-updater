import fnmatch
import glob
import os
import tarfile
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.manager.server_manager import MinecraftServerManager


class MinecraftBackupManager:
    def __init__(self, server_manager: MinecraftServerManager):
        self.server_manager = server_manager
        self.server_directory = server_manager.server_directory
        self.backup_directory = server_manager.backup_directory
        os.makedirs(self.backup_directory, exist_ok=True)
        self.original_cwd = ""

    def backup_files(
            self,
            exclude: Optional[List[str]]
    ) -> None:
        backup_filepath = self.get_backup_path()
        if not backup_filepath:
            return

        self.create_server_backup(exclude)

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
        try:
            self.server_manager.send_screen_command(
                f"say Backup starting at {start_time}. "
                "World no longer saving!...")
            self.server_manager.send_screen_command("save-off")
            self.server_manager.send_screen_command("save-all")
            screen_running = True
        except Exception as e:
            print(
                "Warning: Could not interact with screen for save management: "
                f"{e}")

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
                self.server_manager.send_screen_command("save-on")
                end_time: str = datetime.now().strftime(timestamp_format)
                self.server_manager.send_screen_command(
                    f"say Backup complete at {end_time}! World now saving.")

            self._remove_old_backups(
                days_to_keep,
                server_dirname=server_dirname)
        except Exception as e:
            print(f"Error creating backup using tarfile: {e}")
        finally:
            os.chdir(self.original_cwd)

    def get_backup_path(self) \
            -> Optional[str]:
        """Constructs the backup filepath and checks for existing backups."""
        server_dirname: str = os.path.basename(
            self.server_directory.rstrip('/'))
        backup_filename: str = (f"mcbackup_{server_dirname}_"
                                f"{datetime.now().strftime('%Y-%m-%d-%H')}.tar.gz")
        backup_filepath: str = os.path.join(self.backup_directory,
                                            backup_filename)

        if os.path.exists(backup_filepath):
            return None

        return backup_filepath

    def _remove_old_backups(self, days: int,
                            server_dirname: Optional[str] = None) -> None:
        """
        Removes backup files older than the specified number of days,
        optionally filtering by server directory name.
        """
        backup_directory = self.backup_directory
        cutoff: datetime = datetime.now() - timedelta(days=days)
        for filename in os.listdir(backup_directory):
            filepath: str = os.path.join(backup_directory, filename)
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
