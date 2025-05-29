import fnmatch
import glob
import os
import tarfile
from datetime import datetime, timedelta
from typing import List, Optional

from src.manager.server_manager import MinecraftServerManager


class MinecraftBackupManager:
    def __init__(self, server_manager: MinecraftServerManager,
                 server_directory: str, backup_directory: str):
        self.server_manager = server_manager
        self.server_directory = server_directory
        self.server_directory_base = os.path.basename(self.server_directory)
        self.backup_directory = backup_directory

    def backup_files(self,
                     exclude_patterns: Optional[List[str]] = None,
                     days_to_keep: int = 30) -> None:
        """Executes a backup of the Minecraft server files using tarfile."""
        #  TODO: modify server_manager to know if screen is actually running
        #  TODO:   prior to sending the screen command (or send the screen
        #  TODO:   command without caring about whether it worked or not)
        os.makedirs(self.backup_directory, exist_ok=True)

        screen_running: bool = False
        try:
            self._notify_backup_begin()
            screen_running = True

            self._create_backup_archive(exclude_patterns)

            self._remove_old_backups(days_to_keep)
        except Exception as e:
            print(
                "Warning: Could not interact with screen for save management: "
                f"{e}")
        finally:
            if screen_running:
                self._notify_backup_complete()

    def _create_backup_archive(self,
                               exclude_patterns: Optional[List[str]] = None) \
            -> None:
        original_cwd = os.getcwd()

        try:
            backup_path = self._get_backup_path()

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
        except Exception as e:
            print(f"Error creating backup using tarfile: {e}")
        finally:
            os.chdir(original_cwd)

    def _get_backup_path(self) -> str:
        """Constructs the backup filepath and checks for existing backups."""
        backup_filename: str = (f"mcbackup_{self.server_directory_base}_"
                                f"{self._get_now('%Y-%m-%d-%H')}.tar.gz")
        backup_filepath: str = os.path.join(self.backup_directory,
                                            backup_filename)

        if not os.path.exists(backup_filepath):
            raise FileNotFoundError(f"Backup file {backup_filepath} not found")

        return backup_filepath

    #  TODO: move this to its own home as a utility
    @staticmethod
    def _get_now(timestamp_format: str = "%Y-%m-%d %H:%M:%S") -> str:
        return datetime.now().strftime(timestamp_format)

    def _notify_backup_begin(self) -> None:
        self.server_manager.send_screen_command(
            f"say Backup starting at {self._get_now()}. "
            "World no longer saving!...")
        self.server_manager.send_screen_command("save-off")
        self.server_manager.send_screen_command("save-all")

    def _notify_backup_complete(self) -> None:
        self.server_manager.send_screen_command("save-on")
        self.server_manager.send_screen_command(
            f"say Backup complete at {self._get_now()}! World now saving.")

    def _remove_old_backups(self, days: int) -> None:
        """Removes backup files older than the specified number of days."""
        backup_directory = self.backup_directory
        cutoff: datetime = datetime.now() - timedelta(days=days)

        for filename in os.listdir(backup_directory):
            filepath: str = os.path.join(backup_directory, filename)

            if not os.path.isfile(filepath):
                continue

            if not filename.startswith("mcbackup_") or not filename.endswith(
                    ".tar.gz"):
                continue

            try:
                modified_time: datetime = datetime.fromtimestamp(
                    os.path.getmtime(filepath))
                if modified_time >= cutoff:
                    continue

                if self.server_directory_base:
                    if (f"mcbackup_{self.server_directory_base}_"
                            not in filename):
                        continue

                os.remove(filepath)
            except Exception as e:
                print(f"Error checking or deleting {filepath}: {e}")
